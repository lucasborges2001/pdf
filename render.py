# Materia/Scripts/_pdf/render.py

from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional, Any

from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, PageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.platypus.paragraph import Paragraph
from reportlab.pdfgen import canvas as canv

from .core import DocSpec, PdfTheme
from .ctx import PdfCtx
from .utils import exists, hex_color, safe_draw_image
from .txtfmt import sanitize_para, sanitize_plain

Flowable = Any


class FbdDocTemplate(BaseDocTemplate):
    def __init__(self, *args, toc: Optional[TableOfContents] = None, toc_max_level: int = 3, **kwargs):
        super().__init__(*args, **kwargs)
        self._toc = toc
        self._toc_max_level = toc_max_level

    def afterFlowable(self, flowable: Flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return

        skip_toc = bool(getattr(flowable, "_fbd_skip_toc", False))
        skip_outline = bool(getattr(flowable, "_fbd_skip_outline", False))

        level = getattr(flowable, "_fbd_level", None)
        key = getattr(flowable, "_fbd_key", None)

        # Si tiene key explícita, siempre intentamos generar el bookmark (aunque se saltee TOC/outline)
        if key:
            try:
                self.canv.bookmarkPage(key)
            except Exception:
                pass

        # Si se saltea todo y no hay bookmark que crear, no hacemos nada más
        if skip_toc and skip_outline and not key:
            return

        if level is None:
            st = getattr(flowable.style, "name", "")
            if st == "H1":
                level = 0
            elif st == "H2":
                level = 1
            elif st == "H3":
                level = 2

        if level is None:
            return

        toc_level = max(0, min(int(level), self._toc_max_level - 1))
        text = flowable.getPlainText()

        if not key:
            key = f"sec-{self.page}-{abs(hash(text)) % 10_000_000}"
            try:
                self.canv.bookmarkPage(key)
            except Exception:
                pass

        # Outline
        if not skip_outline:
            try:
                self.canv.addOutlineEntry(text, key, level=toc_level, closed=False)
            except Exception:
                pass

        # TOC
        if self._toc is not None and not skip_toc:
            self.notify("TOCEntry", (toc_level, text, self.page, key))


def build_pdf(
    spec: DocSpec,
    build_content: Callable[[PdfCtx], List[Flowable]],
    theme: Optional[PdfTheme] = None,
) -> Path:
    theme = theme or PdfTheme()
    ctx = PdfCtx(theme)

    page_w, page_h = theme.pagesize

    def draw_footer(c: canv.Canvas, doc):
        c.setFont("Helvetica", 9)
        c.setFillColor(hex_color(theme.footer_color))
        y = 22

        left = sanitize_plain(spec.footer_left or spec.system or "")
        center = sanitize_plain(spec.footer_center or spec.contacto or "")

        right_bits: List[str] = []
        if spec.footer_right:
            right_bits.append(sanitize_plain(spec.footer_right))
        if spec.footer_show_page:
            right_bits.append(f"Página {doc.page}")
        right = " · ".join(right_bits).strip()

        if left:
            c.drawString(theme.left_margin, y, left)

            if left.strip() == "Lucas Borges":
                text_width = c.stringWidth(left, "Helvetica", 9)
                c.linkURL(
                    "https://www.linkedin.com/in/lucasborges0109",
                    (
                        theme.left_margin,
                        y - 2,
                        theme.left_margin + text_width,
                        y + 10,
                    ),
                    relative=0,
                    thickness=0,
                )


        if center:
            c.drawCentredString(page_w / 2, y, center)
            if spec.include_toc and spec.footer_link_to_toc and doc.page >= 2:
                w = 240
                h = 12
                x0 = (page_w / 2) - (w / 2)
                y0 = y - 2
                c.linkRect("", "toc", (x0, y0, x0 + w, y0 + h), relative=0, thickness=0)

        if right:
            c.drawRightString(page_w - theme.right_margin, y, right)

    def draw_header_line(c: canv.Canvas):
        c.setStrokeColor(hex_color(theme.line_color))
        c.setLineWidth(1)
        y = page_h - theme.header_line_y_offset
        c.line(theme.header_line_inset, y, page_w - theme.header_line_inset, y)

    def on_first_page(c: canv.Canvas, doc):
        draw_header_line(c)
        header_y = page_h - theme.header_line_y_offset

        if exists(spec.logo_left):
            safe_draw_image(
                c,
                spec.logo_left,  # type: ignore[arg-type]
                theme.left_margin,
                header_y - 18,
                w=220,
            )

        if exists(spec.icon_right):
            icon_w = 52
            safe_draw_image(
                c,
                spec.icon_right,  # type: ignore[arg-type]
                page_w - theme.right_margin - icon_w,
                header_y - 20,
                w=icon_w,
            )

        draw_footer(c, doc)

    def on_later_pages(c: canv.Canvas, doc):
        draw_header_line(c)
        draw_footer(c, doc)

    story: List[Flowable] = []

    if spec.include_title_block:
        ptitle = ctx.p(sanitize_para(spec.title), ctx.h1)
        setattr(ptitle, "_fbd_skip_toc", True)
        setattr(ptitle, "_fbd_skip_outline", True)
        story.append(ptitle)

        if spec.meta_line:
            story.append(ctx.p(sanitize_para(spec.meta_line), ctx.small))

        if spec.subtitle:
            story.append(ctx.p(sanitize_para(spec.subtitle), ctx.subtitle))

        story.append(ctx.hr(space_before=4, space_after=10))

    toc: Optional[TableOfContents] = None
    if spec.include_toc:
        toc = TableOfContents()
        toc.levelStyles = [ctx.toc0, ctx.toc1, ctx.toc2][: max(1, spec.toc_max_level)]

        p = ctx.p(f'<a name="toc"/>{sanitize_para(spec.toc_title)}', ctx.h2)
        setattr(p, "_fbd_key", "toc")          # destino para linkRect
        setattr(p, "_fbd_level", 0)            # por si alguien usa outline manualmente
        setattr(p, "_fbd_skip_toc", True)      # NO listar dentro del propio TOC
        setattr(p, "_fbd_skip_outline", True)  # evitar ruido en outline
        story.append(p)

        story.append(toc)
        story.append(PageBreak())

    story.extend(build_content(ctx))

    doc = FbdDocTemplate(
        str(spec.out_path),
        pagesize=theme.pagesize,
        leftMargin=theme.left_margin,
        rightMargin=theme.right_margin,
        topMargin=theme.top_margin,
        bottomMargin=theme.bottom_margin,
        title=sanitize_plain(spec.title),
        author=spec.author or "Lucas Borges",
        subject=spec.subject or "",
        keywords=spec.keywords or "",
        toc=toc,
        toc_max_level=spec.toc_max_level,
    )

    frame_first = Frame(
        theme.left_margin,
        theme.bottom_margin,
        page_w - (theme.left_margin + theme.right_margin),
        page_h - theme.bottom_margin - theme.first_page_reserved_top,
        id="first",
    )
    frame_later = Frame(
        theme.left_margin,
        theme.bottom_margin,
        page_w - (theme.left_margin + theme.right_margin),
        page_h - theme.bottom_margin - theme.later_page_reserved_top,
        id="later",
    )

    doc.addPageTemplates(
        [
            PageTemplate(id="First", frames=[frame_first], onPage=on_first_page, autoNextPageTemplate="Later"),
            PageTemplate(id="Later", frames=[frame_later], onPage=on_later_pages),
        ]
    )

    spec.out_path.parent.mkdir(parents=True, exist_ok=True)

    if spec.include_toc:
        doc.multiBuild(story)
    else:
        doc.build(story)

    return spec.out_path
