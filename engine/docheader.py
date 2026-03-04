from __future__ import annotations

import shlex
import re
from typing import Dict, List, Optional, Tuple, Union

Scalar = Union[str, bool, int]

_DOC_RE = re.compile(r"^\[DOC(?P<body>.*)\]\s*$")

# Mantener en sync con runtime.core.DocSpec
ALLOWED_DOC_KEYS = {
    "out",
    "title",
    "subtitle",
    "meta_line",
    "include_title_block",
    "include_toc",
    "toc_title",
    "toc_max_level",
    "footer_left",
    "footer_center",
    "footer_right",
    "footer_show_page",
    "footer_link_to_toc",
    "author",
    "subject",
    "keywords",
    "system",
    "contacto",
}

def _parse_scalar(v: str) -> Scalar:
    s = v.strip()
    lo = s.lower()
    if lo in {"true", "false"}:
        return lo == "true"
    if re.fullmatch(r"-?\d+", s):
        try:
            return int(s)
        except Exception:
            return s
    return s

def parse_doc_header(text: str) -> Tuple[Dict[str, Scalar], List[str], str, Optional[str]]:
    """Parsea un header [DOC ...] si está en la primera línea no vacía.

    Retorna:
      attrs: dict clave->valor
      unknown_keys: claves presentes pero no permitidas
      rest_text: el texto sin la línea del header
      error: mensaje de error si el header existe pero es inválido
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return {}, [], text, None

    m = _DOC_RE.match(lines[i].strip())
    if not m:
        return {}, [], text, None

    body = (m.group("body") or "").strip()
    attrs: Dict[str, Scalar] = {}
    unknown: List[str] = []

    if body:
        try:
            toks = shlex.split(body)
        except ValueError as e:
            rest = "\n".join(lines[:i] + lines[i+1:])
            return {}, [], rest, f"Header [DOC ...] inválido: {e}"

        for tok in toks:
            if "=" not in tok:
                continue
            k, v = tok.split("=", 1)
            k = k.strip()
            attrs[k] = _parse_scalar(v)
            if k not in ALLOWED_DOC_KEYS:
                unknown.append(k)

    rest = "\n".join(lines[:i] + lines[i+1:])
    return attrs, unknown, rest, None
