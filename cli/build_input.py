from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import List, Optional

from ..pipeline.compile import compile_txt
from ..pipeline.scan import report_to_dict, scan_input
from ..term.flags import add_common_flags, console_from_args, output_mode_from_args, show_summary_from_args, verbosity_from_args
from ..term.printers import print_build_summary, print_scan_report


def main(argv: Optional[List[str]] = None) -> None:
    ap = argparse.ArgumentParser(prog="python -m _pdf.build", description="Compila _pdf/input/*.txt -> _pdf/output/*.pdf")
    ap.add_argument("--clean", action="store_true", help="Borra output/ antes de compilar.")
    ap.add_argument("--check", action="store_true", help="Solo valida formato y assets (no genera PDFs).")
    ap.add_argument("--strict", action="store_true", help="En --check, cuenta WARN como error.")
    ap.add_argument("--materia", type=str, default=None, help="Ruta de materia para ayudar a resolver assets.")
    ap.add_argument("--search-dir", action="append", default=[], help="Directorio extra para buscar assets.")
    add_common_flags(ap, include_limits=True)
    args = ap.parse_args(argv)

    console = console_from_args(args)
    mode = output_mode_from_args(args)
    show_summary = show_summary_from_args(args)
    verbosity = verbosity_from_args(args)

    pkg_root = Path(__file__).resolve().parent.parent
    input_dir = pkg_root / "input"
    out_dir = pkg_root / "output"
    out_dir.mkdir(exist_ok=True)

    if args.check:
        report = scan_input(pkg_root=pkg_root)
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
            title="CHECK INPUT",
        )
        raise SystemExit(1 if (report.errors or (args.strict and report.warns)) else 0)

    if args.clean and out_dir.exists():
        shutil.rmtree(out_dir)
        out_dir.mkdir(exist_ok=True)

    materia = Path(args.materia).expanduser().resolve() if args.materia else None
    search_dirs = [Path(path).expanduser().resolve() for path in (args.search_dir or [])]

    built = 0
    ok = True
    for txt in sorted(input_dir.glob("*.txt")):
        try:
            out_pdf = out_dir / f"{txt.stem}.pdf"
            compile_txt(txt_path=txt, out_dir=out_dir, out_name=out_pdf.name, materia=materia, extra_search_dirs=search_dirs)
            built += 1
            if verbosity >= 2 and not args.quiet:
                console.print(f"  {console.g.dot} {txt.name} {console.g.arrow} {out_pdf.name}")
        except Exception as exc:
            ok = False
            if not args.quiet:
                console.print(console.red(f"{console.g.err} ERROR en {txt}: {exc}"))

    if not args.quiet:
        print_build_summary(console, ok=ok, built=built, out_dir=out_dir, mode=mode, show_summary=show_summary)
    raise SystemExit(0 if ok else 1)
