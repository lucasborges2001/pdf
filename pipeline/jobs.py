from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Sequence

from ..parser.header import parse_doc_header_result
from .discovery import discover_txts
from .models import BuildJob


def _classify_area(path: Path) -> str:
    parts = set(path.parts)
    if "Practico" in parts:
        return "Practico"
    if "Taller" in parts:
        return "Taller"
    if "Teorico" in parts:
        return "Teorico"
    return "Other"


def _default_out_name(txt_path: Path) -> str:
    if txt_path.stem.lower() == txt_path.parent.name.lower():
        return f"{txt_path.parent.name}.pdf"
    return f"{txt_path.stem}.pdf"


def discover_jobs(
    materia: Path,
    *,
    area: str = "all",
    only_prefixes: Optional[Sequence[str]] = None,
    dest_root_name: str = "Resumenes",
) -> List[BuildJob]:
    materia = materia.expanduser().resolve()
    dest_root = materia / dest_root_name
    dest_root.mkdir(parents=True, exist_ok=True)

    jobs: List[BuildJob] = []
    for path in discover_txts(materia):
        classified = _classify_area(path)
        if area == "practico" and classified != "Practico":
            continue
        if area == "taller" and classified != "Taller":
            continue
        if area == "teorico" and classified != "Teorico":
            continue
        if area == "both" and classified not in {"Practico", "Taller"}:
            continue

        if only_prefixes and not any(part.startswith(prefix) for prefix in only_prefixes for part in path.parts):
            continue

        header = parse_doc_header_result(path.read_text(encoding="utf-8", errors="ignore"))
        out_from_header = header.attrs.get("out")
        out_name = str(out_from_header) if isinstance(out_from_header, str) and out_from_header else _default_out_name(path)

        resumenes_dir = dest_root / classified if classified in {"Practico", "Taller", "Teorico"} else dest_root
        resumenes_dir.mkdir(parents=True, exist_ok=True)
        out_dirs = tuple(dict.fromkeys((resumenes_dir, path.parent)))
        jobs.append(BuildJob(txt_path=path, area=classified, out_dirs=out_dirs, out_name=out_name))

    return sorted(jobs, key=lambda job: str(job.txt_path))
