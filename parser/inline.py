from __future__ import annotations

import re
import unicodedata
from typing import List
from xml.sax.saxutils import escape as _xml_escape

_REPLACEMENTS = [
    ("âŠ•", " XOR "),
    ("âœ“", "OK"),
    ("âœ—", "NO"),
    ("â†”", "<->"),
    ("â‰ˆ", "~="),
    ("Â±", "+/-"),
    ("â€™", "'"),
    ("â€œ", '"'),
    ("â€", '"'),
    ("â†’", "->"),
    ("â‡ ", "->>"),
    ("â†£", "->>"),
    ("â†¦", "|->"),
    ("â‡’", "=>"),
    ("â‡”", "<=>"),
    ("âˆª", " U "),
    ("âˆ©", " âˆ© "),
    ("âŠ†", "âŠ†"),
    ("âŠ‡", "âŠ‡"),
    ("âˆˆ", "âˆˆ"),
    ("âˆ…", "âˆ…"),
    ("Ã—", "Ã—"),
    ("Â·", "Â·"),
    ("â€”", "-"),
    ("â€“", "-"),
    ("-", "-"),
    (" ", " "),
    ("â‹ˆ", "JOIN"),
    ("â¨", "JOIN"),
    ("â–·â—", "JOIN"),
    ("Ã·", "DIV"),
]

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_CODE_RE = re.compile(r"`([^`]+)`")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


def _normalize_unicode(text: str) -> str:
    out = unicodedata.normalize("NFKC", text or "")
    out = out.replace("\u200d", "")
    out = out.replace("\ufe0f", "")
    out = out.replace("\ufe0e", "")
    out = out.replace("\u200b", "")

    out = out.replace("ðŸŸ¢ OK", "OK")
    out = out.replace("ðŸŸ¡ WARN", "WARN")
    out = out.replace("ðŸ”´ CRIT", "CRIT")

    for old, new in _REPLACEMENTS:
        out = out.replace(old, new)

    emoji_map = {
        "ðŸŸ¢": "OK",
        "ðŸŸ¡": "WARN",
        "ðŸ”´": "CRIT",
        "âœ…": "OK",
        "âŒ": "NO",
        "âš ": "WARN",
        "â„¹": "INFO",
        "ðŸ’¡": "TIP",
    }
    for old, new in emoji_map.items():
        out = out.replace(old, new)

    out = re.sub(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]", "", out)
    return out


def _inline_rl(text: str) -> str:
    rendered = _xml_escape(_normalize_unicode(text))
    code_spans: List[str] = []

    def _stash_code(match: re.Match[str]) -> str:
        code_spans.append(match.group(1))
        return f"@@CODE{len(code_spans)-1}@@"

    rendered = _CODE_RE.sub(_stash_code, rendered)
    rendered = _BOLD_RE.sub(r"<b>\1</b>", rendered)
    rendered = _ITALIC_RE.sub(r"<i>\1</i>", rendered)

    for index, code in enumerate(code_spans):
        rendered = rendered.replace(f"@@CODE{index}@@", f'<font face="Courier">{code}</font>')
    return rendered


def sanitize_para(line: str) -> str:
    return re.sub(r"\s+", " ", _inline_rl(line)).strip()


def sanitize_code_line(line: str) -> str:
    rendered = _xml_escape(_normalize_unicode(line.rstrip("\n").replace("\t", "    ")))
    return rendered.replace(" ", "&nbsp;")


def sanitize_plain(text: str) -> str:
    return re.sub(r"\s+", " ", _normalize_unicode(text or "")).strip()
