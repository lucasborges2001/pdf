# Materia/Scripts/_pdf/core.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from reportlab.lib.pagesizes import A4


@dataclass(frozen=True)
class PdfTheme:
    pagesize: tuple = A4

    # Márgenes
    left_margin: int = 52
    right_margin: int = 52
    top_margin: int = 72
    bottom_margin: int = 55

    # Header / layout
    header_line_inset: int = 40
    header_line_y_offset: int = 30
    first_page_reserved_top: int = 200
    later_page_reserved_top: int = 70

    # Tipografía base
    body_font: str = "Helvetica"
    body_font_bold: str = "Helvetica-Bold"
    mono_font: str = "Courier"
    body_size: int = 11
    body_leading: int = 16

    # Escalas títulos
    h1_size: int = 22
    h1_leading: int = 26
    h2_size: int = 14
    h2_leading: int = 18
    h3_size: int = 12
    h3_leading: int = 16

    # Espaciados
    space_xs: int = 4
    space_sm: int = 8
    space_md: int = 12
    space_lg: int = 16

    # Colores
    text_color: str = "#111827"
    muted_color: str = "#4B5563"
    footer_color: str = "#64748B"
    line_color: str = "#C7D2FE"
    accent_color: str = "#1D4ED8"

    # Callouts
    callout_border: str = "#CBD5E1"
    callout_bg: str = "#F8FAFC"
    callout_note_bg: str = "#EFF6FF"
    callout_note_border: str = "#93C5FD"
    callout_warn_bg: str = "#FFF7ED"
    callout_warn_border: str = "#FDBA74"
    callout_danger_bg: str = "#FEF2F2"
    callout_danger_border: str = "#FCA5A5"


@dataclass(frozen=True)
class DocSpec:
    out_path: Path

    title: str
    subtitle: Optional[str] = None

    # Footer (3 columnas)
    footer_left: str = "Lucas Borges"
    footer_center: str = "Arquitectura de Computadoras"
    footer_right: str = ""
    footer_show_page: bool = True
    footer_link_to_toc: bool = True  # si include_toc=True: link desde footer_center a "toc"

    # Compatibilidad (scripts viejos)
    system: str = ""
    contacto: str = ""

    # PDF metadata
    author: str = ""
    subject: str = ""
    keywords: str = ""

    # Assets
    logo_left: Optional[Path] = None
    icon_right: Optional[Path] = None

    # Título automático
    include_title_block: bool = True
    meta_line: Optional[str] = None

    # TOC / Outline
    include_toc: bool = False
    toc_title: str = "Contenido"
    toc_max_level: int = 3
