from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Sequence

from .style import (
    RESET, BOLD, DIM,
    FG_RED, FG_GREEN, FG_YELLOW, FG_CYAN, FG_GRAY,
    UNICODE_GLYPHS, ASCII_GLYPHS,
)

@dataclass
class ConsoleOpts:
    color: bool = True
    unicode: bool = True
    width: Optional[int] = None


class TeeOut:
    """Escribe en múltiples streams (stdout + archivo de log)."""
    def __init__(self, *outs):
        self.outs = [o for o in outs if o is not None]

    def write(self, s: str) -> int:
        n = 0
        for o in self.outs:
            try:
                r = o.write(s)
                if isinstance(r, int):
                    n = max(n, r)
            except Exception:
                pass
        return n

    def flush(self) -> None:
        for o in self.outs:
            try:
                o.flush()
            except Exception:
                pass

    def isatty(self) -> bool:
        for o in self.outs:
            try:
                if hasattr(o, "isatty") and o.isatty():
                    return True
            except Exception:
                pass
        return False

class Console:
    def __init__(self, *, out=None, opts: Optional[ConsoleOpts]=None):
        self.out = out or sys.stdout
        self.opts = opts or ConsoleOpts()
        if self.opts.width is None:
            try:
                self.opts.width = shutil.get_terminal_size((100, 20)).columns
            except Exception:
                self.opts.width = 100

        # auto-disable color if not tty (unless forced by caller)
        try:
            if hasattr(self.out, "isatty") and not self.out.isatty():
                self.opts.color = False
        except Exception:
            pass

        self.g = UNICODE_GLYPHS if self.opts.unicode else ASCII_GLYPHS

    def _c(self, s: str, code: str) -> str:
        if not self.opts.color:
            return s
        return f"{code}{s}{RESET}"

    def bold(self, s: str) -> str:
        return self._c(s, BOLD)

    def dim(self, s: str) -> str:
        return self._c(s, DIM)

    def green(self, s: str) -> str:
        return self._c(s, FG_GREEN)

    def yellow(self, s: str) -> str:
        return self._c(s, FG_YELLOW)

    def red(self, s: str) -> str:
        return self._c(s, FG_RED)

    def cyan(self, s: str) -> str:
        return self._c(s, FG_CYAN)

    def gray(self, s: str) -> str:
        return self._c(s, FG_GRAY)

    def print(self, s: str = "") -> None:
        self.out.write(s + os.linesep)

    def rule(self, title: str = "") -> None:
        w = max(20, int(self.opts.width or 80))
        if title:
            t = f" {title} "
            pad = max(0, w - len(t))
            left = pad // 2
            right = pad - left
            self.print(self.gray("=" * left) + self.bold(t) + self.gray("=" * right))
        else:
            self.print(self.gray("=" * w))

    def kv(self, items: Sequence[tuple[str, Any]], *, indent: int = 0) -> None:
        pad = " " * indent
        if not items:
            return
        kmax = max(len(k) for k, _ in items)
        for k, v in items:
            self.print(f"{pad}{self.bold(k.ljust(kmax))} : {v}")

    def table(self, headers: Sequence[str], rows: Sequence[Sequence[Any]], *, indent: int = 0) -> None:
        pad = " " * indent
        cols = len(headers)
        widths = [len(str(h)) for h in headers]
        for r in rows:
            for i in range(cols):
                widths[i] = max(widths[i], len(str(r[i])))

        def fmt_row(r):
            return pad + "  ".join(str(r[i]).ljust(widths[i]) for i in range(cols))

        self.print(self.bold(fmt_row(headers)))
        self.print(self.gray(pad + "  ".join("-" * w for w in widths)))
        for r in rows:
            self.print(fmt_row(r))
