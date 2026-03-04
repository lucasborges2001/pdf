from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence

from .scanlib import discover_txts
from .docheader import parse_doc_header


@dataclass(frozen=True)
class BuildJob:
    txt_path: Path
    area: str  # "Practico" | "Taller" | "Teorico" | "Other"
    out_dir: Path
    out_name: str  # pdf filename


def _classify_area(p: Path) -> str:
    parts = set(p.parts)
    if "Practico" in parts:
        return "Practico"
    if "Taller" in parts:
        return "Taller"
    if "Teorico" in parts:
        return "Teorico"
    return "Other"


def _default_out_name(txt_path: Path) -> str:
    # si la convención es <Carpeta>/<Carpeta>.txt, usar carpeta.pdf
    parent = txt_path.parent.name
    stem = txt_path.stem
    if stem.lower() == parent.lower():
        return f"{parent}.pdf"
    return f"{stem}.pdf"


def discover_jobs(
    materia: Path,
    *,
    area: str = "both",   # practico | taller | both
    only_prefixes: Optional[Sequence[str]] = None,
    dest_root_name: str = "Resumenes",
) -> List[BuildJob]:
    materia = materia.expanduser().resolve()
    dest_root = materia / dest_root_name
    dest_root.mkdir(parents=True, exist_ok=True)

    files = discover_txts(materia)

    jobs: List[BuildJob] = []
    for f in files:
        a = _classify_area(f)
        if area == "practico" and a != "Practico":
            continue
        if area == "taller" and a != "Taller":
            continue
        if area == "both" and a not in {"Practico", "Taller"}:
            continue

        if only_prefixes:
            # mantener compatibilidad con 00/01/etc: si alguna parte del path arranca con prefijo
            if not any(part.startswith(pref) for pref in only_prefixes for part in f.parts):
                continue

        text = f.read_text(encoding="utf-8", errors="ignore")
        attrs, _, _, _ = parse_doc_header(text)
        out = attrs.get("out")
        out_name = str(out) if isinstance(out, str) and out else _default_out_name(f)

        out_dir = dest_root / a if a in {"Practico", "Taller"} else dest_root
        out_dir.mkdir(parents=True, exist_ok=True)

        jobs.append(BuildJob(txt_path=f, area=a, out_dir=out_dir, out_name=out_name))

    return sorted(jobs, key=lambda j: str(j.txt_path))
