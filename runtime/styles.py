from __future__ import annotations

from typing import Dict

from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

from .models import PdfTheme
from .utils import hex_color


def build_styles(theme: PdfTheme) -> Dict[str, ParagraphStyle]:
    styles = getSampleStyleSheet()

    base = ParagraphStyle(
        "Base",
        parent=styles["Normal"],
        fontName=theme.body_font,
        fontSize=theme.body_size,
        leading=theme.body_leading,
        textColor=hex_color(theme.text_color),
        spaceAfter=theme.space_sm,
    )

    subtitle = ParagraphStyle(
        "Subtitle",
        parent=base,
        fontSize=theme.body_size,
        leading=theme.body_leading,
        textColor=hex_color(theme.muted_color),
        spaceAfter=theme.space_md,
    )

    small = ParagraphStyle(
        "Small",
        parent=base,
        fontSize=9,
        leading=12,
        textColor=hex_color(theme.muted_color),
        spaceAfter=theme.space_sm,
    )

    h1 = ParagraphStyle(
        "H1",
        parent=base,
        fontName=theme.body_font_bold,
        fontSize=theme.h1_size,
        leading=theme.h1_leading,
        spaceBefore=0,
        spaceAfter=theme.space_xs,
        keepWithNext=1,
    )

    h2 = ParagraphStyle(
        "H2",
        parent=base,
        fontName=theme.body_font_bold,
        fontSize=theme.h2_size,
        leading=theme.h2_leading,
        spaceBefore=theme.space_md,
        spaceAfter=theme.space_xs,
        keepWithNext=1,
    )

    h3 = ParagraphStyle(
        "H3",
        parent=base,
        fontName=theme.body_font_bold,
        fontSize=theme.h3_size,
        leading=theme.h3_leading,
        spaceBefore=theme.space_sm,
        spaceAfter=theme.space_xs,
        keepWithNext=1,
    )

    note = ParagraphStyle("Note", parent=base, textColor=hex_color(theme.text_color))
    link = ParagraphStyle("Link", parent=base, textColor=hex_color(theme.accent_color))

    code = ParagraphStyle(
        "Code",
        parent=base,
        fontName=theme.mono_font,
        fontSize=10,
        leading=14,
        textColor=hex_color(theme.text_color),
    )

    toc0 = ParagraphStyle(
        "TOC0",
        parent=base,
        fontName=theme.body_font_bold,
        fontSize=10,
        leading=13,
        leftIndent=0,
        firstLineIndent=0,
        spaceBefore=2,
        spaceAfter=2,
        textColor=hex_color(theme.text_color),
    )
    toc1 = ParagraphStyle(
        "TOC1",
        parent=toc0,
        fontName=theme.body_font,
        leftIndent=14,
        firstLineIndent=0,
        spaceBefore=1,
        spaceAfter=1,
    )
    toc2 = ParagraphStyle(
        "TOC2",
        parent=toc1,
        leftIndent=28,
    )

    return {
        "Base": base,
        "Subtitle": subtitle,
        "Small": small,
        "H1": h1,
        "H2": h2,
        "H3": h3,
        "Note": note,
        "Link": link,
        "Code": code,
        "TOC0": toc0,
        "TOC1": toc1,
        "TOC2": toc2,
    }
