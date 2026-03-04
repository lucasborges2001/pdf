from __future__ import annotations

import argparse
from typing import Literal

from .console import Console, ConsoleOpts

OutputMode = Literal["normal", "only_summary", "quiet"]

def add_common_flags(ap: argparse.ArgumentParser, *, include_limits: bool = True) -> None:
    mx = ap.add_mutually_exclusive_group()
    mx.add_argument("--quiet", action="store_true", help="No imprime nada si está OK; si hay errores, imprime mínimo.")
    mx.add_argument("--only-summary", action="store_true", help="Imprime solo el resumen final (sin detalle).")

    ap.add_argument("--no-summary", action="store_true", help="No imprime el resumen final (solo detalle).")

    ap.add_argument("-v", "--verbose", action="count", default=0, help="Más detalle (-v, -vv).")
    ap.add_argument("--no-color", action="store_true", help="Desactiva colores ANSI.")
    ap.add_argument("--ascii", action="store_true", help="Usa ASCII en vez de símbolos unicode.")
    ap.add_argument("--log", type=str, default=None, help="Escribe salida de terminal también a un archivo (overwrite).")
    ap.add_argument("--log-json", type=str, default=None, help="Escribe un reporte JSON (scan/check) a un archivo.")
    if include_limits:
        ap.add_argument("--max-issues", type=int, default=30, help="Máximo de issues a imprimir.")
        ap.add_argument("--show-skipped", action="store_true", help="Lista .txt ignorados por heurística.")
        ap.add_argument("--max-skipped", type=int, default=30, help="Máximo de skipped a imprimir.")

def output_mode_from_args(args) -> OutputMode:
    if getattr(args, "quiet", False):
        return "quiet"
    if getattr(args, "only_summary", False):
        return "only_summary"
    return "normal"

def verbosity_from_args(args) -> int:
    # 0 -> sin detalle, 1 -> normal, 2 -> verbose
    v = int(getattr(args, "verbose", 0) or 0)
    return 1 + min(v, 1)

def show_summary_from_args(args) -> bool:
    return not bool(getattr(args, "no_summary", False))

def console_from_args(args) -> Console:
    opts = ConsoleOpts(
        color=not bool(getattr(args, "no_color", False)),
        unicode=not bool(getattr(args, "ascii", False)),
        width=None,
    )
    return Console(opts=opts)
