from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from reportlab.platypus import PageBreak

from ..runtime.ctx import PdfCtx
from .images import fig_pdf_page
from .txtfmt_inline import inline_rl as _inline_rl
from .txtfmt_inline import normalize_unicode as _normalize_unicode
from .txtfmt_inline import sanitize_code_line, sanitize_para, sanitize_plain
from .txtfmt_structure import (
    consume_procedural_steps,
    condbreak,
    is_dash_rule,
    is_eq_rule,
    is_procedural_step_start,
    mk_heading,
    parse_pipe_table,
    unique_key,
)
from .txtfmt_syntax import (
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
    parse_fig_marker,
    parse_img_marker,
)

Flowable = Any

# ------------------------------
# UX policy (paginado)
# ------------------------------
_TOP_LEVEL_STARTS_NEW_PAGE = True
_EXERCISE_STARTS_NEW_PAGE = True

_MIN_SPACE_BEFORE_CALLOUT = 180
_MIN_SPACE_BEFORE_FIG = 260
_MIN_SPACE_BEFORE_CODE = 140


# ------------------------------
# Controller helpers
# ------------------------------

def _last_is_pagebreak(story: List[Flowable]) -> bool:
    return bool(story) and isinstance(story[-1], PageBreak)



def _maybe_pagebreak(story: List[Flowable]) -> None:
    if story and not _last_is_pagebreak(story):
        story.append(PageBreak())



def _needs_pagebreak_before_heading(level: int, title: str) -> bool:
    t = (title or "").lower()
    if _EXERCISE_STARTS_NEW_PAGE and "ejercicio" in t:
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
    resolve_img: Optional[Callable[[str], Path]] = None,
    cache_dir: Optional[Path],
    default_zoom: float,
) -> bool:
    fig = parse_fig_marker(marker_line)
    if not fig:
        return False

    fn, page, cap, zoom = fig
    pdf_path = resolve_pdf(fn)
    caption = cap or f"Fuente: {fn}, pág. {page}"
    condbreak(story, _MIN_SPACE_BEFORE_FIG)
    story.extend(
        fig_pdf_page(
            ctx,
            pdf_path,
            page,
            caption=sanitize_para(caption),
            cache_dir=cache_dir,
            zoom=zoom or default_zoom,
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
    mb = BLOCK_OPEN_RE.match(line)
    if not mb:
        return None

    kind_raw = (mb.group("kind") or "").lower().strip()
    title = (mb.group("title") or "").strip() or None

    body_lines: List[str] = []
    i = start + 1
    while i < len(lines):
        raw2 = lines[i].rstrip("\n")
        if BLOCK_CLOSE_RE.match(raw2.strip()):
            break
        body_lines.append(raw2)
        i += 1

    if i < len(lines) and BLOCK_CLOSE_RE.match(lines[i].strip()):
        i += 1

    if kind_raw == "table":
        rows, aligns = parse_pipe_table(body_lines)
        story.append(ctx.table(rows, header=True, aligns=aligns))
        story.append(ctx.sp(6))
        return i

    kind_map = {
        "def": ("note", "Definición"),
        "ej": ("info", "Ejemplo"),
        "error": ("danger", "Error típico"),
        "tip": ("note", "Tip"),
        "warn": ("warn", "Atención"),
        "info": ("info", "Info"),
        "check": ("info", "Checklist"),
    }
    call_kind, default_title = kind_map.get(
        kind_raw,
        ("info", kind_raw.upper() if kind_raw else "Info"),
    )
    final_title = title or default_title
    body_flow = parse_block(body_lines, True) if body_lines else [ctx.p("", ctx.base)]

    condbreak(story, _MIN_SPACE_BEFORE_CALLOUT)
    story.append(ctx.callout(call_kind, final_title, body_flow))
    story.append(ctx.sp(10))
    return i



def _append_legacy_callout(
    ctx: PdfCtx,
    story: List[Flowable],
    lines: List[str],
    start: int,
    *,
    parse_block: Callable[[List[str], bool], List[Flowable]],
) -> Optional[int]:
    line = lines[start].strip()
    mco = CALLOUT_OPEN_RE.match(line)
    if not mco:
        return None

    kind = mco.group("kind").lower()
    title = mco.group("title") or None

    body_lines: List[str] = []
    i = start + 1
    while i < len(lines):
        raw2 = lines[i].rstrip("\n")
        line2 = raw2.strip()
        mclose = CALLOUT_CLOSE_RE.match(line2)
        if mclose and mclose.group("kind").lower() == kind:
            break
        body_lines.append(raw2)
        i += 1

    if i < len(lines) and CALLOUT_CLOSE_RE.match(lines[i].strip()):
        i += 1

    body_flow = parse_block(body_lines, True) if body_lines else [ctx.p("", ctx.base)]
    kmap = {
        "note": "note",
        "tip": "note",
        "warn": "warn",
        "danger": "danger",
        "info": "info",
        "check": "info",
    }
    condbreak(story, _MIN_SPACE_BEFORE_CALLOUT)
    story.append(ctx.callout(kmap.get(kind, "info"), title, body_flow))
    story.append(ctx.sp(10))
    return i



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
        mblk = HEADING_BLOCK_RE.match(title_line)
        if mblk:
            num = mblk.group("num")
            delim = mblk.group("delim")
            full = f"{num}{delim} {mblk.group('title')}"
            lvl = 1 + num.count(".")
            key = unique_key(f"{num}-{mblk.group('title')}", used_keys)
        else:
            full = title_line
            lvl = 1
            key = unique_key(title_line, used_keys)

        if (not in_callout) and _needs_pagebreak_before_heading(lvl, full):
            _maybe_pagebreak(story)
        story.append(mk_heading(ctx, full, lvl, key, in_callout=in_callout))
        return start + 3

    story.append(ctx.hr(space_before=6, space_after=8))
    return start + 1



def _append_dot_heading(
    ctx: PdfCtx,
    story: List[Flowable],
    line: str,
    *,
    used_keys: Dict[str, int],
    in_callout: bool,
) -> bool:
    mh = HEADING_DOT_RE.match(line)
    if not mh:
        return False

    num = mh.group("num")
    full = f"{num}. {mh.group('title')}"
    lvl = 1 + num.count(".")
    key = unique_key(f"{num}-{mh.group('title')}", used_keys)
    if (not in_callout) and _needs_pagebreak_before_heading(lvl, full):
        _maybe_pagebreak(story)
    story.append(mk_heading(ctx, full, lvl, key, in_callout=in_callout))
    return True



def _append_code_fence(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> Optional[int]:
    raw = lines[start].rstrip("\n")
    mf = FENCE_OPEN_RE.match(raw)
    if not mf:
        return None

    lang = (mf.group("lang") or "").strip()
    block: List[str] = []
    i = start + 1
    while i < len(lines) and not FENCE_CLOSE_RE.match(lines[i]):
        block.append(sanitize_code_line(lines[i]))
        i += 1
    if i < len(lines) and FENCE_CLOSE_RE.match(lines[i]):
        i += 1

    title = f"Código{f' ({lang})' if lang else ''}"
    condbreak(story, _MIN_SPACE_BEFORE_CODE)
    story.append(ctx.codeblock(block, title=title))
    return i



def _append_unordered_list(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> Optional[int]:
    raw = lines[start].rstrip("\n")
    if not raw.lstrip().startswith(("- ", "* ", "• ")):
        return None

    items: List[str] = []
    i = start
    while i < len(lines):
        r2 = lines[i].rstrip("\n")
        s2 = r2.lstrip()
        if not s2.startswith(("- ", "* ", "• ")):
            break
        items.append(sanitize_para(s2[2:]))
        i += 1
    story.append(ctx.ul(items))
    return i



def _append_ordered_list(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> Optional[int]:
    line = lines[start].strip()
    if not ORDERED_LIST_RE.match(line):
        return None

    items: List[str] = []
    i = start
    while i < len(lines):
        mm = ORDERED_LIST_RE.match(lines[i].strip())
        if not mm:
            break
        item_text = lines[i].strip()[mm.end():]
        items.append(sanitize_para(item_text))
        i += 1
    story.append(ctx.ol(items))
    return i



def _append_indented_code(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> Optional[int]:
    raw = lines[start].rstrip("\n")
    if not (raw.startswith("    ") or raw.startswith("\t")):
        return None

    block: List[str] = []
    i = start
    while i < len(lines):
        r2 = lines[i].rstrip("\n")
        if not (r2.startswith("    ") or r2.startswith("\t")):
            break
        block.append(sanitize_code_line(r2[4:] if r2.startswith("    ") else r2[1:]))
        i += 1

    condbreak(story, _MIN_SPACE_BEFORE_CODE)
    story.append(ctx.codeblock(block, title="Procedimiento"))
    return i



def _paragraph_should_stop(peek_raw: str) -> bool:
    peek = peek_raw.strip()
    if not peek:
        return True
    if PB_RE.match(peek):
        return True
    if parse_fig_marker(peek) or parse_img_marker(peek):
        return True
    if BLOCK_OPEN_RE.match(peek) or CALLOUT_OPEN_RE.match(peek):
        return True
    if is_eq_rule(peek) or is_dash_rule(peek):
        return True
    if HEADING_DOT_RE.match(peek):
        return True
    if FENCE_OPEN_RE.match(peek_raw):
        return True
    if peek_raw.lstrip().startswith(("- ", "* ", "• ")):
        return True
    if ORDERED_LIST_RE.match(peek):
        return True
    if peek_raw.startswith("    ") or peek_raw.startswith("\t"):
        return True
    return False



def _append_paragraph(ctx: PdfCtx, story: List[Flowable], lines: List[str], start: int) -> int:
    first = lines[start].rstrip("\n").strip()
    parts: List[str] = [sanitize_para(first)]
    i = start + 1
    while i < len(lines):
        peek_raw = lines[i].rstrip("\n")
        if _paragraph_should_stop(peek_raw):
            break
        parts.append(sanitize_para(peek_raw.strip()))
        i += 1
    story.append(ctx.p(" ".join(parts)))
    return i


# ------------------------------
# Public API / controller
# ------------------------------

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

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n")
        line = raw.strip()

        if not line:
            i += 1
            continue

        if PB_RE.match(line):
            _append_explicit_pagebreak(story)
            i += 1
            continue

        if _append_figure(
            ctx,
            story,
            line,
            resolve_pdf=resolve_pdf,
            resolve_img=resolve_img,
            cache_dir=cache_dir,
            default_zoom=default_zoom,
        ):
            i += 1
            continue

        next_i = _append_block_construct(ctx, story, lines, i, parse_block=parse_block)
        if next_i is not None:
            i = next_i
            continue

        next_i = _append_legacy_callout(ctx, story, lines, i, parse_block=parse_block)
        if next_i is not None:
            i = next_i
            continue

        next_i = _append_eq_block_heading(
            ctx,
            story,
            lines,
            i,
            used_keys=used_keys,
            in_callout=_in_callout,
        )
        if next_i is not None:
            i = next_i
            continue

        if is_dash_rule(line):
            story.append(ctx.hr(space_before=6, space_after=8))
            i += 1
            continue

        if is_procedural_step_start(lines, i):
            flows, i = consume_procedural_steps(ctx, lines, i)
            story.extend(flows)
            continue

        if _append_dot_heading(ctx, story, line, used_keys=used_keys, in_callout=_in_callout):
            i += 1
            continue

        next_i = _append_code_fence(ctx, story, lines, i)
        if next_i is not None:
            i = next_i
            continue

        next_i = _append_unordered_list(ctx, story, lines, i)
        if next_i is not None:
            i = next_i
            continue

        next_i = _append_ordered_list(ctx, story, lines, i)
        if next_i is not None:
            i = next_i
            continue

        next_i = _append_indented_code(ctx, story, lines, i)
        if next_i is not None:
            i = next_i
            continue

        i = _append_paragraph(ctx, story, lines, i)

    return story


__all__ = [
    "sanitize_para",
    "sanitize_plain",
    "sanitize_code_line",
    "txt_to_flowables",
]
