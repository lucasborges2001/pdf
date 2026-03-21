from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, List, Optional

from reportlab.pdfgen import canvas as canv
from reportlab.platypus import BaseDocTemplate, Frame, PageBreak, PageTemplate
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.tableofcontents import TableOfContents

from ..parser.inline import sanitize_para, sanitize_plain
from ..runtime.ctx import PdfCtx
from ..runtime.models import DocSpec, PdfTheme
from ..runtime.utils import exists, hex_color, safe_draw_image

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

        if key:
            try:
                self.canv.bookmarkPage(key)
            except Exception:
                pass

        if skip_toc and skip_outline and not key:
            return

        if level is None:
            style_name = getattr(flowable.style, "name", "")
            if style_name == "H1":
                level = 0
            elif style_name == "H2":
                level = 1
            elif style_name == "H3":
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

        if not skip_outline:
            try:
                self.canv.addOutlineEntry(text, key, level=toc_level, closed=False)
            except Exception:
                pass

        if self._toc is not None and not skip_toc:
            self.notify("TOCEntry", (toc_level, text, self.page, key))


def build_pdf(spec: DocSpec, build_content: Callable[[PdfCtx], List[Flowable]], theme: Optional[PdfTheme] = None) -> Path:
    theme = theme or PdfTheme()
    ctx = PdfCtx(theme)
    page_w, page_h = theme.pagesize

    def draw_footer(canvas: canv.Canvas, doc) -> None:
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(hex_color(theme.footer_color))
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
            canvas.drawString(theme.left_margin, y, left)
            if left.strip() == "Lucas Borges":
                text_width = canvas.stringWidth(left, "Helvetica", 9)
                canvas.linkURL(
                    "https://www.linkedin.com/in/lucasborges0109",
                    (theme.left_margin, y - 2, theme.left_margin + text_width, y + 10),
                    relative=0,
                    thickness=0,
                )

        if center:
            canvas.drawCentredString(page_w / 2, y, center)
            if spec.include_toc and spec.footer_link_to_toc and doc.page >= 2:
                width = 240
                height = 12
                x0 = (page_w / 2) - (width / 2)
                y0 = y - 2
                canvas.linkRect("", "toc", (x0, y0, x0 + width, y0 + height), relative=0, thickness=0)

        if right:
            canvas.drawRightString(page_w - theme.right_margin, y, right)

    def draw_header_line(canvas: canv.Canvas) -> None:
        canvas.setStrokeColor(hex_color(theme.line_color))
        canvas.setLineWidth(1)
        y = page_h - theme.header_line_y_offset
        canvas.line(theme.header_line_inset, y, page_w - theme.header_line_inset, y)

    def on_first_page(canvas: canv.Canvas, doc) -> None:
        draw_header_line(canvas)
        header_y = page_h - theme.header_line_y_offset

        if exists(spec.logo_left):
            safe_draw_image(canvas, spec.logo_left, theme.left_margin, header_y - 18, w=220)  # type: ignore[arg-type]
        if exists(spec.icon_right):
            safe_draw_image(
                canvas,
                spec.icon_right,  # type: ignore[arg-type]
                page_w - theme.right_margin - 52,
                header_y - 20,
                w=52,
            )
        draw_footer(canvas, doc)

    def on_later_pages(canvas: canv.Canvas, doc) -> None:
        draw_header_line(canvas)
        draw_footer(canvas, doc)

    story: List[Flowable] = []
    if spec.include_title_block:
        title = ctx.p(sanitize_para(spec.title), ctx.h1)
        setattr(title, "_fbd_skip_toc", True)
        setattr(title, "_fbd_skip_outline", True)
        story.append(title)

        if spec.meta_line:
            story.append(ctx.p(sanitize_para(spec.meta_line), ctx.small))
        if spec.subtitle:
            story.append(ctx.p(sanitize_para(spec.subtitle), ctx.subtitle))
        story.append(ctx.hr(space_before=4, space_after=10))

    toc: Optional[TableOfContents] = None
    if spec.include_toc:
        toc = TableOfContents()
        toc.levelStyles = [ctx.toc0, ctx.toc1, ctx.toc2][: max(1, spec.toc_max_level)]

        heading = ctx.p(f'<a name="toc"/>{sanitize_para(spec.toc_title)}', ctx.h2)
        setattr(heading, "_fbd_key", "toc")
        setattr(heading, "_fbd_level", 0)
        setattr(heading, "_fbd_skip_toc", True)
        setattr(heading, "_fbd_skip_outline", True)
        story.extend([heading, toc, PageBreak()])

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

    deduped: List[Any] = []
    prev_page_break = False
    for flowable in story:
        is_page_break = isinstance(flowable, PageBreak)
        if is_page_break and prev_page_break:
            continue
        deduped.append(flowable)
        prev_page_break = is_page_break

    if spec.include_toc:
        doc.multiBuild(deduped)
    else:
        doc.build(deduped)

    return spec.out_path
