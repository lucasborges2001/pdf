from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

from .assets import candidate_asset_roots, find_asset
from .docheader import parse_doc_header
from ..format import txtfmt


@dataclass
class Issue:
    severity: str  # ERROR | WARN
    file: Path
    line: int
    msg: str

    def fmt(self) -> str:
        return f"[{self.severity}] {self.file}:{self.line}  {self.msg}"


@dataclass
class ScanFileResult:
    path: Path
    issues: List[Issue]

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "ERROR")

    @property
    def warn_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "WARN")


@dataclass
class ScanReport:
    # Archivos que se consideraron "candidatos" y se lint-earon.
    scanned_files: List[ScanFileResult]

    # Metadatos del descubrimiento (útil para mostrar "totales vs candidatos").
    txt_total: int = 0
    txt_candidates: int = 0

    # .txt encontrados pero descartados por heurística (_is_candidate_txt).
    skipped_files: List[Path] = None

    @property
    def files(self) -> int:
        return len(self.scanned_files)

    @property
    def errors(self) -> int:
        return sum(r.error_count for r in self.scanned_files)

    @property
    def warns(self) -> int:
        return sum(r.warn_count for r in self.scanned_files)



def report_to_dict(report: ScanReport) -> dict:
    """Serializa ScanReport a dict JSON-friendly (paths -> str)."""
    return {
        "txt_total": report.txt_total,
        "txt_candidates": report.txt_candidates,
        "skipped_files": [str(p) for p in (report.skipped_files or [])],
        "scanned_files": [
            {
                "path": str(r.path),
                "errors": r.error_count,
                "warns": r.warn_count,
                "issues": [
                    {
                        "severity": it.severity,
                        "file": str(it.file),
                        "line": it.line,
                        "msg": it.msg,
                    }
                    for it in r.issues
                ],
            }
            for r in report.scanned_files
        ],
        "summary": {
            "files": report.files,
            "errors": report.errors,
            "warns": report.warns,
            "skipped": len(report.skipped_files or []),
        },
    }


def format_report(report: ScanReport, *, max_issues: int = 40, show_skipped: bool = False, max_skipped: int = 30) -> str:
    """Devuelve un texto con issues agrupados por archivo + resumen final."""
    lines: List[str] = []
    printed = 0
    for r in report.scanned_files:
        status = "OK" if r.error_count == 0 else "ERROR"
        lines.append(f"- {r.path}: {status}  (warn={r.warn_count})")
        for it in r.issues:
            if printed >= max_issues:
                continue
            lines.append("    " + it.fmt())
            printed += 1

    skipped = report.skipped_files or []
    lines.append("")
    lines.append(
        f"Resumen: txt_total={report.txt_total}  candidatos={report.txt_candidates}  skipped={len(skipped)}  linted={report.files}  errors={report.errors}  warns={report.warns}"
    )

    if show_skipped and skipped:
        lines.append("")
        lines.append(f"Skipped (por heurística): showing {min(len(skipped), max_skipped)} of {len(skipped)}")
        for p in skipped[:max_skipped]:
            lines.append(f"  - {p}")
        if len(skipped) > max_skipped:
            lines.append("  ...")

    return "\n".join(lines)


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1")


def lint_txt(*, txt_path: Path, materia: Optional[Path] = None, extra_search_dirs: Optional[Iterable[Path]] = None) -> List[Issue]:
    """Lint rápido del formato. No genera PDF."""
    issues: List[Issue] = []
    text = _read_text(txt_path)

    attrs, unknown_keys, rest, header_err = parse_doc_header(text)
    if header_err:
        issues.append(Issue("ERROR", txt_path, 1, header_err))
    elif unknown_keys:
        issues.append(Issue("WARN", txt_path, 1, "Header [DOC] contiene claves desconocidas: " + ", ".join(unknown_keys)))

    roots = candidate_asset_roots(txt_dir=txt_path.parent, materia=materia, extra=extra_search_dirs)

    # Regex del parser (misma semántica que el build)
    FIG_RE = getattr(txtfmt, "_FIG_RE")
    IMG_RE = getattr(txtfmt, "_IMG_RE")
    PB_RE = getattr(txtfmt, "_PB_RE")
    CALLOUT_OPEN_RE = getattr(txtfmt, "_CALLOUT_OPEN_RE")
    CALLOUT_CLOSE_RE = getattr(txtfmt, "_CALLOUT_CLOSE_RE")
    BLOCK_OPEN_RE = getattr(txtfmt, "_BLOCK_OPEN_RE")
    BLOCK_CLOSE_RE = getattr(txtfmt, "_BLOCK_CLOSE_RE")
    FENCE_OPEN_RE = getattr(txtfmt, "_FENCE_OPEN_RE")
    FENCE_CLOSE_RE = getattr(txtfmt, "_FENCE_CLOSE_RE")

    in_fence = False
    fence_open_line: Optional[int] = None
    block_stack: List[Tuple[str, int]] = []
    callout_stack: List[Tuple[str, int]] = []

    lines = rest.splitlines()
    for i, raw in enumerate(lines, start=1):
        s = raw.strip()

        if FENCE_OPEN_RE.match(s):
            in_fence = True
            fence_open_line = i
            continue
        if FENCE_CLOSE_RE.match(s):
            if not in_fence:
                issues.append(Issue("ERROR", txt_path, i, "Cierre de ``` sin apertura previa."))
            in_fence = False
            fence_open_line = None
            continue
        if in_fence:
            continue

        m_open = CALLOUT_OPEN_RE.match(s)
        if m_open:
            kind = m_open.group("kind")
            callout_stack.append((kind, i))
            continue

        m_close = CALLOUT_CLOSE_RE.match(s)
        if m_close:
            kind = m_close.group("kind")
            if not callout_stack:
                issues.append(Issue("ERROR", txt_path, i, f"Cierre [/{kind}] sin apertura."))
            else:
                top_kind, top_line = callout_stack[-1]
                if top_kind != kind:
                    issues.append(Issue("ERROR", txt_path, i, f"Cierre [/{kind}] no matchea apertura [{top_kind}] (línea {top_line})."))
                else:
                    callout_stack.pop()
            continue

        if BLOCK_CLOSE_RE.match(s):
            if not block_stack:
                issues.append(Issue("ERROR", txt_path, i, "Cierre ::: sin apertura previa."))
            else:
                block_stack.pop()
            continue

        m_block = BLOCK_OPEN_RE.match(s)
        if m_block:
            kind = m_block.group("kind") or ""
            block_stack.append((kind, i))
            continue

        if s.startswith("[FIG"):
            m = FIG_RE.match(s)
            if not m:
                issues.append(Issue("ERROR", txt_path, i, "Marcador [FIG] inválido."))
            else:
                fn = m.group("file")
                page = int(m.group("page"))
                zoom = float(m.group("zoom") or "2.0")
                if page < 1:
                    issues.append(Issue("ERROR", txt_path, i, f"[FIG] page debe ser >= 1 (1-based). Vino: {page}"))
                if zoom <= 0:
                    issues.append(Issue("ERROR", txt_path, i, f"[FIG] zoom debe ser > 0. Vino: {zoom}"))
                if find_asset(fn, roots) is None:
                    issues.append(Issue("WARN", txt_path, i, f"[FIG] no encontré '{fn}' en: " + ", ".join(str(r) for r in roots)))
            continue

        if s.startswith("[IMG"):
            m = IMG_RE.match(s)
            if not m:
                issues.append(Issue("ERROR", txt_path, i, "Marcador [IMG] inválido."))
            else:
                fn = m.group("file")
                if find_asset(fn, roots) is None:
                    issues.append(Issue("WARN", txt_path, i, f"[IMG] no encontré '{fn}' en: " + ", ".join(str(r) for r in roots)))
            continue

        if PB_RE.match(s):
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


def discover_txts(base: Path, *, exclude_dirs: Optional[Iterable[str]] = None) -> List[Path]:
    exclude = set(exclude_dirs or [])
    exclude |= {"Resumenes", "output", "__pycache__", ".git", ".venv", "venv", ".mypy_cache", ".pytest_cache"}

    out: List[Path] = []
    for p in base.rglob("*.txt"):
        if any(part in exclude for part in p.parts):
            continue
        if p.name.startswith("."):
            continue
        out.append(p)
    return sorted(out)


def _is_candidate_txt(p: Path) -> bool:
    try:
        text = _read_text(p)
    except Exception:
        return False
    attrs, _, _, _ = parse_doc_header(text)
    if attrs:
        return True
    head = text[:5000]
    for tok in ("[FIG", "[IMG", ":::", "[NOTE]", "[WARN]", "[TIP]", "[PB]"):
        if tok in head:
            return True
    return False


def scan_files(files: List[Path], *, materia: Optional[Path] = None, extra_search_dirs: Optional[Iterable[Path]] = None) -> ScanReport:
    # Primero medimos totales vs candidatos, para reporting.
    total = len(files)
    candidates: List[Path] = [f for f in files if _is_candidate_txt(f)]
    skipped: List[Path] = [f for f in files if f not in set(candidates)]

    results: List[ScanFileResult] = []
    for f in candidates:
        issues = lint_txt(txt_path=f, materia=materia, extra_search_dirs=extra_search_dirs)
        results.append(ScanFileResult(f, issues))

    return ScanReport(results, txt_total=total, txt_candidates=len(candidates), skipped_files=sorted(skipped))
def scan_input(pkg_root: Path, *, extra_search_dirs: Optional[Iterable[Path]] = None) -> ScanReport:
    input_dir = pkg_root / "input"
    files = sorted(input_dir.glob("*.txt"))
    return scan_files(files, materia=None, extra_search_dirs=extra_search_dirs)


def scan_materia(materia: Path, *, extra_search_dirs: Optional[Iterable[Path]] = None) -> ScanReport:
    files = discover_txts(materia)
    return scan_files(files, materia=materia, extra_search_dirs=extra_search_dirs)
