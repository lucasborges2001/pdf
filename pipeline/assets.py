from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional


def candidate_asset_roots(
    *,
    txt_dir: Path,
    materia: Optional[Path] = None,
    extra: Optional[Iterable[Path]] = None,
    extra_dirs: Optional[Iterable[Path]] = None,
) -> List[Path]:
    roots: List[Path] = [txt_dir]

    env = os.getenv("PDF_FIG_SEARCH_DIRS", "").strip()
    if env:
        for part in env.split(os.pathsep):
            cleaned = part.strip().strip('"').strip("'")
            if cleaned:
                roots.append(Path(cleaned).expanduser().resolve())

    for item in list(extra or []) + list(extra_dirs or []):
        roots.append(Path(item).expanduser().resolve())

    if materia is not None:
        roots.extend([materia / "Teorico", materia / "Practico", materia / "Taller", materia])

    seen = set()
    unique: List[Path] = []
    for root in roots:
        try:
            key = str(root.resolve())
        except Exception:
            key = str(root)
        if key in seen:
            continue
        seen.add(key)
        unique.append(root)
    return unique


def find_asset(name: str, roots: List[Path]) -> Optional[Path]:
    cleaned = (name or "").strip()
    if not cleaned:
        return None

    candidate = Path(cleaned)
    if candidate.is_absolute():
        return candidate if candidate.exists() else None

    for root in roots:
        path = root / cleaned
        if path.exists():
            return path
    return None
