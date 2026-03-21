from __future__ import annotations

from pathlib import Path
from typing import Any

from .console import Console
from .fmt import trunc


def print_help(c: Console) -> None:
    c.rule("_pdf - comandos")
    c.print("")
    c.print(c.bold("BUILD (input -> output)"))
    c.print(f"  python -m _pdf.build {c.gray('[--clean] [--check] [--strict] [--search-dir DIR...]')}")
    c.print("")
    c.print(c.bold("BUILD MATERIA (materia -> Resumenes)"))
    c.print(f"  python -m _pdf.build_materia --materia MATERIA {c.gray('[--area teorico|practico|taller|both|all] [--only 00 01 ...] [--check] [--strict]')}")
    c.print("")
    c.print(c.bold("BUILD CARPETA (arbol recursivo)"))
    c.print(f"  python -m _pdf.build_carpeta --carpeta CARPETA {c.gray('[--only nombre...] [--check] [--strict]')}")
    c.print("")
    c.print(c.bold("SCAN / LINT (sin generar PDF)"))
    c.print(f"  python -m _pdf.scan --materia MATERIA {c.gray('[--strict] [--show-skipped]')}")
    c.print("  python -m _pdf.scan --input")
    c.print("")
    c.print(c.bold("FLAGS comunes"))
    rows = [
        ("--quiet", "Silencia si esta OK; si hay errores, imprime minimo"),
        ("--only-summary", "Solo resumen (sin detalle)"),
        ("--no-summary", "Sin resumen (solo detalle)"),
        ("-v, -vv", "Mas detalle"),
        ("--no-color", "Sin ANSI"),
        ("--ascii", "Sin simbolos unicode"),
        ("--max-issues N", "Limite de issues impresos"),
        ("--show-skipped", "Lista .txt ignorados por heuristica"),
        ("--max-skipped N", "Limite de skipped impresos"),
        ("--log FILE", "Guarda la salida en un archivo (ademas de stdout)"),
        ("--log-json FILE", "Guarda reporte JSON (scan/check)"),
    ]
    c.table(("Flag", "Descripcion"), rows, indent=2)
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
    mode: str = "normal",
    show_summary: bool = True,
    verbosity: int = 1,
    max_issues: int = 30,
    show_skipped: bool = False,
    max_skipped: int = 30,
    title: str = "SCAN",
) -> None:
    txt_total = int(getattr(report, "txt_total", 0) or 0)
    candidates = int(getattr(report, "txt_candidates", 0) or 0)
    skipped_list = getattr(report, "skipped_files", None) or []
    skipped = len(skipped_list)
    scanned_files = getattr(report, "scanned_files", None) or []
    linted = len(scanned_files)
    errors = int(getattr(report, "errors", 0) or 0)
    warns = int(getattr(report, "warns", 0) or 0)

    if mode == "quiet":
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

    if mode == "only_summary" or verbosity <= 0:
        return

    if scanned_files:
        rows = []
        for result in scanned_files:
            path = getattr(result, "path", None)
            issues = getattr(result, "issues", []) or []
            errc = sum(1 for issue in issues if getattr(issue, "severity", "") == "ERROR")
            warnc = sum(1 for issue in issues if getattr(issue, "severity", "") == "WARN")
            status = c.green(c.g.ok + " OK") if errc == 0 else c.red(c.g.err + " ERROR")
            rows.append((trunc(str(path), 70), status, warnc))
        c.table(("Archivo", "Estado", "Warns"), rows, indent=2)
        c.print("")

    printed = 0
    for result in scanned_files:
        issues = getattr(result, "issues", []) or []
        if not issues:
            continue
        c.print(c.bold(f"{c.g.dot} {getattr(result, 'path', '')}"))
        for issue in issues:
            if printed >= max_issues:
                break
            sev = getattr(issue, "severity", "")
            line = getattr(issue, "line", 0)
            msg = getattr(issue, "msg", "")
            c.print(f"    {_severity_badge(c, sev)} {c.gray('L'+str(line))}  {msg}")
            printed += 1
        c.print("")
        if printed >= max_issues:
            break

    if printed >= max_issues:
        c.print(c.gray(f"(se alcanzo --max-issues={max_issues})"))
        c.print("")

    if show_skipped and skipped_list:
        c.print(c.bold("Skipped (.txt ignorados por heuristica)"))
        for path in skipped_list[:max_skipped]:
            c.print(f"  {c.g.dot} {path}")
        if len(skipped_list) > max_skipped:
            c.print(c.gray(f"(se alcanzo --max-skipped={max_skipped}, total skipped={len(skipped_list)})"))
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
