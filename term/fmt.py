from __future__ import annotations

from typing import Iterable, List

def trunc(s: str, max_len: int) -> str:
    if max_len <= 3:
        return s[:max_len]
    if len(s) <= max_len:
        return s
    return s[: max_len - 1] + "…"

def indent_lines(lines: Iterable[str], n: int) -> List[str]:
    pad = " " * n
    return [pad + ln if ln else ln for ln in lines]
