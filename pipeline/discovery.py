from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from ..parser.header import parse_doc_header_result

DEFAULT_EXCLUDED_DIRS = {
    "resumenes",
    "output",
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    "scripts",
    "_pdf",
}

DEFAULT_TREE_SKIP_DIRS = {
    ".git",
    ".github",
    ".venv",
    "__pycache__",
    "node_modules",
    "output",
    "input",
}


@dataclass(frozen=True)
class TxtDiscovery:
    all_files: List[Path]
    candidates: List[Path]
    skipped: List[Path]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def is_candidate_txt(path: Path) -> bool:
    try:
        text = _read_text(path)
    except Exception:
        return False
    header = parse_doc_header_result(text)
    if header.has_header:
        return True
    head = text[:5000]
    for token in ("[FIG", "[IMG", ":::", "[NOTE]", "[WARN]", "[TIP]", "[PB]"):
        if token in head:
            return True
    return False


def discover_txt_inventory(base: Path, *, exclude_dirs: Optional[Iterable[str]] = None) -> TxtDiscovery:
    base = base.expanduser().resolve()
    excluded = {item.lower() for item in (exclude_dirs or [])}
    excluded |= DEFAULT_EXCLUDED_DIRS

    all_files: List[Path] = []
    for path in base.rglob("*.txt"):
        rel_parts = path.relative_to(base).parts
        if any(part.lower() in excluded for part in rel_parts[:-1]):
            continue
        if path.name.startswith("."):
            continue
        all_files.append(path)

    all_files = sorted(all_files)
    candidates = [path for path in all_files if is_candidate_txt(path)]
    candidate_set = set(candidates)
    skipped = [path for path in all_files if path not in candidate_set]
    return TxtDiscovery(all_files=all_files, candidates=candidates, skipped=sorted(skipped))


def discover_txts(base: Path, *, exclude_dirs: Optional[Iterable[str]] = None) -> List[Path]:
    return discover_txt_inventory(base, exclude_dirs=exclude_dirs).candidates


def discover_tree_txts(
    root: Path,
    *,
    only_names: Optional[Sequence[str]] = None,
    skip_dir_names: Optional[Iterable[str]] = None,
) -> List[Path]:
    root = root.expanduser().resolve()
    skip_dirs = {name.lower() for name in (skip_dir_names or DEFAULT_TREE_SKIP_DIRS)}
    only_set = {name.lower() for name in only_names} if only_names else None

    found: List[Path] = []
    for path in sorted(root.rglob("*.txt")):
        rel_parents = path.relative_to(root).parents
        if any(parent.name.lower() in skip_dirs for parent in rel_parents if str(parent) != "."):
            continue
        if only_set and path.parent.name.lower() not in only_set and path.stem.lower() not in only_set:
            continue
        found.append(path)
    return found
