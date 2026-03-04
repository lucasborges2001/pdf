# _pdf/paths.py
from __future__ import annotations

import os
from pathlib import Path

_MATERIA_MARKERS = ("Practico", "Teorico", "Taller")


def pdf_pkg_dir() -> Path:
    # .../<repo>/_pdf  (este paquete)
    return Path(__file__).resolve().parent


def scripts_dir() -> Path:
    # Si el paquete vive en: <Materia>/Scripts/_pdf  -> devuelve <Materia>/Scripts
    # Si el paquete vive en: D:/Scripts/_pdf         -> devuelve D:/Scripts
    return pdf_pkg_dir().parent


def _looks_like_materia_root(p: Path) -> bool:
    if not p or not p.is_dir():
        return False
    return any((p / name).is_dir() for name in _MATERIA_MARKERS)


def find_materia_root(start: Path | None = None) -> Path:
    """Encuentra la carpeta raíz de una Materia.

    Estructura esperada:
      <Materia>/
        Practico/
        Teorico/
        Taller/
        (opcional) Resumenes/

    Resolución (prioridad):
      1) env: PDF_MATERIA_ROOT
      2) 'start' (si se pasa) y sus padres
      3) CWD y sus padres
      4) layout legacy: <Materia>/Scripts/_pdf  (usa la ubicación del paquete)

    Si no la puede inferir, levanta FileNotFoundError.
    """
    env = os.environ.get("PDF_MATERIA_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if _looks_like_materia_root(p):
            return p

    base = (start or Path.cwd()).resolve()
    if base.is_file():
        base = base.parent

    # Si te pasan directamente Practico/Teorico/Taller, subimos 1 nivel
    if base.name in _MATERIA_MARKERS and _looks_like_materia_root(base.parent):
        return base.parent

    for cand in (base, *base.parents):
        if _looks_like_materia_root(cand):
            return cand

    legacy = scripts_dir().parent
    if _looks_like_materia_root(legacy):
        return legacy

    raise FileNotFoundError(
        "No pude inferir <Materia>. Pasá la ruta explícita (ej: --materia D:\\ArqComp) "
        "o definí PDF_MATERIA_ROOT."
    )


def materia_root() -> Path:
    # Compat: antes asumíamos <Materia>/Scripts/_pdf. Ahora inferimos por marcadores.
    return find_materia_root()


def practico_dir(materia: Path | None = None) -> Path:
    m = (materia or materia_root()).resolve()
    return m / "Practico"


def taller_dir(materia: Path | None = None) -> Path:
    m = (materia or materia_root()).resolve()
    return m / "Taller"


def output_root(materia: Path | None = None) -> Path:
    m = (materia or materia_root()).resolve()
    return m / "Resumenes"
