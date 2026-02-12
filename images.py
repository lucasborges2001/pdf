# Materia/Scripts/_pdf/images.py
# Helpers para assets + figuras (flowables) reutilizables por todos los tutoriales.

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, List, Any

from reportlab.platypus import Image as RLImage, Spacer, Table, TableStyle
from reportlab.lib import colors

Flowable = Any

_WARN = os.getenv("PDF_WARN_MISSING_ASSETS", "0").strip() == "1"

# ReportLab Frame paddings por defecto (si no se pasan al Frame()):
# left/right/top/bottom = 6 pt
_FRAME_PAD = 6.0


def _warn(msg: str) -> None:
    if _WARN:
        print(f"[WARN][_pdf] {msg}", file=sys.stderr)


def asset(base_dir: Path, name: str, fallback_dir: Optional[Path] = None) -> Path:
    p1 = base_dir / name
    if p1.is_file():
        return p1

    if fallback_dir is None:
        env = os.getenv("PDF_ASSET_FALLBACK", "").strip()
        if env:
            fallback_dir = Path(env)
        else:
            fallback_dir = Path(__file__).resolve().parent / "assets"  # Scripts/_pdf/assets

    p2 = fallback_dir / name
    if p2.is_file():
        return p2

    _warn(f"Asset no encontrado: '{name}' (buscado en '{p1}' y fallback '{p2}')")
    return p1



def content_width(ctx) -> float:
    """Ancho útil según márgenes del theme (sin considerar padding interno del Frame)."""
    page_w, _ = ctx.theme.pagesize
    return float(page_w - ctx.theme.left_margin - ctx.theme.right_margin)


def _frame_effective_width(ctx) -> float:
    """Ancho efectivo dentro del Frame (resta padding interno del Frame)."""
    return max(10.0, content_width(ctx) - 2 * _FRAME_PAD)


def _min_frame_effective_height(ctx) -> float:
    """
    Altura efectiva mínima garantizada del Frame, considerando:
    - First vs Later (reserved top distintos)
    - padding interno del Frame
    """
    _, page_h = ctx.theme.pagesize
    h_first = page_h - ctx.theme.bottom_margin - ctx.theme.first_page_reserved_top
    h_later = page_h - ctx.theme.bottom_margin - ctx.theme.later_page_reserved_top
    h = float(min(h_first, h_later))
    return max(10.0, h - 2 * _FRAME_PAD)


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
    """
    Inserta una figura (imagen) escalada para que SIEMPRE entre en el Frame.

    - Por defecto limita el ancho al ancho efectivo del Frame.
    - Por defecto limita la altura a la altura efectiva mínima del Frame (First/Later).
      Esto evita LayoutError de ReportLab (flowable más alto/ancho que el frame).

    safety: margen extra en puntos para evitar errores por redondeos/bordes.
    """
    if not path.is_file():
        _warn(f"Figura omitida (archivo inexistente): {path}")
        return []

    # Límites efectivos (Frame)
    eff_w = _frame_effective_width(ctx)
    eff_h = _min_frame_effective_height(ctx)

    w_limit = float(min(max_w, eff_w) if max_w is not None else eff_w)
    h_limit = float(min(max_h, eff_h) if max_h is not None else eff_h)

    # Reservamos espacio para padding + borde + margen de seguridad
    max_img_h = h_limit - (2 * pad) - 4 - safety
    if max_img_h <= 20:
        _warn(f"Figura omitida (sin espacio vertical suficiente): {path}")
        return []

    img = RLImage(str(path))
    iw, ih = float(img.imageWidth), float(img.imageHeight)
    if iw <= 0 or ih <= 0:
        _warn(f"Figura omitida (dimensiones inválidas): {path}")
        return []

    # Escalado por ancho y por alto (para que entre)
    scale_w = w_limit / iw
    scale_h = max_img_h / ih
    scale = min(1.0, scale_w, scale_h)

    img.drawWidth = iw * scale
    img.drawHeight = ih * scale

    # El contenedor (Table) debe respetar el ancho efectivo del frame
    t = Table([[img]], colWidths=[w_limit])
    t.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor(border_color)),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
    ]))

    out: List[Flowable] = [t]
    if caption:
        out.append(ctx.p(caption, ctx.small))
    out.append(Spacer(1, space_after))
    return out


def fig_if_exists(
    ctx,
    path: Path,
    caption: Optional[str] = None,
    *,
    max_w: Optional[float] = None,
    max_h: Optional[float] = None,
    space_after: int = 10,
    border_color: str = "#E0E0E0",
    pad: int = 6,
) -> List[Flowable]:
    return fig(
        ctx,
        path,
        caption,
        max_w=max_w,
        max_h=max_h,
        space_after=space_after,
        border_color=border_color,
        pad=pad,
    )


def fig_if_asset(
    ctx,
    base_dir: Path,
    filename: str,
    caption: Optional[str] = None,
    *,
    fallback_dir: Optional[Path] = None,
    italic: bool = False,
    max_w: Optional[float] = None,
    max_h: Optional[float] = None,
    space_after: int = 10,
    border_color: str = "#E0E0E0",
    pad: int = 6,
) -> List[Flowable]:
    p = asset(base_dir, filename, fallback_dir=fallback_dir)
    cap = f"<i>{caption}</i>" if (caption and italic) else caption
    return fig_if_exists(
        ctx,
        p,
        cap,
        max_w=max_w,
        max_h=max_h,
        space_after=space_after,
        border_color=border_color,
        pad=pad,
    )


# ============================================================
# Figuras desde páginas de PDFs (sin recortar manual)
# ============================================================
def pdf_page_to_png(
    pdf_path: Path,
    page_1based: int,
    out_png: Path,
    *,
    zoom: float = 2.0,
) -> bool:
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
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        pix.save(str(out_png))
        return True
    except Exception as e:
        _warn(f"No se pudo exportar {pdf_path} pág. {page_1based}: {type(e).__name__}: {e}")
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
    max_w: Optional[float] = None,
    max_h: Optional[float] = None,
    space_after: int = 10,
    border_color: str = "#E0E0E0",
    pad: int = 6,
) -> List[Flowable]:
    cd = cache_dir if cache_dir is not None else (Path.cwd() / "assets" / "_pdfpages")
    out_png = cd / pdf_path.stem / f"p{page_1based:03d}_z{zoom:g}.png"

    ok = pdf_page_to_png(pdf_path, page_1based, out_png, zoom=zoom)
    if not ok:
        return []

    return fig(
        ctx,
        out_png,
        caption,
        max_w=max_w,
        max_h=max_h,
        space_after=space_after,
        border_color=border_color,
        pad=pad,
    )
