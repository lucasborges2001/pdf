from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from reportlab.platypus import CondPageBreak
from reportlab.platypus.paragraph import Paragraph

from ..runtime.ctx import PdfCtx
from .inline import _inline_rl, _normalize_unicode, sanitize_para
from .syntax import (
    BLOCK_OPEN_RE,
    CALLOUT_OPEN_RE,
    FENCE_OPEN_RE,
    HEADING_DOT_RE,
    ORDERED_LIST_RE,
    PB_RE,
    PIPE_SEP_CELL_RE,
    SIMPLE_HEADING_RE,
    STEP_ITEM_RE,
    parse_fig_marker,
    parse_img_marker,
)

Flowable = Any


def is_rule(line: str, ch: str, min_len: int) -> bool:
    stripped = line.strip()
    return len(stripped) >= min_len and set(stripped) == {ch}


def is_eq_rule(line: str) -> bool:
    return is_rule(line, "=", 10)


def is_dash_rule(line: str) -> bool:
    return is_rule(line, "-", 5)


def slugify(text: str) -> str:
    text = _normalize_unicode(text).lower().strip()
    text = re.sub(r"[^\w\s.-]", "", text)
    text = re.sub(r"[\s.]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    return text or "sec"


def unique_key(base: str, used: Dict[str, int]) -> str:
    key = slugify(base)
    count = used.get(key, 0)
    used[key] = count + 1
    return key if count == 0 else f"{key}-{count + 1}"


def mk_heading(ctx: PdfCtx, text: str, level: int, key: str, *, in_callout: bool) -> Flowable:
    style = ctx.h2 if level <= 1 else ctx.h3
    paragraph = ctx.p(f'<a name="{key}"/>{_inline_rl(text)}', style)
    setattr(paragraph, "_fbd_key", key)
    setattr(paragraph, "_fbd_level", max(0, int(level) - 1))
    setattr(paragraph, "_fbd_is_heading", True)
    if in_callout:
        setattr(paragraph, "_fbd_skip_toc", True)
        setattr(paragraph, "_fbd_skip_outline", True)
    return paragraph


def peek_next_nonempty(lines: List[str], start: int) -> Optional[str]:
    idx = start
    while idx < len(lines):
        stripped = lines[idx].strip()
        if stripped:
            return stripped
        idx += 1
    return None


def is_procedural_step_start(lines: List[str], idx: int) -> bool:
    line = lines[idx].strip()
    if not STEP_ITEM_RE.match(line):
        return False
    nxt = peek_next_nonempty(lines, idx + 1)
    if not nxt or STEP_ITEM_RE.match(nxt):
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


def looks_like_simple_dot_heading(lines: List[str], idx: int) -> bool:
    line = lines[idx].strip()
    match = SIMPLE_HEADING_RE.match(line)
    if not match:
        return False

    title = (match.group("title") or "").strip()
    if not title:
        return False

    nxt = peek_next_nonempty(lines, idx + 1)
    if nxt and ORDERED_LIST_RE.match(nxt):
        return False
    if title.endswith((":", ";", ".", "?", "!")):
        return False
    if len(title.split()) > 12:
        return False

    has_alpha = any(ch.isalpha() for ch in title)
    has_lower = any(ch.isalpha() and ch.islower() for ch in title)
    if has_alpha and not has_lower:
        return True

    words = [word for word in re.split(r"\s+", title) if word]
    title_case_words = 0
    for word in words:
        lead = next((ch for ch in word if ch.isalpha()), "")
        if lead and lead.isupper():
            title_case_words += 1
    return bool(words) and title_case_words >= max(1, len(words) - 1)


def consume_procedural_steps(ctx: PdfCtx, lines: List[str], start: int) -> Tuple[List[Flowable], int]:
    items: List[Paragraph] = []
    idx = start
    while idx < len(lines):
        line = lines[idx].strip()
        match = STEP_ITEM_RE.match(line)
        if not match:
            break

        num = match.group("num")
        title = sanitize_para(match.group("title"))
        idx += 1

        body_parts: List[str] = []
        while idx < len(lines):
            peek_raw = lines[idx].rstrip("\n")
            peek = peek_raw.strip()
            if not peek:
                break
            if STEP_ITEM_RE.match(peek) or PB_RE.match(peek):
                break
            if parse_fig_marker(peek) or parse_img_marker(peek):
                break
            if BLOCK_OPEN_RE.match(peek) or CALLOUT_OPEN_RE.match(peek):
                break
            if is_eq_rule(peek) or is_dash_rule(peek):
                break
            if HEADING_DOT_RE.match(peek) or ORDERED_LIST_RE.match(peek):
                break
            if FENCE_OPEN_RE.match(peek_raw):
                break
            if peek_raw.lstrip().startswith(("- ", "* ", "â€¢ ")):
                break
            if peek_raw.startswith("    ") or peek_raw.startswith("\t"):
                break
            body_parts.append(sanitize_para(peek))
            idx += 1

        html = f"<b>{num}. {title}:</b>"
        if body_parts:
            html += " " + " ".join(body_parts)
        items.append(ctx.p(html))

        while idx < len(lines) and not lines[idx].strip():
            nxt = peek_next_nonempty(lines, idx + 1)
            if nxt and STEP_ITEM_RE.match(nxt):
                idx += 1
            else:
                break

    return [ctx.ol(items)], idx


def condbreak(story: List[Flowable], min_space: int) -> None:
    if story and isinstance(story[-1], Paragraph) and bool(getattr(story[-1], "_fbd_is_heading", False)):
        heading = story.pop()
        story.append(CondPageBreak(min_space))
        story.append(heading)
        return
    story.append(CondPageBreak(min_space))


def pipe_align_from_sep(cell: str) -> Optional[str]:
    stripped = cell.strip()
    if not PIPE_SEP_CELL_RE.match(stripped):
        return None
    left = stripped.startswith(":")
    right = stripped.endswith(":")
    if left and right:
        return "CENTER"
    if right:
        return "RIGHT"
    if left:
        return "LEFT"
    return None


def parse_pipe_table(body_lines: List[str]) -> Tuple[List[List[str]], Optional[List[Optional[str]]]]:
    raw_rows: List[List[str]] = []
    for line in body_lines:
        stripped = line.strip()
        if stripped and stripped.startswith("|"):
            raw_rows.append([cell.strip() for cell in stripped.strip("|").split("|")])

    if not raw_rows:
        return [[""]], None

    aligns: Optional[List[Optional[str]]] = None
    if len(raw_rows) >= 2 and all(PIPE_SEP_CELL_RE.match(cell.strip()) for cell in raw_rows[1]):
        aligns = [pipe_align_from_sep(cell) for cell in raw_rows[1]]
        raw_rows.pop(1)

    rows = [[sanitize_para(cell) for cell in row] for row in raw_rows]
    if aligns is not None:
        ncols = max(len(row) for row in rows) if rows else len(aligns)
        aligns = (list(aligns) + [None] * max(0, ncols - len(aligns)))[:ncols]
    return rows, aligns
