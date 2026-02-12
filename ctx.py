# Materia/Scripts/_pdf/ctx.py

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union, cast

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    Paragraph, Spacer, ListFlowable, ListItem, KeepTogether,
    Table, TableStyle
)
from reportlab.platypus.flowables import Flowable as RLFlowable

from .core import PdfTheme
from .utils import hex_color
from . import images as img_mod  # para ctx.fig / ctx.asset


Flowable = Any


class PdfCtx:
    def __init__(self, theme: PdfTheme):
        self.theme = theme
        self.styles = self._build_styles(theme)

        # Mantener nombres usados por tus scripts
        self.base = self.styles["Base"]
        self.subtitle = self.styles["Subtitle"]
        self.h1 = self.styles["H1"]
        self.h2 = self.styles["H2"]
        self.h3 = self.styles["H3"]
        self.note = self.styles["Note"]
        self.link = self.styles["Link"]
        self.small = self.styles["Small"]
        self.code = self.styles["Code"]

        # TOC styles (usados por render.py si include_toc=True)
        self.toc0 = self.styles["TOC0"]
        self.toc1 = self.styles["TOC1"]
        self.toc2 = self.styles["TOC2"]

    @staticmethod
    def _build_styles(theme: PdfTheme) -> Dict[str, ParagraphStyle]:
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

        # Table of Contents (TOC) styles
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

    # ---- Flowable factories ----
    def p(self, html: str, style: Optional[ParagraphStyle] = None) -> Paragraph:
        return Paragraph(html, style or self.base)

    def sp(self, h: int = 8) -> Spacer:
        return Spacer(1, h)

    def hr(self, space_before: int = 10, space_after: int = 10) -> Flowable:
        t = Table([[""]], colWidths=["*"])
        t.setStyle(TableStyle([
            ("LINEBELOW", (0, 0), (-1, -1), 1, hex_color(self.theme.line_color)),
            ("TOPPADDING", (0, 0), (-1, -1), space_before),
            ("BOTTOMPADDING", (0, 0), (-1, -1), space_after),
        ]))
        return t

    def keep(self, *flowables: Flowable) -> KeepTogether:
        return KeepTogether(list(flowables))

    def section(self, title: str, *flowables: Flowable) -> Flowable:
        items = [self.p(title, self.h2)]
        items.extend(flowables)
        return self.keep(*items)

    def ul(
        self,
        items: Sequence[Union[str, Paragraph]],
        left_indent: int = 18,
        bullet_indent: int = 8,
        space_after: int = 10,
    ) -> ListFlowable:
        li: List[Any] = [ListItem(it if isinstance(it, Paragraph) else self.p(it)) for it in items]
        # Pylance: stubs de reportlab no tipan ListItem como _NestedFlowable (falso positivo).
        return ListFlowable(
            cast(Any, li),
            bulletType="bullet",
            leftIndent=left_indent,
            bulletIndent=bullet_indent,
            spaceAfter=space_after,
        )

    def ol(
        self,
        items: Sequence[Union[str, Paragraph]],
        left_indent: int = 22,
        bullet_indent: int = 12,
        space_after: int = 10,
    ) -> ListFlowable:
        li: List[Any] = [ListItem(it if isinstance(it, Paragraph) else self.p(it)) for it in items]
        # Pylance: stubs de reportlab no tipan ListItem como _NestedFlowable (falso positivo).
        return ListFlowable(
            cast(Any, li),
            bulletType="1",
            leftIndent=left_indent,
            bulletIndent=bullet_indent,
            spaceAfter=space_after,
        )

    def codeblock(
        self,
        lines: Sequence[str],
        title: str | None = None,
        space_before: int = 6,
        space_after: int = 10,
    ) -> Flowable:
        """Bloque de código monoespaciado SPLITTABLE (evita LayoutError).

        Estrategia: Table con 1 fila por línea (y opcional título), splitByRow=1.
        `lines` debe venir sanitizado (por ejemplo con &nbsp; y sin unicode raro).
        """
        rows: List[List[Flowable]] = []

        if title:
            rows.append([self.p(title, self.h3)])

        if lines:
            for ln in lines:
                rows.append([self.p(ln, self.code)])
        else:
            rows.append([self.p("", self.code)])

        t = Table(rows, colWidths=["*"], splitByRow=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), hex_color(self.theme.callout_bg)),
            ("BOX", (0, 0), (-1, -1), 1, hex_color(self.theme.line_color)),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),

            # padding chico por fila para no inflar altura
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),

            # aire global arriba/abajo
            ("TOPPADDING", (0, 0), (-1, 0), max(8, space_before)),
            ("BOTTOMPADDING", (0, -1), (-1, -1), max(8, space_after)),
        ]))

        # Si hay título, separar del código
        if title and len(rows) >= 2:
            t.setStyle(TableStyle([
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ]))

        return t

    def table(
        self,
        rows: Sequence[Sequence[str]],
        *,
        header: bool = True,
        col_widths: Optional[Sequence[Any]] = None,
        aligns: Optional[Sequence[Optional[str]]] = None,
        space_after: int = 10,
    ) -> Flowable:
        """Tabla SPLITTABLE.

        - splitByRow=1 para permitir corte entre filas.
        - header=True: la primera fila se considera encabezado.
        - aligns: lista por columna con valores "LEFT"|"CENTER"|"RIGHT" o None.
        """
        if not rows:
            rows = [[""]]

        ncols = max(len(r) for r in rows) if rows else 1

        data: List[List[RLFlowable]] = []
        for r_i, r in enumerate(rows):
            rr = list(r) + [""] * max(0, ncols - len(r))
            out_row: List[RLFlowable] = []
            for c in rr:
                if header and r_i == 0:
                    out_row.append(self.p(f"<b>{c}</b>", self.base))
                else:
                    out_row.append(self.p(c, self.base))
            data.append(out_row)

        t = Table(data, colWidths=list(col_widths) if col_widths else ["*"] * ncols, splitByRow=1)

        style: List[Tuple[Any, ...]] = [
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, hex_color(self.theme.line_color)),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]

        if header and data:
            style += [
                ("BACKGROUND", (0, 0), (-1, 0), hex_color(self.theme.callout_bg)),
                ("LINEBELOW", (0, 0), (-1, 0), 1, hex_color(self.theme.line_color)),
            ]

        if aligns:
            for col, al in enumerate(aligns):
                if al:
                    style.append(("ALIGN", (col, 0), (col, -1), al))

        t.setStyle(TableStyle(style))
        t.spaceAfter = space_after
        return t

    def callout(
        self,
        kind: str,
        title: Optional[str],
        body: Union[str, Paragraph, RLFlowable, Sequence[Union[str, Paragraph, RLFlowable]]],
    ) -> Flowable:
        """Recuadro SPLITTABLE.

        - Preserva Flowables reales (listas, tablas, codeblocks, etc.)
        - Si recibe KeepTogether, lo aplana (flatten) para evitar bloques no splittables.
        - splitByRow=1 para que el recuadro pueda cortarse de forma limpia si es largo.
        """
        kind = (kind or "info").lower().strip()

        if kind == "note":
            bg = hex_color(self.theme.callout_note_bg)
            border = hex_color(self.theme.callout_note_border)
        elif kind == "warn":
            bg = hex_color(self.theme.callout_warn_bg)
            border = hex_color(self.theme.callout_warn_border)
        elif kind == "danger":
            bg = hex_color(self.theme.callout_danger_bg)
            border = hex_color(self.theme.callout_danger_border)
        else:
            bg = hex_color(self.theme.callout_bg)
            border = hex_color(self.theme.callout_border)

        def _as_flowable(x: Union[str, Paragraph, RLFlowable]) -> RLFlowable:
            if isinstance(x, str):
                return self.p(x, self.note)
            if isinstance(x, Paragraph):
                return x
            # RLFlowable es la clase base real de reportlab (NO typing.Any)
            if isinstance(x, RLFlowable):
                return x
            return self.p(str(x), self.note)

        def _flatten(x: RLFlowable) -> List[RLFlowable]:
            # Aplanar KeepTogether para permitir split dentro del callout
            try:
                from reportlab.platypus.flowables import KeepTogether as RLKeepTogether
                if isinstance(x, RLKeepTogether):
                    out: List[RLFlowable] = []
                    for y in list(getattr(x, "_content", [])):
                        out.extend(_flatten(_as_flowable(y)))  # type: ignore[arg-type]
                    return out
            except Exception:
                pass
            return [x]

        items: List[RLFlowable] = []
        if title:
            items.append(self.p(title, self.h3))

        if isinstance(body, (str, Paragraph)) or isinstance(body, RLFlowable):
            items.extend(_flatten(_as_flowable(body)))  # type: ignore[arg-type]
        else:
            for it in body:
                items.extend(_flatten(_as_flowable(it)))  # type: ignore[arg-type]

        if not items:
            items = [self.p("", self.note)]

        rows = [[it] for it in items]
        t = Table(rows, colWidths=["*"], splitByRow=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg),
            ("BOX", (0, 0), (-1, -1), 1, border),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),

            # padding mínimo por fila
            ("TOPPADDING", (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),

            # aire global arriba/abajo del recuadro
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
        ]))
        return t

    def kv(self, pairs: Sequence[Tuple[str, str]], space_after: int = 10) -> Flowable:
        data = []
        for k, v in pairs:
            data.append([self.p(f"<b>{k}</b>", self.small), self.p(v, self.small)])

        t = Table(data, colWidths=[90, "*"])
        t.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TEXTCOLOR", (0, 0), (-1, -1), hex_color(self.theme.muted_color)),
            ("LINEBELOW", (0, 0), (-1, -1), 0.5, hex_color(self.theme.line_color)),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        wrap = Table([[t]], colWidths=["*"])
        wrap.setStyle(TableStyle([
            ("BOTTOMPADDING", (0, 0), (-1, -1), space_after),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
        ]))
        return wrap

    # ---- Imágenes (API amigable para tutoriales) ----
    def fig(self, path: Path, caption: str, **kwargs):
        return img_mod.fig(self, path, caption, **kwargs)

    def content_width(self) -> float:
        return img_mod.content_width(self)
