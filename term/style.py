from __future__ import annotations

from dataclasses import dataclass

# ANSI helpers
RESET = "\x1b[0m"
BOLD = "\x1b[1m"
DIM = "\x1b[2m"

FG_RED = "\x1b[31m"
FG_GREEN = "\x1b[32m"
FG_YELLOW = "\x1b[33m"
FG_BLUE = "\x1b[34m"
FG_MAGENTA = "\x1b[35m"
FG_CYAN = "\x1b[36m"
FG_GRAY = "\x1b[90m"

@dataclass(frozen=True)
class Glyphs:
    ok: str
    warn: str
    err: str
    dot: str
    arrow: str

UNICODE_GLYPHS = Glyphs(ok="✓", warn="⚠", err="✗", dot="•", arrow="→")
ASCII_GLYPHS   = Glyphs(ok="OK", warn="WARN", err="ERR", dot="-", arrow="->")
