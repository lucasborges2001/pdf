# Materia/Scripts/_pdf/txtfmt.py

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Any

from xml.sax.saxutils import escape as _xml_escape

from reportlab.platypus import PageBreak, CondPageBreak
from reportlab.platypus.paragraph import Paragraph

from .ctx import PdfCtx
from .images import fig_pdf_page

Flowable = Any

# ------------------------------
# UX policy (paginado)
# ------------------------------
_TOP_LEVEL_STARTS_NEW_PAGE = True     # headings nivel 1 (secciones mayores)
_EXERCISE_STARTS_NEW_PAGE = True      # headings que contienen "Ejercicio"

_MIN_SPACE_BEFORE_CALLOUT = 180       # puntos
_MIN_SPACE_BEFORE_FIG = 260           # puntos
_MIN_SPACE_BEFORE_CODE = 140          # puntos


def _last_is_pagebreak(story: List[Flowable]) -> bool:
    return bool(story) and isinstance(story[-1], PageBreak)


def _maybe_pagebreak(story: List[Flowable]) -> None:
    # no agregar PB si es el inicio o si ya hay PB
    if story and not _last_is_pagebreak(story):
        story.append(PageBreak())


def _needs_pagebreak_before_heading(level: int, title: str) -> bool:
    t = (title or "").lower()
    if _EXERCISE_STARTS_NEW_PAGE and "ejercicio" in t:
        return True
    if _TOP_LEVEL_STARTS_NEW_PAGE and level == 1:
        return True
    return False


# ------------------------------
# Marcadores
# ------------------------------

# [FIG file="..." page=... caption="..." zoom=2.0]
_FIG_RE = re.compile(
    r'^\[FIG\s+file="(?P<file>[^"]+)"\s+page=(?P<page>\d+)(?:\s+caption="(?P<caption>[^"]*)")?(?:\s+zoom=(?P<zoom>[\d.]+))?\s*\]\s*$'
)

# [PAGEBREAK] / [PB]
_PB_RE = re.compile(r'^\[(?:PAGEBREAK|PB)\]\s*$')

# [NOTE title="..."] ... [/NOTE]
# Kinds: NOTE|WARN|DANGER|INFO|TIP|CHECK
_CALLOUT_OPEN_RE = re.compile(
    r'^\[(?P<kind>NOTE|WARN|DANGER|INFO|TIP|CHECK)(?:\s+title="(?P<title>[^"]*)")?\]\s*$'
)
_CALLOUT_CLOSE_RE = re.compile(r'^\[/(?P<kind>NOTE|WARN|DANGER|INFO|TIP|CHECK)\]\s*$')

# :::def [title] ... :::  /  :::table ... :::
_BLOCK_OPEN_RE = re.compile(r"^:::(?P<kind>[A-Za-z0-9_-]+)(?:\s+(?P<title>.+))?\s*$")
_BLOCK_CLOSE_RE = re.compile(r"^:::\s*$")

# ```lang ... ```
_FENCE_OPEN_RE = re.compile(r'^\s*```(?P<lang>[A-Za-z0-9_+-]+)?\s*$')
_FENCE_CLOSE_RE = re.compile(r'^\s*```\s*$')

_HEADING_DOT_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)*)\.\s+(?P<title>.+)$")
_HEADING_BLOCK_RE = re.compile(r"^(?P<num>\d+(?:\.\d+)*)(?P<delim>[.)])\s+(?P<title>.+)$")


def parse_fig_marker(line: str) -> Optional[Tuple[str, int, Optional[str], float]]:
    m = _FIG_RE.match(line.strip())
    if not m:
        return None
    fn = m.group("file")
    page = int(m.group("page"))
    cap = m.group("caption")
    zoom = float(m.group("zoom")) if m.group("zoom") else 2.0
    return fn, page, cap, zoom


# ------------------------------
# Sanitización + formato inline
# ------------------------------

_REPLACEMENTS = [
    # Common symbols that standard PDF fonts may not render reliably
    ("⊕", " XOR "),
    ("✓", "OK"),
    ("✗", "NO"),
    ("↔", "<->"),
    ("≈", "~="),
    ("±", "+/-"),
    ("’", "'"),
    ("“", '"'),
    ("”", '"'),

    # Original mappings
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


def _normalize_unicode(s: str) -> str:
    # Normalización “safe” para PDF core fonts (Helvetica/Courier).
    # 1) normaliza compatibilidad
    out = unicodedata.normalize("NFKC", s or "")

    # 2) sacá joiners/variation selectors que rompen reemplazos
    out = out.replace("\u200d", "")   # ZWJ
    out = out.replace("\ufe0f", "")   # VS16 (emoji)
    out = out.replace("\ufe0e", "")   # VS15 (text)
    out = out.replace("\u200b", "")   # ZWSP

    # 3) reemplazos “frase” para no duplicar semántica (ej: "🟢 OK" -> "OK")
    out = out.replace("🟢 OK", "OK")
    out = out.replace("🟡 WARN", "WARN")
    out = out.replace("🔴 CRIT", "CRIT")

    # 4) reemplazos simples existentes
    for a, b in _REPLACEMENTS:
        out = out.replace(a, b)

    # 5) mapa de emojis frecuentes -> texto (sin perder info)
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

    # 6) fallback: cualquier emoji restante (rangos comunes) lo removemos
    out = re.sub(r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF]", "", out)
    return out



def _inline_rl(text: str) -> str:
    t = _xml_escape(_normalize_unicode(text))
    t = _CODE_RE.sub(r'<font face="Courier">\1</font>', t)
    t = _BOLD_RE.sub(r"<b>\1</b>", t)
    t = _ITALIC_RE.sub(r"<i>\1</i>", t)
    return t


def sanitize_para(line: str) -> str:
    t = _inline_rl(line)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def sanitize_code_line(line: str) -> str:
    t = _xml_escape(_normalize_unicode(line.rstrip("\n").replace("\t", "    ")))
    return t.replace(" ", "&nbsp;")


def sanitize_plain(text: str) -> str:
    """Sanitiza para strings planas (footer, etc.), sin XML escape."""
    t = _normalize_unicode(text or "")
    t = re.sub(r"\s+", " ", t).strip()
    return t



# ------------------------------
# Parsing estructura
# ------------------------------

def _is_rule(line: str, ch: str, min_len: int) -> bool:
    s = line.strip()
    return len(s) >= min_len and set(s) == {ch}


def _is_eq_rule(line: str) -> bool:
    return _is_rule(line, "=", 10)


def _is_dash_rule(line: str) -> bool:
    return _is_rule(line, "-", 5)


def _slugify(s: str) -> str:
    s = _normalize_unicode(s).lower().strip()
    s = re.sub(r"[^\w\s.-]", "", s)
    s = re.sub(r"[\s.]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s or "sec"


def _unique_key(base: str, used: Dict[str, int]) -> str:
    k = _slugify(base)
    n = used.get(k, 0)
    used[k] = n + 1
    return k if n == 0 else f"{k}-{n+1}"


def _mk_heading(ctx: PdfCtx, text: str, level: int, key: str, *, in_callout: bool) -> Flowable:
    # nivel 1 -> H2; nivel >=2 -> H3 (H1 lo maneja el title block del PDF)
    style = ctx.h2 if level <= 1 else ctx.h3
    html = f'<a name="{key}"/>{_inline_rl(text)}'
    p = ctx.p(html, style)
    setattr(p, "_fbd_key", key)
    # TOC/outline esperan niveles 0..; mapeamos 1->0, 2->1, ...
    setattr(p, "_fbd_level", max(0, int(level) - 1))
    setattr(p, "_fbd_is_heading", True)
    if in_callout:
        setattr(p, "_fbd_skip_toc", True)
        setattr(p, "_fbd_skip_outline", True)
    return p


def _condbreak(story: List[Flowable], min_space: int) -> None:
    """Si el flowable anterior es heading, movemos el CondPageBreak antes del heading."""
    if story and isinstance(story[-1], Paragraph) and bool(getattr(story[-1], "_fbd_is_heading", False)):
        h = story.pop()
        story.append(CondPageBreak(min_space))
        story.append(h)
    else:
        story.append(CondPageBreak(min_space))



_PIPE_SEP_CELL_RE = re.compile(r"^:?-{3,}:?$")


def _pipe_align_from_sep(cell: str) -> Optional[str]:
    c = cell.strip()
    if not _PIPE_SEP_CELL_RE.match(c):
        return None
    left = c.startswith(":")
    right = c.endswith(":")
    if left and right:
        return "CENTER"
    if right:
        return "RIGHT"
    if left:
        return "LEFT"
    return None


def _parse_pipe_table(body_lines: List[str]) -> Tuple[List[List[str]], Optional[List[Optional[str]]]]:
    raw_rows: List[List[str]] = []

    for ln in body_lines:
        s = ln.strip()
        if not s:
            continue
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip().strip("|").split("|")]
        raw_rows.append(cells)

    if not raw_rows:
        return [[""]], None

    aligns: Optional[List[Optional[str]]] = None
    if len(raw_rows) >= 2 and all(_PIPE_SEP_CELL_RE.match(c.strip()) for c in raw_rows[1]):
        aligns = [_pipe_align_from_sep(c) for c in raw_rows[1]]
        raw_rows.pop(1)

    rows = [[sanitize_para(c) for c in r] for r in raw_rows]
    if aligns is not None:
        # normalizar tamaño a ncols (por si el separador no coincide perfecto)
        ncols = max(len(r) for r in rows) if rows else len(aligns)
        aligns = (list(aligns) + [None] * max(0, ncols - len(aligns)))[:ncols]

    return rows, aligns


def txt_to_flowables(
    ctx: PdfCtx,
    text: str,
    *,
    resolve_pdf: Callable[[str], Path],
    cache_dir: Optional[Path] = None,
    default_zoom: float = 2.0,
    _used_keys: Optional[Dict[str, int]] = None,
    _in_callout: bool = False,
) -> List[Flowable]:
    lines = text.splitlines()
    story: List[Flowable] = []
    used_keys: Dict[str, int] = _used_keys if _used_keys is not None else {}

    def parse_block(block_lines: List[str], *, in_callout: bool = False) -> List[Flowable]:
        # IMPORTANTE: compartimos used_keys para evitar anchors duplicados en sub-bloques
        return txt_to_flowables(
            ctx,
            "\n".join(block_lines),
            resolve_pdf=resolve_pdf,
            cache_dir=cache_dir,
            default_zoom=default_zoom,
            _used_keys=used_keys,
            _in_callout=in_callout,
        )

    i = 0
    while i < len(lines):
        raw = lines[i].rstrip("\n")
        line = raw.strip()

        if not line:
            i += 1
            continue

        # PageBreak explícito
        if _PB_RE.match(line):
            story.append(PageBreak())
            i += 1
            continue

        # FIG marker
        fig = parse_fig_marker(line)
        if fig:
            fn, page, cap, zoom = fig
            pdf_path = resolve_pdf(fn)
            caption = cap or f"Fuente: {fn}, pág. {page}"
            _condbreak(story, _MIN_SPACE_BEFORE_FIG)
            story.extend(
                fig_pdf_page(
                    ctx,
                    pdf_path,
                    page,
                    caption=sanitize_para(caption),
                    cache_dir=cache_dir,
                    zoom=zoom or default_zoom,
                )
            )
            i += 1
            continue

        # ::: blocks (callouts y tablas)
        mb = _BLOCK_OPEN_RE.match(line)
        if mb:
            kind_raw = (mb.group("kind") or "").lower().strip()
            title = (mb.group("title") or "").strip() or None

            body_lines: List[str] = []
            i += 1
            while i < len(lines):
                raw2 = lines[i].rstrip("\n")
                if _BLOCK_CLOSE_RE.match(raw2.strip()):
                    break
                body_lines.append(raw2)
                i += 1

            # consume cierre si estaba
            if i < len(lines) and _BLOCK_CLOSE_RE.match(lines[i].strip()):
                i += 1

            # tabla
            if kind_raw == "table":
                rows, aligns = _parse_pipe_table(body_lines)
                story.append(ctx.table(rows, header=True, aligns=aligns))
                story.append(ctx.sp(6))
                continue

            # callout sugar
            kind_map = {
                "def": ("note", "Definición"),
                "ej": ("info", "Ejemplo"),
                "error": ("danger", "Error típico"),
                "tip": ("note", "Tip"),
                "warn": ("warn", "Atención"),
                "info": ("info", "Info"),
                "check": ("info", "Checklist"),
            }
            call_kind, default_title = kind_map.get(
                kind_raw,
                ("info", kind_raw.upper() if kind_raw else "Info"),
            )
            final_title = title or default_title
            body_flow = parse_block(body_lines, in_callout=True) if body_lines else [ctx.p("", ctx.base)]

            _condbreak(story, _MIN_SPACE_BEFORE_CALLOUT)
            story.append(ctx.callout(call_kind, final_title, body_flow))
            story.append(ctx.sp(10))
            continue

        # Callout block (legacy)
        mco = _CALLOUT_OPEN_RE.match(line)
        if mco:
            kind = mco.group("kind").lower()
            title = mco.group("title") or None

            body_lines2: List[str] = []
            i += 1
            while i < len(lines):
                raw2 = lines[i].rstrip("\n")
                line2 = raw2.strip()
                mclose = _CALLOUT_CLOSE_RE.match(line2)
                if mclose and mclose.group("kind").lower() == kind:
                    break
                body_lines2.append(raw2)
                i += 1

            # consume cierre si estaba
            if i < len(lines) and _CALLOUT_CLOSE_RE.match(lines[i].strip()):
                i += 1

            body_flow = parse_block(body_lines2, in_callout=True) if body_lines2 else [ctx.p("", ctx.base)]
            kmap = {
                "note": "note",
                "tip": "note",
                "warn": "warn",
                "danger": "danger",
                "info": "info",
                "check": "info",
            }
            _condbreak(story, _MIN_SPACE_BEFORE_CALLOUT)
            story.append(ctx.callout(kmap.get(kind, "info"), title, body_flow))
            story.append(ctx.sp(10))
            continue

        # ==== heading block
        if _is_eq_rule(line):
            if i + 2 < len(lines) and lines[i + 2].strip() and _is_eq_rule(lines[i + 2]):
                title_line = lines[i + 1].strip()
                mblk = _HEADING_BLOCK_RE.match(title_line)
                if mblk:
                    num = mblk.group("num")
                    delim = mblk.group("delim")
                    full = f"{num}{delim} {mblk.group('title')}"
                    lvl = 1 + num.count(".")
                    key = _unique_key(f"{num}-{mblk.group('title')}", used_keys)
                    if (not _in_callout) and _needs_pagebreak_before_heading(lvl, full):
                        _maybe_pagebreak(story)
                    story.append(_mk_heading(ctx, full, lvl, key, in_callout=_in_callout))
                else:
                    lvl = 1
                    key = _unique_key(title_line, used_keys)
                    if (not _in_callout) and _needs_pagebreak_before_heading(lvl, title_line):
                        _maybe_pagebreak(story)
                    story.append(_mk_heading(ctx, title_line, lvl, key, in_callout=_in_callout))
                i += 3
                continue

            story.append(ctx.hr(space_before=6, space_after=8))
            i += 1
            continue

        # ---- hr
        if _is_dash_rule(line):
            story.append(ctx.hr(space_before=6, space_after=8))
            i += 1
            continue

        # 1. / 1.2.
        mh = _HEADING_DOT_RE.match(line)
        if mh:
            num = mh.group("num")
            full = f"{num}. {mh.group('title')}"
            lvl = 1 + num.count(".")
            key = _unique_key(f"{num}-{mh.group('title')}", used_keys)
            if (not _in_callout) and _needs_pagebreak_before_heading(lvl, full):
                _maybe_pagebreak(story)
            story.append(_mk_heading(ctx, full, lvl, key, in_callout=_in_callout))
            i += 1
            continue

        # fenced code
        mf = _FENCE_OPEN_RE.match(raw)
        if mf:
            lang = (mf.group("lang") or "").strip()
            block: List[str] = []
            i += 1
            while i < len(lines) and not _FENCE_CLOSE_RE.match(lines[i]):
                block.append(sanitize_code_line(lines[i]))
                i += 1
            if i < len(lines) and _FENCE_CLOSE_RE.match(lines[i]):
                i += 1
            title = f"Código{f' ({lang})' if lang else ''}"
            _condbreak(story, _MIN_SPACE_BEFORE_CODE)
            story.append(ctx.codeblock(block, title=title))
            continue

        # UL
        if raw.lstrip().startswith(("- ", "* ", "• ")):
            items: List[str] = []
            while i < len(lines):
                r2 = lines[i].rstrip("\n")
                s2 = r2.lstrip()
                if not s2.startswith(("- ", "* ", "• ")):
                    break
                items.append(sanitize_para(s2[2:]))
                i += 1
            story.append(ctx.ul(items))
            continue

        # OL
        if re.match(r"^\d+[.)]\s+", line):
            items2: List[str] = []
            while i < len(lines):
                mm = re.match(r"^\d+[.)]\s+(.*)$", lines[i].strip())
                if not mm:
                    break
                items2.append(sanitize_para(mm.group(1)))
                i += 1
            story.append(ctx.ol(items2))
            continue

        # indented code
        if raw.startswith("    ") or raw.startswith("\t"):
            block2: List[str] = []
            while i < len(lines):
                r2 = lines[i].rstrip("\n")
                if not (r2.startswith("    ") or r2.startswith("\t")):
                    break
                r2 = r2[4:] if r2.startswith("    ") else r2[1:]
                block2.append(sanitize_code_line(r2))
                i += 1
            _condbreak(story, _MIN_SPACE_BEFORE_CODE)
            story.append(ctx.codeblock(block2, title="Procedimiento"))
            continue

        # paragraph (acumula)
        parts: List[str] = [sanitize_para(line)]
        i += 1
        while i < len(lines):
            peek_raw = lines[i].rstrip("\n")
            peek = peek_raw.strip()
            if not peek:
                break
            if _PB_RE.match(peek):
                break
            if parse_fig_marker(peek):
                break
            if _BLOCK_OPEN_RE.match(peek):
                break
            if _CALLOUT_OPEN_RE.match(peek):
                break
            if _is_eq_rule(peek) or _is_dash_rule(peek):
                break
            if _HEADING_DOT_RE.match(peek):
                break
            if _FENCE_OPEN_RE.match(peek_raw):
                break
            if peek_raw.lstrip().startswith(("- ", "* ", "• ")):
                break
            if re.match(r"^\d+[.)]\s+", peek):
                break
            if peek_raw.startswith("    ") or peek_raw.startswith("\t"):
                break
            parts.append(sanitize_para(peek))
            i += 1

        story.append(ctx.p(" ".join(parts)))
        i += 1

    return story
