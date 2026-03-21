from __future__ import annotations

from ..parser.inline import sanitize_code_line, sanitize_para, sanitize_plain


def txt_to_flowables(*args, **kwargs):
    from ..parser.flowables import txt_to_flowables as _txt_to_flowables

    return _txt_to_flowables(*args, **kwargs)


def __getattr__(name: str):
    if name in {
        "_FIG_RE",
        "_IMG_RE",
        "_PB_RE",
        "_CALLOUT_OPEN_RE",
        "_CALLOUT_CLOSE_RE",
        "_BLOCK_OPEN_RE",
        "_BLOCK_CLOSE_RE",
        "_FENCE_OPEN_RE",
        "_FENCE_CLOSE_RE",
    }:
        from ..parser import syntax

        mapping = {
            "_FIG_RE": syntax.FIG_RE,
            "_IMG_RE": syntax.IMG_RE,
            "_PB_RE": syntax.PB_RE,
            "_CALLOUT_OPEN_RE": syntax.CALLOUT_OPEN_RE,
            "_CALLOUT_CLOSE_RE": syntax.CALLOUT_CLOSE_RE,
            "_BLOCK_OPEN_RE": syntax.BLOCK_OPEN_RE,
            "_BLOCK_CLOSE_RE": syntax.BLOCK_CLOSE_RE,
            "_FENCE_OPEN_RE": syntax.FENCE_OPEN_RE,
            "_FENCE_CLOSE_RE": syntax.FENCE_CLOSE_RE,
        }
        return mapping[name]
    raise AttributeError(name)


__all__ = ["sanitize_para", "sanitize_plain", "sanitize_code_line", "txt_to_flowables"]
