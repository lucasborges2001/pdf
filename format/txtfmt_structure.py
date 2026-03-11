from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from reportlab.platypus import CondPageBreak
from reportlab.platypus.paragraph import Paragraph

from ..runtime.ctx import PdfCtx
from .txtfmt_inline import _inline_rl, _normalize_unicode, sanitize_para
from .txtfmt_syntax import (
    BLOCK_OPEN_RE,
    CALLOUT_OPEN_RE,
    FENCE_OPEN_RE,
    HEADING_DOT_RE,
    ORDERED_LIST_RE,
    PB_RE,
    PIPE_SEP_CELL_RE,
    STEP_ITEM_RE,
    parse_fig_marker,
    parse_img_marker,
)

Flowable = Any


def is_rule(line: str, ch: str, min_len: int) -> bool:
    s = line.strip()
    return len(s) >= min_len and set(s) == {ch}


def is_eq_rule(line: str) -> bool:
    return is_rule(line, "=", 10)


def is_dash_rule(line: str) -> bool:
    return is_rule(line, "-", 5)


def slugify(s: str) -> str:
    s = _normalize_unicode(s).lower().strip()
    s = re.sub(r"[^\w\s.-]", "", s)
    s = re.sub(r"[\s.]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "sec"


def unique_key(base: str, used: Dict[str, int]) -> str:
    k = slugify(base)
    n = used.get(k, 0)
    used[k] = n + 1
    return k if n == 0 else f"{k}-{n+1}"


def mk_heading(ctx: PdfCtx, text: str, level: int, key: str, *, in_callout: bool) -> Flowable:
    style = ctx.h2 if level <= 1 else ctx.h3
    html = f'<a name="{key}"/>{_inline_rl(text)}'
    p = ctx.p(html, style)
    setattr(p, "_fbd_key", key)
    setattr(p, "_fbd_level", max(0, int(level) - 1))
    setattr(p, "_fbd_is_heading", True)
    if in_callout:
        setattr(p, "_fbd_skip_toc", True)
        setattr(p, "_fbd_skip_outline", True)
    return p


def peek_next_nonempty(lines: List[str], start: int) -> Optional[str]:
    j = start
    while j < len(lines):
        s = lines[j].strip()
        if s:
            return s
        j += 1
    return None


def is_procedural_step_start(lines: List[str], idx: int) -> bool:
    line = lines[idx].strip()
    if not STEP_ITEM_RE.match(line):
        return False
    nxt = peek_next_nonempty(lines, idx + 1)
    if not nxt:
        return False
    if STEP_ITEM_RE.match(nxt):
        return False
    if HEADING_DOT_RE.match(nxt) or ORDERED_LIST_RE.match(nxt):
        return False
    if PB_RE.match(nxt) or parse_fig_marker(nxt) or parse_img_marker(nxt):
        return False
    if BLOCK_OPEN_RE.match(nxt) or CALLOUT_OPEN_RE.match(nxt):
        return False
    if is_eq_rule(nxt) or is_dash_rule(nxt):
        return False
    if FENCE_OPEN_RE.match(nxt):
        return False
    return True


def consume_procedural_steps(ctx: PdfCtx, lines: List[str], start: int) -> Tuple[List[Flowable], int]:
    items: List[Paragraph] = []
    i = start
    while i < len(lines):
        line = lines[i].strip()
        m = STEP_ITEM_RE.match(line)
        if not m:
            break

        num = m.group("num")
        title = sanitize_para(m.group("title"))
        i += 1

        body_parts: List[str] = []
        while i < len(lines):
            peek_raw = lines[i].rstrip("\n")
            peek = peek_raw.strip()
            if not peek:
                break
            if STEP_ITEM_RE.match(peek):
                break
            if PB_RE.match(peek):
                break
            if parse_fig_marker(peek) or parse_img_marker(peek):
                break
            if BLOCK_OPEN_RE.match(peek):
                break
            if CALLOUT_OPEN_RE.match(peek):
                break
            if is_eq_rule(peek) or is_dash_rule(peek):
                break
            if HEADING_DOT_RE.match(peek):
                break
            if FENCE_OPEN_RE.match(peek_raw):
                break
            if peek_raw.lstrip().startswith(("- ", "* ", "• ")):
                break
            if ORDERED_LIST_RE.match(peek):
                break
            if peek_raw.startswith("    ") or peek_raw.startswith("\t"):
                break
            body_parts.append(sanitize_para(peek))
            i += 1

        html = f'<b>{num}. {title}:</b>'
        if body_parts:
            html += ' ' + ' '.join(body_parts)
        items.append(ctx.p(html))

        while i < len(lines) and not lines[i].strip():
            nxt = peek_next_nonempty(lines, i + 1)
            if nxt and STEP_ITEM_RE.match(nxt):
                i += 1
            else:
                break

    return [ctx.ol(items)], i


def condbreak(story: List[Flowable], min_space: int) -> None:
    if story and isinstance(story[-1], Paragraph) and bool(getattr(story[-1], "_fbd_is_heading", False)):
        h = story.pop()
        story.append(CondPageBreak(min_space))
        story.append(h)
    else:
        story.append(CondPageBreak(min_space))


def pipe_align_from_sep(cell: str) -> Optional[str]:
    c = cell.strip()
    if not PIPE_SEP_CELL_RE.match(c):
        return None
    left = c.startswith(":")
    right = c.endswith(":")
    if left and right:
        return "CENTER"
    if right:
        return "RIGHT"
    if left:
        return "LEFT"
    return None


def parse_pipe_table(body_lines: List[str]) -> Tuple[List[List[str]], Optional[List[Optional[str]]]]:
    raw_rows: List[List[str]] = []
    for ln in body_lines:
        s = ln.strip()
        if not s or not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip().strip("|").split("|")]
        raw_rows.append(cells)

    if not raw_rows:
        return [[""]], None

    aligns: Optional[List[Optional[str]]] = None
    if len(raw_rows) >= 2 and all(PIPE_SEP_CELL_RE.match(c.strip()) for c in raw_rows[1]):
        aligns = [pipe_align_from_sep(c) for c in raw_rows[1]]
        raw_rows.pop(1)

    rows = [[sanitize_para(c) for c in r] for r in raw_rows]
    if aligns is not None:
        ncols = max(len(r) for r in rows) if rows else len(aligns)
        aligns = (list(aligns) + [None] * max(0, ncols - len(aligns)))[:ncols]

    return rows, aligns
