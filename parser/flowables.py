from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from reportlab.platypus import PageBreak

from ..render.images import fig, fig_pdf_page
from ..runtime.ctx import PdfCtx
from .inline import sanitize_code_line, sanitize_para, sanitize_plain
from .structure import (
    condbreak,
    consume_procedural_steps,
    is_dash_rule,
    is_eq_rule,
    is_procedural_step_start,
    looks_like_simple_dot_heading,
    mk_heading,
    parse_pipe_table,
    unique_key,
)
from .syntax import (
    BLOCK_CLOSE_RE,
    BLOCK_OPEN_RE,
    CALLOUT_CLOSE_RE,
    CALLOUT_OPEN_RE,
    FENCE_CLOSE_RE,
    FENCE_OPEN_RE,
    HEADING_BLOCK_RE,
    HEADING_DOT_RE,
    ORDERED_LIST_RE,
    PB_RE,
    SIMPLE_HEADING_RE,
    parse_fig_marker,
    parse_img_marker,
)

Flowable = Any

_TOP_LEVEL_STARTS_NEW_PAGE = True
_EXERCISE_STARTS_NEW_PAGE = True

_MIN_SPACE_BEFORE_CALLOUT = 180
_MIN_SPACE_BEFORE_FIG = 260
_MIN_SPACE_BEFORE_CODE = 140


def _last_is_pagebreak(story: List[Flowable]) -> bool:
    return bool(story) and isinstance(story[-1], PageBreak)


def _maybe_pagebreak(story: List[Flowable]) -> None:
    if story and not _last_is_pagebreak(story):
        story.append(PageBreak())


def _needs_pagebreak_before_heading(level: int, title: str) -> bool:
    lowered = (title or "").lower()
    if _EXERCISE_STARTS_NEW_PAGE and "ejercicio" in lowered:
        return True
    if _TOP_LEVEL_STARTS_NEW_PAGE and level == 1:
        return True
    return False


def _append_explicit_pagebreak(story: List[Flowable]) -> None:
    story.append(PageBreak())


def _append_figure(
    ctx: PdfCtx,
    story: List[Flowable],
    marker_line: str,
    *,
    resolve_pdf: Callable[[str], Path],
    cache_dir: Optional[Path],
    default_zoom: float,
) -> bool:
    parsed = parse_fig_marker(marker_line)
    if not parsed:
        return False

    filename, page, caption, zoom = parsed
    condbreak(story, _MIN_SPACE_BEFORE_FIG)
    story.extend(
        fig_pdf_page(
            ctx,
            resolve_pdf(filename),
            page,
            caption=sanitize_para(caption or f"Fuente: {filename}, pág. {page}"),
            cache_dir=cache_dir,
            zoom=zoom or default_zoom,
        )
    )
    return True


def _append_image(
    ctx: PdfCtx,
    story: List[Flowable],
    marker_line: str,
    *,
    resolve_img: Optional[Callable[[str], Path]],
) -> bool:
    parsed = parse_img_marker(marker_line)
    if not parsed or resolve_img is None:
        return False

    filename, caption, width = parsed
    condbreak(story, _MIN_SPACE_BEFORE_FIG)
    story.extend(
        fig(
            ctx,
            resolve_img(filename),
            sanitize_para(caption) if caption else None,
            max_w=width,
        )
    )
    return True


def _append_block_construct(
    ctx: PdfCtx,
    story: List[Flowable],
    lines: List[str],
    start: int,
    *,
    parse_block: Callable[[List[str], bool], List[Flowable]],
) -> Optional[int]:
    line = lines[start].strip()
    match = BLOCK_OPEN_RE.match(line)
    if not match:
        return None

    kind_raw = (match.group("kind") or "").lower().strip()
    title = (match.group("title") or "").strip() or None

    body_lines: List[str] = []
    idx = start + 1
    while idx < len(lines):
        raw = lines[idx].rstrip("\n")
        if BLOCK_CLOSE_RE.match(raw.strip()):
            break
        body_lines.append(raw)
        idx += 1

    if idx < len(lines) and BLOCK_CLOSE_RE.match(lines[idx].strip()):
        idx += 1

    if kind_raw == "table":
        rows, aligns = parse_pipe_table(body_lines)
        story.append(ctx.table(rows, header=True, aligns=aligns))
        story.append(ctx.sp(6))
        return idx

    kind_map = {
        "def": ("note", "Definición"),
        "ej": ("info", "Ejemplo"),
        "error": ("danger", "Error típico"),
        "tip": ("note", "Tip"),
        "warn": ("warn", "Atención"),
        "info": ("info", "Info"),
        "check": ("info", "Checklist"),
    }
    call_kind, default_title = kind_map.get(kind_raw, ("info", kind_raw.upper() if kind_raw else "Info"))
    body_flow = parse_block(body_lines, True) if body_lines else [ctx.p("", ctx.base)]

    condbreak(story, _MIN_SPACE_BEFORE_CALLOUT)
    story.append(ctx.callout(call_kind, title or default_title, body_flow))
    story.append(ctx.sp(10))
    return idx


def _append_legacy_callout(
    ctx: PdfCtx,
    story: List[Flowable],
    lines: List[str],
    start: int,
    *,
    parse_block: Callable[[List[str], bool], List[Flowable]],
) -> Optional[int]:
    line = lines[start].strip()
    match = CALLOUT_OPEN_RE.match(line)
    if not match:
        return None

    kind = match.group("kind").lower()
    title = match.group("title") or None
    body_lines: List[str] = []
    idx = start + 1
    while idx < len(lines):
        raw = lines[idx].rstrip("\n")
        stripped = raw.strip()
        close = CALLOUT_CLOSE_RE.match(stripped)
        if close and close.group("kind").lower() == kind:
            break
        body_lines.append(raw)
        idx += 1

    if idx < len(lines) and CALLOUT_CLOSE_RE.match(lines[idx].strip()):
        idx += 1

    body_flow = parse_block(body_lines, True) if body_lines else [ctx.p("", ctx.base)]
    kind_map = {
        "note": "note",
        "tip": "note",
        "warn": "warn",
        "danger": "danger",
        "info": "info",
        "check": "info",
    }
    condbreak(story, _MIN_SPACE_BEFORE_CALLOUT)
    story.append(ctx.callout(kind_map.get(kind, "info"), title, body_flow))
    story.append(ctx.sp(10))
    return idx


def _append_eq_block_heading(
    ctx: PdfCtx,
    story: List[Flowable],
    lines: List[str],
    start: int,
    *,
    used_keys: Dict[str, int],
    in_callout: bool,
) -> Optional[int]:
    line = lines[start].strip()
    if not is_eq_rule(line):
        return None

    if start + 2 < len(lines) and lines[start + 2].strip() and is_eq_rule(lines[start + 2]):
        title_line = lines[start + 1].strip()
        match = HEADING_BLOCK_RE.match(title_line)
        if match:
            num = match.group("num")
            full = f"{num}{match.group('delim')} {match.group('title')}"
            level = 1 + num.count(".")
            key = unique_key(f"{num}-{match.group('title')}", used_keys)
        else:
            full = title_line
            level = 1
            key = unique_key(title_line, used_keys)

        if (not in_callout) and _needs_pagebreak_before_heading(level, full):
            _maybe_pagebreak(story)
        story.append(mk_heading(ctx, full, level, key, in_callout=in_callout))
        return start + 3

    story.append(ctx.hr(space_before=6, space_after=8))
    return start + 1


def _append_dot_heading(
    ctx: PdfCtx,
    story: List[Flowable],
    lines: List[str],
    start: int,
    *,
    used_keys: Dict[str, int],
    in_callout: bool,
) -> bool:
    line = lines[start].strip()
    match = HEADING_DOT_RE.match(line)
    if match:
        num = match.group("num")
        full = f"{num}. {match.group('title')}"
        level = 1 + num.count(".")
        key = unique_key(f"{num}-{match.group('title')}", used_keys)
        if (not in_callout) and _needs_pagebreak_before_heading(level, full):
            _maybe_pagebreak(story)
        story.append(mk_heading(ctx, full, level, key, in_callout=in_callout))
        return True

    simple = SIMPLE_HEADING_RE.match(line)
    if not simple or not looks_like_simple_dot_heading(lines, start):
        return False

    num = simple.group("num")
    full = f"{num}. {simple.group('title')}"
    key = unique_key(f"{num}-{simple.group('title')}", used_keys)
    if (not in_callout) and _needs_pagebreak_before_heading(1, full):
        _maybe_pagebreak(story)
    story.append(mk_heading(ctx, full, 1, key, in_callout=in_callout))
    return True


def _append_code_fence(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> Optional[int]:
    match = FENCE_OPEN_RE.match(lines[start].rstrip("\n"))
    if not match:
        return None

    lang = (match.group("lang") or "").strip()
    block: List[str] = []
    idx = start + 1
    while idx < len(lines) and not FENCE_CLOSE_RE.match(lines[idx]):
        block.append(sanitize_code_line(lines[idx]))
        idx += 1
    if idx < len(lines) and FENCE_CLOSE_RE.match(lines[idx]):
        idx += 1

    condbreak(story, _MIN_SPACE_BEFORE_CODE)
    story.append(ctx.codeblock(block, title=f"Código{f' ({lang})' if lang else ''}"))
    return idx


def _append_unordered_list(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> Optional[int]:
    raw = lines[start].rstrip("\n")
    if not raw.lstrip().startswith(("- ", "* ", "â€¢ ")):
        return None

    items: List[str] = []
    idx = start
    while idx < len(lines):
        raw = lines[idx].rstrip("\n")
        stripped = raw.lstrip()
        if not stripped.startswith(("- ", "* ", "â€¢ ")):
            break
        items.append(sanitize_para(stripped[2:]))
        idx += 1
    story.append(ctx.ul(items))
    return idx


def _append_ordered_list(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> Optional[int]:
    line = lines[start].strip()
    if not ORDERED_LIST_RE.match(line):
        return None

    raw_items: List[str] = []
    idx = start
    while idx < len(lines):
        match = ORDERED_LIST_RE.match(lines[idx].strip())
        if not match:
            break
        raw_items.append(lines[idx].strip()[match.end() :])
        idx += 1

    if len(raw_items) == 1 and looks_like_simple_dot_heading(lines, start):
        return None

    story.append(ctx.ol([sanitize_para(item) for item in raw_items]))
    return idx


def _append_indented_code(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> Optional[int]:
    raw = lines[start].rstrip("\n")
    if not (raw.startswith("    ") or raw.startswith("\t")):
        return None

    block: List[str] = []
    idx = start
    while idx < len(lines):
        raw = lines[idx].rstrip("\n")
        if not (raw.startswith("    ") or raw.startswith("\t")):
            break
        block.append(sanitize_code_line(raw[4:] if raw.startswith("    ") else raw[1:]))
        idx += 1

    condbreak(story, _MIN_SPACE_BEFORE_CODE)
    story.append(ctx.codeblock(block, title="Procedimiento"))
    return idx


def _paragraph_should_stop(peek_raw: str) -> bool:
    peek = peek_raw.strip()
    if not peek or PB_RE.match(peek):
        return True
    if parse_fig_marker(peek) or parse_img_marker(peek):
        return True
    if BLOCK_OPEN_RE.match(peek) or CALLOUT_OPEN_RE.match(peek):
        return True
    if is_eq_rule(peek) or is_dash_rule(peek):
        return True
    if HEADING_DOT_RE.match(peek) or FENCE_OPEN_RE.match(peek_raw):
        return True
    if peek_raw.lstrip().startswith(("- ", "* ", "â€¢ ")):
        return True
    if ORDERED_LIST_RE.match(peek):
        return True
    if peek_raw.startswith("    ") or peek_raw.startswith("\t"):
        return True
    return False


def _append_paragraph(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> int:
    parts: List[str] = [sanitize_para(lines[start].rstrip("\n").strip())]
    idx = start + 1
    while idx < len(lines):
        peek_raw = lines[idx].rstrip("\n")
        if _paragraph_should_stop(peek_raw):
            break
        parts.append(sanitize_para(peek_raw.strip()))
        idx += 1
    story.append(ctx.p(" ".join(parts)))
    return idx


def txt_to_flowables(
    ctx: PdfCtx,
    text: str,
    *,
    resolve_pdf: Callable[[str], Path],
    resolve_img: Optional[Callable[[str], Path]] = None,
    cache_dir: Optional[Path] = None,
    default_zoom: float = 2.0,
    _used_keys: Optional[Dict[str, int]] = None,
    _in_callout: bool = False,
) -> List[Flowable]:
    lines = text.splitlines()
    story: List[Flowable] = []
    used_keys: Dict[str, int] = _used_keys if _used_keys is not None else {}

    def parse_block(block_lines: List[str], in_callout: bool = False) -> List[Flowable]:
        return txt_to_flowables(
            ctx,
            "\n".join(block_lines),
            resolve_pdf=resolve_pdf,
            resolve_img=resolve_img,
            cache_dir=cache_dir,
            default_zoom=default_zoom,
            _used_keys=used_keys,
            _in_callout=in_callout,
        )

    idx = 0
    while idx < len(lines):
        raw = lines[idx].rstrip("\n")
        line = raw.strip()

        if not line:
            idx += 1
            continue
        if PB_RE.match(line):
            _append_explicit_pagebreak(story)
            idx += 1
            continue
        if _append_figure(ctx, story, line, resolve_pdf=resolve_pdf, cache_dir=cache_dir, default_zoom=default_zoom):
            idx += 1
            continue
        if _append_image(ctx, story, line, resolve_img=resolve_img):
            idx += 1
            continue

        next_idx = _append_block_construct(ctx, story, lines, idx, parse_block=parse_block)
        if next_idx is not None:
            idx = next_idx
            continue

        next_idx = _append_legacy_callout(ctx, story, lines, idx, parse_block=parse_block)
        if next_idx is not None:
            idx = next_idx
            continue

        next_idx = _append_eq_block_heading(ctx, story, lines, idx, used_keys=used_keys, in_callout=_in_callout)
        if next_idx is not None:
            idx = next_idx
            continue

        if is_dash_rule(line):
            story.append(ctx.hr(space_before=6, space_after=8))
            idx += 1
            continue

        if is_procedural_step_start(lines, idx):
            flows, idx = consume_procedural_steps(ctx, lines, idx)
            story.extend(flows)
            continue

        next_idx = _append_code_fence(ctx, story, lines, idx)
        if next_idx is not None:
            idx = next_idx
            continue

        next_idx = _append_unordered_list(ctx, story, lines, idx)
        if next_idx is not None:
            idx = next_idx
            continue

        next_idx = _append_ordered_list(ctx, story, lines, idx)
        if next_idx is not None:
            idx = next_idx
            continue

        if _append_dot_heading(ctx, story, lines, idx, used_keys=used_keys, in_callout=_in_callout):
            idx += 1
            continue

        next_idx = _append_indented_code(ctx, story, lines, idx)
        if next_idx is not None:
            idx = next_idx
            continue

        idx = _append_paragraph(ctx, story, lines, idx)

    return story


__all__ = [
    "sanitize_para",
    "sanitize_plain",
    "sanitize_code_line",
    "txt_to_flowables",
]
