from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from ..parser.header import parse_doc_header_result
from ..parser.syntax import (
    BLOCK_CLOSE_RE,
    BLOCK_OPEN_RE,
    CALLOUT_CLOSE_RE,
    CALLOUT_OPEN_RE,
    FENCE_CLOSE_RE,
    FENCE_OPEN_RE,
    FIG_RE,
    IMG_RE,
    PB_RE,
)
from .assets import candidate_asset_roots, find_asset
from .discovery import discover_txt_inventory
from .models import Issue, ScanFileResult, ScanReport


def report_to_dict(report: ScanReport) -> dict:
    return {
        "txt_total": report.txt_total,
        "txt_candidates": report.txt_candidates,
        "skipped_files": [str(path) for path in report.skipped_files],
        "scanned_files": [
            {
                "path": str(result.path),
                "errors": result.error_count,
                "warns": result.warn_count,
                "issues": [
                    {
                        "severity": issue.severity,
                        "file": str(issue.file),
                        "line": issue.line,
                        "msg": issue.msg,
                    }
                    for issue in result.issues
                ],
            }
            for result in report.scanned_files
        ],
        "summary": {
            "files": report.files,
            "errors": report.errors,
            "warns": report.warns,
            "skipped": len(report.skipped_files),
        },
    }


def format_report(report: ScanReport, *, max_issues: int = 40, show_skipped: bool = False, max_skipped: int = 30) -> str:
    lines: List[str] = []
    printed = 0
    for result in report.scanned_files:
        status = "OK" if result.error_count == 0 else "ERROR"
        lines.append(f"- {result.path}: {status}  (warn={result.warn_count})")
        for issue in result.issues:
            if printed >= max_issues:
                continue
            lines.append("    " + issue.fmt())
            printed += 1

    lines.append("")
    lines.append(
        "Resumen: "
        f"txt_total={report.txt_total}  candidatos={report.txt_candidates}  skipped={len(report.skipped_files)}  "
        f"linted={report.files}  errors={report.errors}  warns={report.warns}"
    )

    if show_skipped and report.skipped_files:
        lines.append("")
        lines.append(
            f"Skipped (por heurística): showing {min(len(report.skipped_files), max_skipped)} of {len(report.skipped_files)}"
        )
        for path in report.skipped_files[:max_skipped]:
            lines.append(f"  - {path}")
        if len(report.skipped_files) > max_skipped:
            lines.append("  ...")

    return "\n".join(lines)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _header_issues(txt_path: Path, text: str) -> Tuple[object, List[Issue]]:
    header = parse_doc_header_result(text)
    issues: List[Issue] = []
    if header.error:
        issues.append(Issue("ERROR", txt_path, header.line_number or 1, header.error))
    elif not header.has_header:
        issues.append(Issue("ERROR", txt_path, 1, "Falta header [DOC ...] en la primera línea no vacía."))
    elif "title" not in header.attrs or not str(header.attrs["title"]).strip():
        issues.append(Issue("ERROR", txt_path, header.line_number or 1, "Header [DOC] debe incluir title."))

    if header.unknown_keys:
        issues.append(
            Issue(
                "WARN",
                txt_path,
                header.line_number or 1,
                "Header [DOC] contiene claves desconocidas: " + ", ".join(header.unknown_keys),
            )
        )
    return header, issues


def lint_txt(*, txt_path: Path, materia: Optional[Path] = None, extra_search_dirs: Optional[Iterable[Path]] = None) -> List[Issue]:
    issues: List[Issue] = []
    text = _read_text(txt_path)
    header, header_issues = _header_issues(txt_path, text)
    issues.extend(header_issues)

    body = getattr(header, "body", text)
    roots = candidate_asset_roots(txt_dir=txt_path.parent, materia=materia, extra=extra_search_dirs)

    in_fence = False
    fence_open_line: Optional[int] = None
    block_stack: List[Tuple[str, int]] = []
    callout_stack: List[Tuple[str, int]] = []

    lines = body.splitlines()
    for line_no, raw in enumerate(lines, start=1):
        stripped = raw.strip()

        if in_fence and FENCE_CLOSE_RE.match(stripped):
            in_fence = False
            fence_open_line = None
            continue
        if (not in_fence) and FENCE_CLOSE_RE.match(stripped):
            issues.append(Issue("ERROR", txt_path, line_no, "Cierre de ``` sin apertura previa."))
            continue
        if (not in_fence) and FENCE_OPEN_RE.match(stripped):
            in_fence = True
            fence_open_line = line_no
            continue
        if in_fence:
            continue

        callout_open = CALLOUT_OPEN_RE.match(stripped)
        if callout_open:
            callout_stack.append((callout_open.group("kind"), line_no))
            continue

        callout_close = CALLOUT_CLOSE_RE.match(stripped)
        if callout_close:
            kind = callout_close.group("kind")
            if not callout_stack:
                issues.append(Issue("ERROR", txt_path, line_no, f"Cierre [/{kind}] sin apertura."))
            else:
                top_kind, top_line = callout_stack[-1]
                if top_kind != kind:
                    issues.append(
                        Issue(
                            "ERROR",
                            txt_path,
                            line_no,
                            f"Cierre [/{kind}] no matchea apertura [{top_kind}] (línea {top_line}).",
                        )
                    )
                else:
                    callout_stack.pop()
            continue

        if BLOCK_CLOSE_RE.match(stripped):
            if not block_stack:
                issues.append(Issue("ERROR", txt_path, line_no, "Cierre ::: sin apertura previa."))
            else:
                block_stack.pop()
            continue

        block_open = BLOCK_OPEN_RE.match(stripped)
        if block_open:
            block_stack.append((block_open.group("kind") or "", line_no))
            continue

        if stripped.startswith("[FIG"):
            match = FIG_RE.match(stripped)
            if not match:
                issues.append(Issue("ERROR", txt_path, line_no, "Marcador [FIG] inválido."))
            else:
                filename = match.group("file")
                page = int(match.group("page"))
                zoom = float(match.group("zoom") or "2.0")
                if page < 1:
                    issues.append(Issue("ERROR", txt_path, line_no, f"[FIG] page debe ser >= 1. Vino: {page}"))
                if zoom <= 0:
                    issues.append(Issue("ERROR", txt_path, line_no, f"[FIG] zoom debe ser > 0. Vino: {zoom}"))
                if find_asset(filename, roots) is None:
                    issues.append(
                        Issue(
                            "WARN",
                            txt_path,
                            line_no,
                            f"[FIG] no encontré '{filename}' en: " + ", ".join(str(root) for root in roots),
                        )
                    )
            continue

        if stripped.startswith("[IMG"):
            match = IMG_RE.match(stripped)
            if not match:
                issues.append(Issue("ERROR", txt_path, line_no, "Marcador [IMG] inválido."))
            else:
                filename = match.group("file")
                if find_asset(filename, roots) is None:
                    issues.append(
                        Issue(
                            "WARN",
                            txt_path,
                            line_no,
                            f"[IMG] no encontré '{filename}' en: " + ", ".join(str(root) for root in roots),
                        )
                    )
            continue

        if PB_RE.match(stripped):
            continue

    if in_fence and fence_open_line is not None:
        issues.append(Issue("ERROR", txt_path, fence_open_line, "Bloque ``` abierto y no cerrado."))
    if block_stack:
        kind, line_open = block_stack[-1]
        issues.append(Issue("ERROR", txt_path, line_open, f"Bloque :::'{kind}' abierto y no cerrado con :::"))
    if callout_stack:
        kind, line_open = callout_stack[-1]
        issues.append(Issue("ERROR", txt_path, line_open, f"Callout [{kind}] abierto y no cerrado con [/{kind}]"))

    return issues


def scan_files(files: List[Path], *, materia: Optional[Path] = None, extra_search_dirs: Optional[Iterable[Path]] = None) -> ScanReport:
    results = [
        ScanFileResult(path=path, issues=lint_txt(txt_path=path, materia=materia, extra_search_dirs=extra_search_dirs))
        for path in files
    ]
    return ScanReport(scanned_files=results, txt_total=len(files), txt_candidates=len(files), skipped_files=[])


def scan_input(pkg_root: Path, *, extra_search_dirs: Optional[Iterable[Path]] = None) -> ScanReport:
    files = sorted((pkg_root / "input").glob("*.txt"))
    return scan_files(files, materia=None, extra_search_dirs=extra_search_dirs)


def scan_materia(materia: Path, *, extra_search_dirs: Optional[Iterable[Path]] = None) -> ScanReport:
    discovery = discover_txt_inventory(materia)
    results = [
        ScanFileResult(path=path, issues=lint_txt(txt_path=path, materia=materia, extra_search_dirs=extra_search_dirs))
        for path in discovery.candidates
    ]
    return ScanReport(
        scanned_files=results,
        txt_total=len(discovery.all_files),
        txt_candidates=len(discovery.candidates),
        skipped_files=discovery.skipped,
    )
