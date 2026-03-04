#!/usr/bin/env python3
"""_pdf/build_materia.py

Build por materia (centralizado):
- Recorre la materia completa, descubre .txt candidatos (Practico/Taller) y compila.
- Copia salida a: <Materia>/Resumenes/(Practico|Taller)/

Opcional:
- --check: valida formato (scan) sin generar PDFs
- --only: mantiene compatibilidad con prefijos 00/01/... (filtra por partes del path)

Salida en terminal se centraliza en _pdf/term/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List, Optional, Sequence

from .engine.compile import compile_txt
from .engine.materia import discover_jobs
from .engine.scanlib import scan_materia
from .term.flags import add_common_flags, console_from_args, verbosity_from_args, output_mode_from_args, show_summary_from_args
from .term.printers import print_scan_report, print_build_summary


def _prompt_path() -> Path:
    s = input(r"Ruta de la materia (ej: D:\ArqComp): ").strip().strip('"').strip("'")
    return Path(s).expanduser().resolve()


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m _pdf.build_materia", description="Compila una materia -> Resumenes/")
    ap.add_argument("materia", nargs="?", default=None, help="Ruta de la materia (si no se pasa, se pide).")
    ap.add_argument("--area", choices=["practico", "taller", "both"], default="both", help="Qué áreas compilar.")
    ap.add_argument("--only", nargs="*", default=None, help="Filtra por prefijos (ej: 00 01 07).")
    ap.add_argument("--check", action="store_true", help="Solo valida formato y assets (no genera PDFs).")
    ap.add_argument("--strict", action="store_true", help="En --check, cuenta WARN como error (exit code).")

    add_common_flags(ap, include_limits=True)
    args = ap.parse_args(argv)

    c = console_from_args(args)
    mode = output_mode_from_args(args)
    show_summary = show_summary_from_args(args)
    verbosity = verbosity_from_args(args)

    materia = Path(args.materia).expanduser().resolve() if args.materia else _prompt_path()
    if not materia.is_dir():
        if not args.quiet:
            c.print(c.red(f"{c.g.err} Ruta inválida: {materia}"))
        raise SystemExit(2)

    if args.check:
        report = scan_materia(materia=materia)
        print_scan_report(
            c,
            report,
            mode=mode,
            show_summary=show_summary,
            verbosity=verbosity,
            max_issues=args.max_issues,
            show_skipped=args.show_skipped,
            max_skipped=args.max_skipped,
            title=f"CHECK MATERIA: {materia}",
        )
        if args.strict:
            raise SystemExit(1 if (report.errors or report.warns) else 0)
        raise SystemExit(1 if report.errors else 0)

    only_prefixes: Optional[Sequence[str]] = args.only if args.only else None
    jobs = discover_jobs(materia, area=args.area, only_prefixes=only_prefixes)

    built = 0
    ok = True

    for job in jobs:
        try:
            compile_txt(
                txt_path=job.txt_path,
                out_dir=job.out_dir,
                out_name=job.out_name,
                materia=materia,
                extra_search_dirs=None,
            )
            built += 1
            if verbosity >= 2 and not args.quiet:
                c.print(f"  {c.g.dot} {job.txt_path.name} {c.g.arrow} {job.out_dir / job.out_name}")
        except Exception as e:
            ok = False
            if not args.quiet:
                c.print(c.red(f"{c.g.err} ERROR en {job.txt_path}: {e}"))

    if not args.quiet:
        # Destino principal
        out_root = materia / "Resumenes"
        print_build_summary(c, ok=ok, built=built, out_dir=out_root)

    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
