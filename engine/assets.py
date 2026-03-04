from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

def candidate_asset_roots(*, txt_dir: Path, materia: Optional[Path] = None, extra: Optional[Iterable[Path]] = None) -> List[Path]:
    roots: List[Path] = [txt_dir]

    env = os.getenv("PDF_FIG_SEARCH_DIRS", "").strip()
    if env:
        for part in env.split(os.pathsep):
            p = part.strip().strip('"').strip("'")
            if p:
                roots.append(Path(p).expanduser().resolve())

    if extra:
        for p in extra:
            roots.append(Path(p).expanduser().resolve())

    if materia:
        roots.extend([
            materia / "Teorico",
            materia / "Practico",
            materia / "Taller",
            materia,
        ])

    # dedup
    seen = set()
    uniq: List[Path] = []
    for r in roots:
        try:
            key = str(r.resolve())
        except Exception:
            key = str(r)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    return uniq

def find_asset(name: str, roots: List[Path]) -> Optional[Path]:
    name = (name or "").strip()
    if not name:
        return None

    p = Path(name)
    if p.is_absolute():
        return p if p.exists() else None

    for r in roots:
        cand = r / name
        if cand.exists():
            return cand
    return None
