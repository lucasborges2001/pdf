from __future__ import annotations

from .parser.inline import sanitize_code_line, sanitize_para, sanitize_plain
from .pipeline import compile_txt

__all__ = [
    "DocSpec",
    "PdfTheme",
    "PdfCtx",
    "build_pdf",
    "asset",
    "content_width",
    "fig",
    "fig_if_exists",
    "fig_if_asset",
    "fig_pdf_page",
    "txt_to_flowables",
    "compile_txt",
    "sanitize_para",
    "sanitize_plain",
    "sanitize_code_line",
]

__version__ = "0.4.0"


def __getattr__(name: str):
    if name in {"PdfTheme", "DocSpec"}:
        from .runtime.core import DocSpec, PdfTheme

        return {"PdfTheme": PdfTheme, "DocSpec": DocSpec}[name]
    if name == "PdfCtx":
        from .runtime.ctx import PdfCtx

        return PdfCtx
    if name == "build_pdf":
        from .render.pdf import build_pdf

        return build_pdf
    if name in {"asset", "content_width", "fig", "fig_if_exists", "fig_if_asset", "fig_pdf_page"}:
        from .render import images

        return getattr(images, name)
    if name == "txt_to_flowables":
        from .parser.flowables import txt_to_flowables

        return txt_to_flowables
    raise AttributeError(name)
