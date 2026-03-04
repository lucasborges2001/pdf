from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from .assets import candidate_asset_roots, find_asset
from .docheader import parse_doc_header
from .paths import find_materia_root
from ..runtime.core import DocSpec, PdfTheme
from ..runtime.framework import build_pdf
from ..format.txtfmt import txt_to_flowables


def _read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="latin-1")


def _resolver_for(*, txt_path: Path, materia: Optional[Path], extra_search_dirs: Optional[Iterable[Path]] = None) -> Tuple[Callable[[str], Path], Callable[[str], Path], List[Path]]:
    if materia is None:
        # intento liviano de inferencia; si falla, None
        try:
            materia = find_materia_root(txt_path.parent)
        except Exception:
            materia = None

    roots = candidate_asset_roots(txt_dir=txt_path.parent, materia=materia, extra=extra_search_dirs)

    def resolve_pdf(name: str) -> Path:
        p = find_asset(name, roots)
        if p is None:
            # devolver path "best effort" para que el error sea visible en el build
            return (roots[0] / name) if roots else Path(name)
        return p

    def resolve_img(name: str) -> Path:
        p = find_asset(name, roots)
        if p is None:
            return (roots[0] / name) if roots else Path(name)
        return p

    return resolve_pdf, resolve_img, roots


def _spec_from_attrs(*, out_path: Path, attrs: dict) -> DocSpec:
    # DocSpec tiene defaults; solo seteamos lo que venga
    kwargs = dict(attrs)
    kwargs.pop("out", None)

    # Asegurar tipos esperados
    if "toc_max_level" in kwargs:
        try:
            kwargs["toc_max_level"] = int(kwargs["toc_max_level"])
        except Exception:
            kwargs.pop("toc_max_level", None)

    return DocSpec(out_path=out_path, **kwargs)  # type: ignore[arg-type]


def compile_txt(
    txt_path: Path,
    *,
    out_dir: Path,
    out_name: Optional[str] = None,
    materia: Optional[Path] = None,
    theme: Optional[PdfTheme] = None,
    extra_search_dirs: Optional[Iterable[Path]] = None,
) -> Path:
    """Compila un .txt al PDF. Retorna la ruta del PDF generado."""
    txt_path = txt_path.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    text = _read_text(txt_path)
    attrs, _, rest, header_err = parse_doc_header(text)
    if header_err:
        raise RuntimeError(f"{txt_path}: {header_err}")

    out_from_header = attrs.get("out")
    final_name = out_name or (str(out_from_header) if isinstance(out_from_header, str) and out_from_header else (txt_path.stem + ".pdf"))
    out_path = out_dir / final_name

    resolve_pdf, resolve_img, _roots = _resolver_for(txt_path=txt_path, materia=materia, extra_search_dirs=extra_search_dirs)

    def build_content(ctx):
        return txt_to_flowables(
            ctx,
            rest,
            resolve_pdf=resolve_pdf,
            resolve_img=resolve_img,
            cache_dir=None,
        )

    spec = _spec_from_attrs(out_path=out_path, attrs=attrs)
    return build_pdf(spec, build_content, theme=theme)
