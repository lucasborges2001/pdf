from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union

Scalar = Union[str, bool, int]

_DOC_RE = re.compile(r"^\[DOC(?P<body>.*)\]\s*$")

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


@dataclass(frozen=True)
class DocHeaderParseResult:
    attrs: Dict[str, Scalar]
    unknown_keys: List[str]
    body: str
    error: Optional[str]
    has_header: bool
    line_number: int

    def as_tuple(self) -> Tuple[Dict[str, Scalar], List[str], str, Optional[str]]:
        return self.attrs, self.unknown_keys, self.body, self.error


def _parse_scalar(value: str) -> Scalar:
    raw = value.strip()
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if re.fullmatch(r"-?\d+", raw):
        try:
            return int(raw)
        except Exception:
            return raw
    return raw


def parse_doc_header_result(text: str) -> DocHeaderParseResult:
    lines = text.splitlines()
    idx = 0
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    if idx >= len(lines):
        return DocHeaderParseResult({}, [], text, None, False, 0)

    line = lines[idx].strip()
    rest = "\n".join(lines[:idx] + lines[idx + 1 :])

    if not line.startswith("[DOC"):
        return DocHeaderParseResult({}, [], text, None, False, idx + 1)

    match = _DOC_RE.match(line)
    if not match:
        return DocHeaderParseResult(
            {},
            [],
            rest,
            "Header [DOC ...] inválido. Debe cerrar con ']' y usar pares clave=valor.",
            True,
            idx + 1,
        )

    attrs: Dict[str, Scalar] = {}
    unknown: List[str] = []
    body = (match.group("body") or "").strip()

    if body:
        try:
            tokens = shlex.split(body)
        except ValueError as exc:
            return DocHeaderParseResult({}, [], rest, f"Header [DOC ...] inválido: {exc}", True, idx + 1)

        for token in tokens:
            if "=" not in token:
                return DocHeaderParseResult(
                    {},
                    [],
                    rest,
                    f"Header [DOC ...] inválido: token sin '=' ({token}).",
                    True,
                    idx + 1,
                )
            key, value = token.split("=", 1)
            key = key.strip()
            attrs[key] = _parse_scalar(value)
            if key not in ALLOWED_DOC_KEYS:
                unknown.append(key)

    return DocHeaderParseResult(attrs, unknown, rest, None, True, idx + 1)


def parse_doc_header(text: str) -> Tuple[Dict[str, Scalar], List[str], str, Optional[str]]:
    return parse_doc_header_result(text).as_tuple()
