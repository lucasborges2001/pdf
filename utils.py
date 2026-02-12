# Materia/Scripts/_pdf/utils.py
# Helpers internos compartidos (no API pública)

from __future__ import annotations

from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.pdfgen import canvas as canv
from reportlab.lib.utils import ImageReader


def exists(p: Optional[Path]) -> bool:
    return bool(p) and p.is_file()


def hex_color(c: str):
    return colors.HexColor(c)


def safe_draw_image(c: canv.Canvas, path: Path, x: float, y: float, w: float) -> float:
    """
    Dibuja imagen manteniendo aspect ratio. No revienta si falla.
    Retorna alto dibujado.
    """
    try:
        img = ImageReader(str(path))
        iw, ih = img.getSize()
        h = w * ih / iw
        c.drawImage(img, x, y - h, width=w, height=h, mask="auto")
        return h
    except Exception:
        return 0.0
