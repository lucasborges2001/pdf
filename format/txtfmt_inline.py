from __future__ import annotations

import re
import unicodedata
from xml.sax.saxutils import escape as _xml_escape

_REPLACEMENTS = [
    ("⊕", " XOR "),
    ("✓", "OK"),
    ("✗", "NO"),
    ("↔", "<->"),
    ("≈", "~="),
    ("±", "+/-"),
    ("’", "'"),
    ("“", '"'),
    ("”", '"'),
    ("→", "->"),
    ("⇠", "->>"),
    ("↣", "->>"),
    ("↦", "|->"),
    ("⇒", "=>"),
    ("⇔", "<=>"),
    ("∪", " U "),
    ("∩", " ∩ "),
    ("⊆", "⊆"),
    ("⊇", "⊇"),
    ("∈", "∈"),
    ("∅", "∅"),
    ("×", "×"),
    ("·", "·"),
    ("—", "-"),
    ("–", "-"),
    ("-", "-"),
    (" ", " "),
    ("⋈", "JOIN"),
    ("⨝", "JOIN"),
    ("▷◁", "JOIN"),
    ("÷", "DIV"),
]

_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")
_CODE_RE = re.compile(r"`([^`]+)`")
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)")


def normalize_unicode(s: str) -> str:
    out = unicodedata.normalize("NFKC", s or "")
    out = out.replace("\u200d", "")
    out = out.replace("\ufe0f", "")
    out = out.replace("\ufe0e", "")
    out = out.replace("\u200b", "")
    out = out.replace("🟢 OK", "OK")
    out = out.replace("🟡 WARN", "WARN")
    out = out.replace("🔴 CRIT", "CRIT")
    for a, b in _REPLACEMENTS:
        out = out.replace(a, b)
    emoji_map = {
        "🟢": "OK",
        "🟡": "WARN",
        "🔴": "CRIT",
        "✅": "OK",
        "❌": "NO",
        "⚠": "WARN",
        "ℹ": "INFO",
        "💡": "TIP",
    }
    for a, b in emoji_map.items():
        out = out.replace(a, b)
    out = re.sub(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]", "", out)
    return out


def inline_rl(text: str) -> str:
    t = _xml_escape(normalize_unicode(text))
    t = _CODE_RE.sub(r'<font face="Courier">\1</font>', t)
    t = _BOLD_RE.sub(r"<b>\1</b>", t)
    t = _ITALIC_RE.sub(r"<i>\1</i>", t)
    return t


def sanitize_para(line: str) -> str:
    t = inline_rl(line)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def sanitize_code_line(line: str) -> str:
    t = _xml_escape(normalize_unicode(line.rstrip("\n").replace("\t", "    ")))
    return t.replace(" ", "&nbsp;")


def sanitize_plain(text: str) -> str:
    t = normalize_unicode(text or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t
