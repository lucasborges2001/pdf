#!/usr/bin/env python3
"""_pdf/scan.py

Diagnóstico rápido: recorre carpetas, detecta .txt candidatos y valida formato.
No genera PDFs.

Exit codes:
  0 = OK (sin errores)
  1 = errores (o warnings si --strict)
  2 = parámetros / path inválido
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from .engine.scanlib import scan_input, scan_materia, report_to_dict
from .term.flags import add_common_flags, console_from_args, verbosity_from_args, output_mode_from_args, show_summary_from_args
from .term.printers import print_scan_report


def main(argv: Optional[list[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m _pdf.scan", description="Scan/Lint del formato .txt (sin generar PDF).")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--materia", type=str, help="Ruta de la materia a escanear (recursivo).")
    g.add_argument("--input", action="store_true", help="Escanea _pdf/input/*.txt.")
    ap.add_argument("--strict", action="store_true", help="Cuenta WARN como error (exit code).")

    add_common_flags(ap, include_limits=True)
    args = ap.parse_args(argv)

    c = console_from_args(args)
    mode = output_mode_from_args(args)
    show_summary = show_summary_from_args(args)
    verbosity = verbosity_from_args(args)

    if args.input:
        report = scan_input(pkg_root=Path(__file__).resolve().parent)
        print_scan_report(
            c,
            report,
            mode=mode,
            show_summary=show_summary,
            verbosity=verbosity,
            max_issues=args.max_issues,
            show_skipped=args.show_skipped,
            max_skipped=args.max_skipped,
            title="SCAN INPUT",
        )
    else:
        materia = Path(args.materia).expanduser().resolve()
        if not materia.is_dir():
            c.print(f"Ruta inválida: {materia}")
            raise SystemExit(2)
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
            title=f"SCAN MATERIA: {materia}",
        )

    # Exit code
    if args.strict:
        raise SystemExit(1 if (report.errors or report.warns) else 0)
    raise SystemExit(1 if report.errors else 0)


if __name__ == "__main__":
    main()
