from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence

from .console import Console
from .fmt import trunc

def print_help(c: Console) -> None:
    c.rule("_pdf — comandos")
    c.print("")
    c.print(c.bold("BUILD (input → output)"))
    c.print(f"  python -m _pdf.build {c.gray('[--clean] [--check] [--strict] [--search-dir DIR...]')}")
    c.print("")
    c.print(c.bold("BUILD MATERIA (materia → Resumenes)"))
    c.print(f"  python -m _pdf.build_materia --materia MATERIA {c.gray('[--area practico|taller|both] [--only 00 01 ...] [--check] [--strict]')}")
    c.print("")
    c.print(c.bold("SCAN / LINT (sin generar PDF)"))
    c.print(f"  python -m _pdf.scan --materia MATERIA {c.gray('[--strict] [--show-skipped]')}")
    c.print(f"  python -m _pdf.scan --input")
    c.print("")
    c.print(c.bold("FLAGS comunes"))
    rows = [
        ("--quiet", "Silencia si está OK; si hay errores, imprime mínimo"),
        ("--only-summary", "Solo resumen (sin detalle)"),
        ("--no-summary", "Sin resumen (solo detalle)"),
        ("-v, -vv", "Más detalle"),
        ("--no-color", "Sin ANSI"),
        ("--ascii", "Sin símbolos unicode"),
        ("--max-issues N", "Límite de issues impresos"),
        ("--show-skipped", "Lista .txt ignorados por heurística"),
        ("--max-skipped N", "Límite de skipped impresos"),
        ("--log FILE", "Guarda la salida en un archivo (además de stdout)"),
        ("--log-json FILE", "Guarda reporte JSON (scan/check)"),
    ]
    c.table(("Flag", "Descripción"), rows, indent=2)
    c.print("")
    c.print(c.gray("Tip: --check valida formato y assets sin generar PDFs."))

def _severity_badge(c: Console, sev: str) -> str:
    if sev == "ERROR":
        return c.red(c.g.err + " ERROR")
    if sev == "WARN":
        return c.yellow(c.g.warn + " WARN")
    return sev

def print_scan_report(
    c: Console,
    report: Any,
    *,
    mode: str = "normal",  # normal | only_summary | quiet
    show_summary: bool = True,
    verbosity: int = 1,
    max_issues: int = 30,
    show_skipped: bool = False,
    max_skipped: int = 30,
    title: str = "SCAN",
) -> None:
    """Imprime un ScanReport (engine.scanlib.ScanReport) en formato legible."""

    # Stats (compat con ScanReport actual)
    txt_total = int(getattr(report, "txt_total", 0) or 0)
    candidates = int(getattr(report, "txt_candidates", 0) or 0)
    skipped_list = getattr(report, "skipped_files", None) or []
    skipped = len(skipped_list)
    scanned_files = getattr(report, "scanned_files", None) or []
    linted = len(scanned_files)
    errors = int(getattr(report, "errors", 0) or 0)
    warns = int(getattr(report, "warns", 0) or 0)

    if mode == "quiet":
        # Si está OK, no imprimir nada. Si hay problemas, imprimir mínimo.
        if errors == 0 and warns == 0:
            return
        badge = c.red(c.g.err + " ERROR") if errors else c.yellow(c.g.warn + " WARN")
        c.print(f"{badge}  errors={errors} warns={warns}  candidatos={candidates} skipped={skipped}")
        return

    c.rule(title)

    if show_summary:
        c.kv(
            [
                ("txt_total", txt_total),
                ("candidatos", candidates),
                ("skipped", skipped),
                ("linted", linted),
                ("errors", errors),
                ("warns", warns),
            ],
            indent=2,
        )
        c.print("")

    # only_summary: nada de tablas ni detalle
    if mode == "only_summary":
        return

    if verbosity <= 0:
        return

    # Per-file summary
    if scanned_files:
        rows = []
        for r in scanned_files:
            path = getattr(r, "path", None)
            issues = getattr(r, "issues", []) or []
            errc = sum(1 for i in issues if getattr(i, "severity", "") == "ERROR")
            warnc = sum(1 for i in issues if getattr(i, "severity", "") == "WARN")
            status_s = c.green(c.g.ok + " OK") if errc == 0 else c.red(c.g.err + " ERROR")
            rows.append((trunc(str(path), 70), status_s, warnc))
        c.table(("Archivo", "Estado", "Warns"), rows, indent=2)
        c.print("")

    # Issues detail
    printed = 0
    for r in scanned_files:
        issues = getattr(r, "issues", []) or []
        if not issues:
            continue
        c.print(c.bold(f"{c.g.dot} {getattr(r, 'path', '')}"))
        for it in issues:
            if printed >= max_issues:
                break
            sev = getattr(it, "severity", "")
            line = getattr(it, "line", 0)
            msg = getattr(it, "msg", "")
            c.print(f"    {_severity_badge(c, sev)} {c.gray('L'+str(line))}  {msg}")
            printed += 1
        c.print("")
        if printed >= max_issues:
            break

    if printed >= max_issues:
        c.print(c.gray(f"(se alcanzó --max-issues={max_issues})"))
        c.print("")

    if show_skipped and skipped_list:
        c.print(c.bold("Skipped (.txt ignorados por heurística)"))
        for p in skipped_list[:max_skipped]:
            c.print(f"  {c.g.dot} {p}")
        if len(skipped_list) > max_skipped:
            c.print(c.gray(f"(se alcanzó --max-skipped={max_skipped}, total skipped={len(skipped_list)})"))
        c.print("")

def print_build_summary(c: Console, *, ok: bool, built: int, out_dir: Path, mode: str = "normal", show_summary: bool = True) -> None:
    if mode == "quiet" and ok:
        return
    if not show_summary:
        return
    badge = c.green(c.g.ok + " OK") if ok else c.red(c.g.err + " ERROR")
    c.rule("RESULTADO")
    c.print(f"  {badge}  PDFs generados: {built}")
    c.print(f"  {c.gray('output')} {c.g.arrow} {out_dir}")