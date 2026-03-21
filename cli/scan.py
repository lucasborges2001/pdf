from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from ..pipeline.scan import report_to_dict, scan_input, scan_materia
from ..term.flags import add_common_flags, console_from_args, output_mode_from_args, show_summary_from_args, verbosity_from_args
from ..term.printers import print_scan_report


def main(argv: Optional[list[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m _pdf.scan", description="Scan/Lint del formato .txt (sin generar PDF).")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--materia", type=str, help="Ruta de la materia a escanear.")
    group.add_argument("--input", action="store_true", help="Escanea _pdf/input/*.txt.")
    ap.add_argument("--strict", action="store_true", help="Cuenta WARN como error.")
    add_common_flags(ap, include_limits=True)
    args = ap.parse_args(argv)

    console = console_from_args(args)
    mode = output_mode_from_args(args)
    show_summary = show_summary_from_args(args)
    verbosity = verbosity_from_args(args)

    if args.input:
        report = scan_input(pkg_root=Path(__file__).resolve().parent.parent)
        title = "SCAN INPUT"
    else:
        materia = Path(args.materia).expanduser().resolve()
        if not materia.is_dir():
            console.print(f"Ruta inválida: {materia}")
            raise SystemExit(2)
        report = scan_materia(materia=materia)
        title = f"SCAN MATERIA: {materia}"

    if args.log_json:
        Path(args.log_json).write_text(json.dumps(report_to_dict(report), indent=2, ensure_ascii=False), encoding="utf-8")

    print_scan_report(
        console,
        report,
        mode=mode,
        show_summary=show_summary,
        verbosity=verbosity,
        max_issues=args.max_issues,
        show_skipped=args.show_skipped,
        max_skipped=args.max_skipped,
        title=title,
    )
    raise SystemExit(1 if (report.errors or (args.strict and report.warns)) else 0)
