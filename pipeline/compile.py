from __future__ import annotations

from dataclasses import fields
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Sequence, Tuple

from ..engine.paths import find_materia_root
from ..parser.header import ALLOWED_DOC_KEYS, DocHeaderParseResult, parse_doc_header_result
from ..runtime.models import DocSpec, PdfTheme
from .assets import candidate_asset_roots, find_asset
from .errors import PdfBuildError

DOCSPEC_FIELDS = {field.name for field in fields(DocSpec)}


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _resolver_for(
    *,
    txt_path: Path,
    materia: Optional[Path],
    extra_search_dirs: Optional[Iterable[Path]] = None,
) -> Tuple[Callable[[str], Path], Callable[[str], Path], List[Path]]:
    if materia is None:
        try:
            materia = find_materia_root(txt_path.parent)
        except Exception:
            materia = None

    roots = candidate_asset_roots(txt_dir=txt_path.parent, materia=materia, extra=extra_search_dirs)

    def _resolve(name: str) -> Path:
        path = find_asset(name, roots)
        if path is None:
            return (roots[0] / name) if roots else Path(name)
        return path

    return _resolve, _resolve, roots


def build_error_for_header(txt_path: Path, header: DocHeaderParseResult) -> Optional[str]:
    if header.error:
        return f"{txt_path}: {header.error}"
    if not header.has_header:
        return f"{txt_path}: Falta header [DOC ...] en la primera línea no vacía."
    if "title" not in header.attrs or not str(header.attrs["title"]).strip():
        return f"{txt_path}: Header [DOC] debe incluir title."
    return None


def build_doc_spec(*, source_path: Path, out_path: Path, header: DocHeaderParseResult) -> DocSpec:
    error = build_error_for_header(source_path, header)
    if error:
        raise PdfBuildError(error)

    kwargs = {key: value for key, value in header.attrs.items() if key in DOCSPEC_FIELDS and key in ALLOWED_DOC_KEYS}
    kwargs.pop("out", None)
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
    extra_search_dirs: Optional[Sequence[Path]] = None,
) -> Path:
    txt_path = txt_path.expanduser().resolve()
    out_dir = out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    header = parse_doc_header_result(_read_text(txt_path))
    error = build_error_for_header(txt_path, header)
    if error:
        raise PdfBuildError(error)

    out_from_header = header.attrs.get("out")
    final_name = out_name or (
        str(out_from_header) if isinstance(out_from_header, str) and out_from_header else f"{txt_path.stem}.pdf"
    )
    out_path = out_dir / final_name

    resolve_pdf, resolve_img, _roots = _resolver_for(
        txt_path=txt_path,
        materia=materia,
        extra_search_dirs=extra_search_dirs,
    )

    def build_content(ctx):
        from ..parser.flowables import txt_to_flowables

        return txt_to_flowables(
            ctx,
            header.body,
            resolve_pdf=resolve_pdf,
            resolve_img=resolve_img,
            cache_dir=None,
        )

    from ..render.pdf import build_pdf

    spec = build_doc_spec(source_path=txt_path, out_path=out_path, header=header)
    return build_pdf(spec, build_content, theme=theme)
