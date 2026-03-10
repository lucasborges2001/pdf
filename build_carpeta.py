#!/usr/bin/env python3
"""_pdf/build_carpeta.py

Build recursivo por carpeta:
- Recorre una carpeta arbitraria buscando `.txt` de forma recursiva.
- Genera cada PDF junto al `.txt` de origen.

Interfaz de CLI:
- Requiere `--carpeta <PATH>`.
- Por compatibilidad, si el primer argumento no empieza con `-` se interpreta como la ruta.

Ejemplos:
- python -m _pdf.build_carpeta D:\ruta\docs\tutoriales_cargadores
- python -m _pdf.build_carpeta --carpeta D:\ruta\docs\tutoriales_cargadores
- python -m _pdf.build_carpeta --carpeta ... --only crearUsuario cargarSaldo
- python -m _pdf.build_carpeta --carpeta ... --check

Salida en terminal se centraliza en `_pdf/term/`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from .engine.compile import compile_txt
from .engine.scanlib import scan_materia
from .term.flags import (
    add_common_flags,
    console_from_args,
    verbosity_from_args,
    output_mode_from_args,
    show_summary_from_args,
)
from .term.printers import print_scan_report, print_build_summary


SKIP_DIR_NAMES = {
    ".git",
    ".github",
    ".venv",
    "__pycache__",
    "node_modules",
    "output",
    "input",
}


def _normalize_argv(argv: Optional[List[str]]) -> Optional[List[str]]:
    """Compatibilidad: `python -m _pdf.build_carpeta D:\docs` -> `--carpeta D:\docs`.
    """
    if not argv:
        return argv
    if argv and not argv[0].startswith("-"):
        return ["--carpeta", argv[0], *argv[1:]]
    return argv


def _should_skip_dir(path: Path) -> bool:
    return path.name in SKIP_DIR_NAMES


def _discover_txts(root: Path, only_names: Optional[Sequence[str]] = None) -> List[Path]:
    txts: List[Path] = []
    only_set = {name.lower() for name in only_names} if only_names else None

    for path in sorted(root.rglob("*.txt")):
        if any(_should_skip_dir(parent) for parent in path.parents):
            continue
        if only_set and path.parent.name.lower() not in only_set and path.stem.lower() not in only_set:
            continue
        txts.append(path)

    return txts


def main(argv: Optional[List[str]] = None) -> None:
    argv = _normalize_argv(argv if argv is not None else sys.argv[1:])

    ap = argparse.ArgumentParser(
        prog="python -m _pdf.build_carpeta",
        description="Compila una carpeta recursiva y deja cada PDF junto al .txt de origen.",
    )

    ap.add_argument(
        "--carpeta",
        "-c",
        required=True,
        help=r"Ruta raíz a recorrer (ej: C:\repo\docs\tutoriales_cargadores).",
    )
    ap.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Filtra por nombre de carpeta o nombre base de archivo (ej: crearUsuario cargarSaldo).",
    )
    ap.add_argument("--check", action="store_true", help="Solo valida formato y assets (no genera PDFs).")
    ap.add_argument("--strict", action="store_true", help="En --check, cuenta WARN como error (exit code).")

    add_common_flags(ap, include_limits=True)
    args = ap.parse_args(argv)

    c = console_from_args(args)
    mode = output_mode_from_args(args)
    show_summary = show_summary_from_args(args)
    verbosity = verbosity_from_args(args)

    carpeta = Path(args.carpeta).expanduser().resolve()
    if not carpeta.is_dir():
        if not args.quiet:
            c.print(c.red(f"{c.g.err} Ruta inválida: {carpeta}"))
        raise SystemExit(2)

    if args.check:
        report = scan_materia(materia=carpeta)
        print_scan_report(
            c,
            report,
            mode=mode,
            show_summary=show_summary,
            verbosity=verbosity,
            max_issues=args.max_issues,
            show_skipped=args.show_skipped,
            max_skipped=args.max_skipped,
            title=f"CHECK CARPETA: {carpeta}",
        )
        if args.strict:
            raise SystemExit(1 if (report.errors or report.warns) else 0)
        raise SystemExit(1 if report.errors else 0)

    txts = _discover_txts(carpeta, only_names=args.only)
    if not txts:
        if not args.quiet:
            c.print(c.yellow(f"{c.g.warn} No se encontraron .txt en: {carpeta}"))
        raise SystemExit(0)

    built = 0
    ok = True

    for txt in txts:
        try:
            out_dir = txt.parent
            out_name = f"{txt.stem}.pdf"
            out_pdf = compile_txt(
                txt_path=txt,
                out_dir=out_dir,
                out_name=out_name,
                materia=carpeta,
                extra_search_dirs=None,
            )
            built += 1
            if verbosity >= 2 and not args.quiet:
                c.print(f"  {c.g.dot} {txt.name} {c.g.arrow} {out_pdf}")
        except Exception as e:
            ok = False
            if not args.quiet:
                c.print(c.red(f"{c.g.err} ERROR en {txt}: {e}"))

    if not args.quiet:
        print_build_summary(c, ok=ok, built=built, out_dir=carpeta, mode=mode, show_summary=show_summary)
        if show_summary and mode != "quiet":
            c.print(f"  {c.gray('output')} {c.g.arrow} mismo directorio de cada .txt")

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
