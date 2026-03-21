from __future__ import annotations

__all__ = ["DocSpec", "PdfTheme", "PdfCtx"]


def __getattr__(name: str):
    if name in {"DocSpec", "PdfTheme"}:
        from .core import DocSpec, PdfTheme

        return {"DocSpec": DocSpec, "PdfTheme": PdfTheme}[name]
    if name == "PdfCtx":
        from .ctx import PdfCtx

        return PdfCtx
    raise AttributeError(name)
