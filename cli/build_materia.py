from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from ..pipeline.compile import compile_txt
from ..pipeline.jobs import discover_jobs
from ..pipeline.scan import scan_materia
from ..term.flags import add_common_flags, console_from_args, output_mode_from_args, show_summary_from_args, verbosity_from_args
from ..term.printers import print_build_summary, print_scan_report
from .common import normalize_path_argv


def main(argv: Optional[List[str]] = None) -> None:
    argv = normalize_path_argv(argv if argv is not None else sys.argv[1:], flag="--materia")

    ap = argparse.ArgumentParser(
        prog="python -m _pdf.build_materia",
        description="Compila una materia -> <Materia>/Resumenes/ y copia junto al .txt",
    )
    ap.add_argument("--materia", "-m", required=True, help=r"Ruta de la materia (ej: D:\ArqComp).")
    ap.add_argument("--area", choices=["teorico", "practico", "taller", "both", "all"], default="all")
    ap.add_argument("--only", nargs="*", default=None, help="Filtra por prefijos (ej: 00 01 07).")
    ap.add_argument("--check", action="store_true", help="Solo valida formato y assets (no genera PDFs).")
    ap.add_argument("--strict", action="store_true", help="En --check, cuenta WARN como error.")
    add_common_flags(ap, include_limits=True)
    args = ap.parse_args(argv)

    console = console_from_args(args)
    mode = output_mode_from_args(args)
    show_summary = show_summary_from_args(args)
    verbosity = verbosity_from_args(args)

    materia = Path(args.materia).expanduser().resolve()
    if not materia.is_dir():
        if not args.quiet:
            console.print(console.red(f"{console.g.err} Ruta inválida: {materia}"))
        raise SystemExit(2)

    if args.check:
        report = scan_materia(materia=materia)
        print_scan_report(
            console,
            report,
            mode=mode,
            show_summary=show_summary,
            verbosity=verbosity,
            max_issues=args.max_issues,
            show_skipped=args.show_skipped,
            max_skipped=args.max_skipped,
            title=f"CHECK MATERIA: {materia}",
        )
        raise SystemExit(1 if (report.errors or (args.strict and report.warns)) else 0)

    only_prefixes: Optional[Sequence[str]] = args.only if args.only else None
    jobs = discover_jobs(materia, area=args.area, only_prefixes=only_prefixes)

    built = 0
    ok = True
    for job in jobs:
        try:
            primary_out = compile_txt(
                txt_path=job.txt_path,
                out_dir=job.out_dirs[0],
                out_name=job.out_name,
                materia=materia,
                extra_search_dirs=None,
            )
            for extra_out_dir in job.out_dirs[1:]:
                extra_out_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(primary_out, extra_out_dir / job.out_name)
            built += 1
            if verbosity >= 2 and not args.quiet:
                rendered = ", ".join(str(out_dir / job.out_name) for out_dir in job.out_dirs)
                console.print(f"  {console.g.dot} {job.txt_path.name} {console.g.arrow} {rendered}")
        except Exception as exc:
            ok = False
            if not args.quiet:
                console.print(console.red(f"{console.g.err} ERROR en {job.txt_path}: {exc}"))

    if not args.quiet:
        out_root = materia / "Resumenes"
        print_build_summary(console, ok=ok, built=built, out_dir=out_root, mode=mode, show_summary=show_summary)
        if show_summary and mode != "quiet":
            console.print(f"  {console.gray('mirror')} {console.g.arrow} carpetas origen de cada .txt")

    raise SystemExit(0 if ok else 1)
