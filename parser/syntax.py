from __future__ import annotations

import re
from typing import Optional, Tuple

FIG_RE = re.compile(
    r'^\[FIG\s+file="(?P<file>[^"]+)"\s+page=(?P<page>\d+)(?:\s+caption="(?P<caption>[^"]*)")?(?:\s+zoom=(?P<zoom>[\d.]+))?\s*\]\s*$'
)
IMG_RE = re.compile(
    r'^\[IMG\s+file="(?P<file>[^"]+)"(?:\s+caption="(?P<caption>[^"]*)")?(?:\s+width=(?P<width>[\d.]+))?\s*\]\s*$'
)
PB_RE = re.compile(r"^\[(?:PAGEBREAK|PB)\]\s*$")
CALLOUT_OPEN_RE = re.compile(
    r'^\[(?P<kind>NOTE|WARN|DANGER|INFO|TIP|CHECK)(?:\s+title="(?P<title>[^"]*)")?\]\s*$'
)
CALLOUT_CLOSE_RE = re.compile(r"^\[/(?P<kind>NOTE|WARN|DANGER|INFO|TIP|CHECK)\]\s*$")
BLOCK_OPEN_RE = re.compile(r"^:::(?P<kind>[A-Za-z0-9_-]+)(?:\s+(?P<title>.+))?\s*$")
BLOCK_CLOSE_RE = re.compile(r"^:::\s*$")
FENCE_OPEN_RE = re.compile(r"^\s*```(?P<lang>[A-Za-z0-9_+-]+)?\s*$")
FENCE_CLOSE_RE = re.compile(r"^\s*```\s*$")
HEADING_DOT_RE = re.compile(r"^(?P<num>\d+\.\d+(?:\.\d+)*)\.\s+(?P<title>.+)$")
SIMPLE_HEADING_RE = re.compile(r"^(?P<num>\d+)\.\s+(?P<title>.+)$")
HEADING_BLOCK_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)*)(?P<delim>[.)])\s+(?P<title>.+)$")
STEP_ITEM_RE = re.compile(r"^(?P<num>\d+)\.\s+(?P<title>.+?)\s*:\s*$")
ORDERED_LIST_RE = re.compile(r"^\d+[.)]\s+")
PIPE_SEP_CELL_RE = re.compile(r"^:?-{3,}:?$")


def parse_fig_marker(line: str) -> Optional[Tuple[str, int, Optional[str], float]]:
    match = FIG_RE.match(line.strip())
    if not match:
        return None
    zoom = float(match.group("zoom")) if match.group("zoom") else 2.0
    return match.group("file"), int(match.group("page")), match.group("caption"), zoom


def parse_img_marker(line: str) -> Optional[Tuple[str, Optional[str], Optional[float]]]:
    match = IMG_RE.match(line.strip())
    if not match:
        return None
    width = float(match.group("width")) if match.group("width") else None
    return match.group("file"), match.group("caption"), width
