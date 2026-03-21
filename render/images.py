from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, List, Optional

from reportlab.lib import colors
from reportlab.platypus import Image as RLImage, Spacer, Table, TableStyle

Flowable = Any

_WARN = os.getenv("PDF_WARN_MISSING_ASSETS", "0").strip() == "1"
_FRAME_PAD = 6.0


def _warn(msg: str) -> None:
    if _WARN:
        print(f"[WARN][_pdf] {msg}", file=sys.stderr)


def asset(base_dir: Path, name: str, fallback_dir: Optional[Path] = None) -> Path:
    primary = base_dir / name
    if primary.is_file():
        return primary

    if fallback_dir is None:
        env = os.getenv("PDF_ASSET_FALLBACK", "").strip()
        fallback_dir = Path(env) if env else Path(__file__).resolve().parent / "assets"

    secondary = fallback_dir / name
    if secondary.is_file():
        return secondary

    _warn(f"Asset no encontrado: '{name}' (buscado en '{primary}' y fallback '{secondary}')")
    return primary


def content_width(ctx) -> float:
    page_w, _ = ctx.theme.pagesize
    return float(page_w - ctx.theme.left_margin - ctx.theme.right_margin)


def _frame_effective_width(ctx) -> float:
    return max(10.0, content_width(ctx) - 2 * _FRAME_PAD)


def _min_frame_effective_height(ctx) -> float:
    _, page_h = ctx.theme.pagesize
    h_first = page_h - ctx.theme.bottom_margin - ctx.theme.first_page_reserved_top
    h_later = page_h - ctx.theme.bottom_margin - ctx.theme.later_page_reserved_top
    return max(10.0, float(min(h_first, h_later)) - 2 * _FRAME_PAD)


def fig(
    ctx,
    path: Path,
    caption: Optional[str] = None,
    *,
    max_w: Optional[float] = None,
    max_h: Optional[float] = None,
    space_after: int = 10,
    border_color: str = "#E0E0E0",
    pad: int = 6,
    safety: float = 10.0,
) -> List[Flowable]:
    if not path.is_file():
        _warn(f"Figura omitida (archivo inexistente): {path}")
        return []

    eff_w = _frame_effective_width(ctx)
    eff_h = _min_frame_effective_height(ctx)
    w_limit = float(min(max_w, eff_w) if max_w is not None else eff_w)
    h_limit = float(min(max_h, eff_h) if max_h is not None else eff_h)
    max_img_h = h_limit - (2 * pad) - 4 - safety
    if max_img_h <= 20:
        _warn(f"Figura omitida (sin espacio vertical suficiente): {path}")
        return []

    image = RLImage(str(path))
    iw, ih = float(image.imageWidth), float(image.imageHeight)
    if iw <= 0 or ih <= 0:
        _warn(f"Figura omitida (dimensiones inválidas): {path}")
        return []

    scale = min(1.0, w_limit / iw, max_img_h / ih)
    image.drawWidth = iw * scale
    image.drawHeight = ih * scale

    table = Table([[image]], colWidths=[w_limit])
    table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(border_color)),
                ("LEFTPADDING", (0, 0), (-1, -1), pad),
                ("RIGHTPADDING", (0, 0), (-1, -1), pad),
                ("TOPPADDING", (0, 0), (-1, -1), pad),
                ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
            ]
        )
    )

    out: List[Flowable] = [table]
    if caption:
        out.append(ctx.p(caption, ctx.small))
    out.append(Spacer(1, space_after))
    return out


def fig_if_exists(ctx, path: Path, caption: Optional[str] = None, **kwargs) -> List[Flowable]:
    return fig(ctx, path, caption, **kwargs)


def fig_if_asset(
    ctx,
    base_dir: Path,
    filename: str,
    caption: Optional[str] = None,
    *,
    fallback_dir: Optional[Path] = None,
    italic: bool = False,
    **kwargs,
) -> List[Flowable]:
    path = asset(base_dir, filename, fallback_dir=fallback_dir)
    final_caption = f"<i>{caption}</i>" if caption and italic else caption
    return fig_if_exists(ctx, path, final_caption, **kwargs)


def pdf_page_to_png(pdf_path: Path, page_1based: int, out_png: Path, *, zoom: float = 2.0) -> bool:
    if out_png.is_file():
        return True
    if not pdf_path.is_file():
        _warn(f"PDF fuente no existe para exportar página: {pdf_path}")
        return False

    try:
        import fitz  # type: ignore
    except Exception:
        _warn("PyMuPDF (fitz) no está instalado. Se omiten figuras desde PDF.")
        return False

    out_png.parent.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(page_1based - 1)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        pix.save(str(out_png))
        return True
    except Exception as exc:
        _warn(f"No se pudo exportar {pdf_path} pág. {page_1based}: {type(exc).__name__}: {exc}")
        return False
    finally:
        doc.close()


def fig_pdf_page(
    ctx,
    pdf_path: Path,
    page_1based: int,
    *,
    caption: Optional[str] = None,
    cache_dir: Optional[Path] = None,
    zoom: float = 2.0,
    **kwargs,
) -> List[Flowable]:
    cache_root = cache_dir if cache_dir is not None else (Path.cwd() / "assets" / "_pdfpages")
    out_png = cache_root / pdf_path.stem / f"p{page_1based:03d}_z{zoom:g}.png"
    if not pdf_page_to_png(pdf_path, page_1based, out_png, zoom=zoom):
        return []
    return fig(ctx, out_png, caption, **kwargs)
