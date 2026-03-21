from __future__ import annotations

from ..parser.structure import (
    condbreak,
    consume_procedural_steps,
    is_dash_rule,
    is_eq_rule,
    is_procedural_step_start,
    is_rule,
    looks_like_simple_dot_heading,
    mk_heading,
    parse_pipe_table,
    peek_next_nonempty,
    pipe_align_from_sep,
    slugify,
    unique_key,
)

__all__ = [
    "condbreak",
    "consume_procedural_steps",
    "is_dash_rule",
    "is_eq_rule",
    "is_procedural_step_start",
    "is_rule",
    "looks_like_simple_dot_heading",
    "mk_heading",
    "parse_pipe_table",
    "peek_next_nonempty",
    "pipe_align_from_sep",
    "slugify",
    "unique_key",
]
