from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from ..pipeline.compile import compile_txt
from ..pipeline.discovery import discover_tree_txts
from ..pipeline.scan import scan_materia
from ..term.flags import add_common_flags, console_from_args, output_mode_from_args, show_summary_from_args, verbosity_from_args
from ..term.printers import print_build_summary, print_scan_report
from .common import normalize_path_argv


def main(argv: Optional[List[str]] = None) -> None:
    argv = normalize_path_argv(argv if argv is not None else sys.argv[1:], flag="--carpeta")

    ap = argparse.ArgumentParser(
        prog="python -m _pdf.build_carpeta",
        description="Compila una carpeta recursiva y deja cada PDF junto al .txt de origen.",
    )
    ap.add_argument("--carpeta", "-c", required=True, help=r"Ruta raíz a recorrer.")
    ap.add_argument("--only", nargs="*", default=None, help="Filtra por nombre de carpeta o nombre base de archivo.")
    ap.add_argument("--check", action="store_true", help="Solo valida formato y assets (no genera PDFs).")
    ap.add_argument("--strict", action="store_true", help="En --check, cuenta WARN como error.")
    add_common_flags(ap, include_limits=True)
    args = ap.parse_args(argv)

    console = console_from_args(args)
    mode = output_mode_from_args(args)
    show_summary = show_summary_from_args(args)
    verbosity = verbosity_from_args(args)

    carpeta = Path(args.carpeta).expanduser().resolve()
    if not carpeta.is_dir():
        if not args.quiet:
            console.print(console.red(f"{console.g.err} Ruta inválida: {carpeta}"))
        raise SystemExit(2)

    if args.check:
        report = scan_materia(materia=carpeta)
        print_scan_report(
            console,
            report,
            mode=mode,
            show_summary=show_summary,
            verbosity=verbosity,
            max_issues=args.max_issues,
            show_skipped=args.show_skipped,
            max_skipped=args.max_skipped,
            title=f"CHECK CARPETA: {carpeta}",
        )
        raise SystemExit(1 if (report.errors or (args.strict and report.warns)) else 0)

    txts = discover_tree_txts(carpeta, only_names=args.only)
    if not txts:
        if not args.quiet:
            console.print(console.yellow(f"{console.g.warn} No se encontraron .txt en: {carpeta}"))
        raise SystemExit(0)

    built = 0
    ok = True
    for txt in txts:
        try:
            out_pdf = compile_txt(txt_path=txt, out_dir=txt.parent, out_name=f"{txt.stem}.pdf", materia=carpeta)
            built += 1
            if verbosity >= 2 and not args.quiet:
                console.print(f"  {console.g.dot} {txt.name} {console.g.arrow} {out_pdf}")
        except Exception as exc:
            ok = False
            if not args.quiet:
                console.print(console.red(f"{console.g.err} ERROR en {txt}: {exc}"))

    if not args.quiet:
        print_build_summary(console, ok=ok, built=built, out_dir=carpeta, mode=mode, show_summary=show_summary)
        if show_summary and mode != "quiet":
            console.print(f"  {console.gray('output')} {console.g.arrow} mismo directorio de cada .txt")
    raise SystemExit(0 if ok else 1)
