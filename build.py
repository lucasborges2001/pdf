#!/usr/bin/env python3
"""
Scripts/_pdf/build.py

Versión simple del builder:
- Lee todos los .txt de: Scripts/_pdf/input/*.txt
- Genera PDFs en:       Scripts/_pdf/output/*.pdf

Soporta el mismo formato que build_all.py:
- Header opcional: [DOC key="value" ...]
- Directivas del txtfmt (TOC, headings, FIG, etc.)
- Resolución de PDFs para [FIG] igual que build_all (Teorico/Practico/Taller/Materia)
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from .framework import DocSpec, PdfCtx, PdfTheme, build_pdf
from .paths import find_materia_root
from .txtfmt import txt_to_flowables

Scalar = Union[str, bool, int]

_DOC_RE = re.compile(r"^\[DOC(?P<body>.*)\]\s*$")

_ALLOWED_DOC_KEYS = {
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
    # si viene con comillas, shlex ya las sacó; acá dejamos raw
    return s


def _parse_doc_header(text: str) -> Tuple[Dict[str, Scalar], List[str], str]:
    """
    Igual que build_all.py:
    - Busca la primera línea no vacía
    - Si es [DOC ...], la parsea (shlex)
    - Esa línea no se imprime en el PDF
    """
    lines = text.splitlines()
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines):
        return {}, [], text

    m = _DOC_RE.match(lines[i].strip())
    if not m:
        return {}, [], text

    body = (m.group("body") or "").strip()
    attrs: Dict[str, Scalar] = {}
    unknown: List[str] = []

    if body:
        for tok in shlex.split(body):
            if "=" not in tok:
                continue
            k, v = tok.split("=", 1)
            k = k.strip()
            attrs[k] = _parse_scalar(v)
            if k not in _ALLOWED_DOC_KEYS:
                unknown.append(k)

    rest = "\n".join(lines[:i] + lines[i + 1 :])
    return attrs, unknown, rest


def _resolve_pdf_factory(*, materia: Path, txt_dir: Path):
    """
    Misma idea que build_all.py:
    Permite que [FIG file="X.pdf"] encuentre PDFs en lugares típicos.
    """
    teo = materia / "Teorico"
    pra = materia / "Practico"
    tal = materia / "Taller"

    def resolve_pdf(filename: str) -> Path:
        candidates = [
            txt_dir / filename,
            teo / filename,
            pra / filename,
            tal / filename,
            materia / filename,
        ]
        for p in candidates:
            if p.is_file():
                return p
        return candidates[0]  # default si no existe (txtfmt decide warning)

    return resolve_pdf


def _default_out_pdf(*, output_dir: Path, txt_path: Path, attrs: Dict[str, Scalar]) -> Path:
    """
    - Si [DOC out="algo.pdf"] existe, lo respeta, PERO siempre bajo output_dir
    - Si no, usa el nombre del txt con .pdf
    """
    v = attrs.get("out")
    if isinstance(v, str) and v.strip():
        name = Path(v.strip()).name  # por si ponen rutas, sanitizamos a basename
        p = output_dir / name
    else:
        p = output_dir / txt_path.with_suffix(".pdf").name
    return p if p.suffix.lower() == ".pdf" else p.with_suffix(".pdf")


def build_one(
    *,
    txt_path: Path,
    output_dir: Path,
    strict: bool,
    materia: Path,
) -> Tuple[bool, Optional[str], Optional[Path]]:
    try:
        raw = txt_path.read_text(encoding="utf-8", errors="replace")
        attrs, unknown, body = _parse_doc_header(raw)

        if unknown:
            msg = f"{txt_path.name}: claves DOC desconocidas: {', '.join(sorted(set(unknown)))}"
            if strict:
                return False, msg, None
            print(f"[WARN] {msg}")

        out_pdf = _default_out_pdf(output_dir=output_dir, txt_path=txt_path, attrs=attrs)

        # Defaults razonables (no acoplados a Practico/Taller)
        spec = DocSpec(
            out_path=out_pdf,
            title=str(attrs.get("title") or txt_path.stem),
            subtitle=str(attrs["subtitle"]) if isinstance(attrs.get("subtitle"), str) else None,
            meta_line=str(attrs["meta_line"]) if isinstance(attrs.get("meta_line"), str) else None,
            include_title_block=bool(attrs.get("include_title_block", True)),
            include_toc=bool(attrs.get("include_toc", True)),
            toc_title=str(attrs.get("toc_title") or "Contenido"),
            toc_max_level=int(attrs.get("toc_max_level", 3)) if isinstance(attrs.get("toc_max_level", 3), int) else 3,
            footer_left=str(attrs.get("footer_left") or "Lucas Borges"),
            footer_center=str(attrs.get("footer_center") or ""),
            footer_right=str(attrs.get("footer_right") or ""),
            footer_show_page=bool(attrs.get("footer_show_page", True)),
            footer_link_to_toc=bool(attrs.get("footer_link_to_toc", True)),
            author=str(attrs.get("author") or ""),
            subject=str(attrs.get("subject") or ""),
            keywords=str(attrs.get("keywords") or ""),
            system=str(attrs.get("system") or ""),
            contacto=str(attrs.get("contacto") or ""),
        )

        theme = PdfTheme()

        # Cache local para [FIG ...] (páginas exportadas)
        cache_dir = output_dir / "_cache" / txt_path.stem
        resolve_pdf = _resolve_pdf_factory(materia=materia, txt_dir=txt_path.parent)

        def content(ctx: PdfCtx):
            return txt_to_flowables(ctx, body, resolve_pdf=resolve_pdf, cache_dir=cache_dir)

        build_pdf(spec, content, theme)
        return True, None, out_pdf

    except Exception as e:
        return False, f"{type(e).__name__}: {e}", None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--materia", type=str, default=None, help="Ruta a <Materia> (opcional). Si se omite, se intenta inferir desde CWD; si no, se usa input_dir.parent.")
    ap.add_argument("--input-dir", type=str, default=None, help="Default: Scripts/_pdf/input")
    ap.add_argument("--output-dir", type=str, default=None, help="Default: Scripts/_pdf/output")
    ap.add_argument("--clean", action="store_true", help="Borra *.pdf en output antes de compilar")
    ap.add_argument("--strict", action="store_true", help="Falla ante claves DOC desconocidas")
    ap.add_argument("--no-warn-missing-assets", action="store_true")
    args = ap.parse_args()

    if not args.no_warn_missing_assets:
        os.environ.setdefault("PDF_WARN_MISSING_ASSETS", "1")

    root = Path(__file__).resolve().parent
    input_dir = Path(args.input_dir).resolve() if args.input_dir else (root / "input")
    output_dir = Path(args.output_dir).resolve() if args.output_dir else (root / "output")

    if not input_dir.is_dir():
        raise SystemExit(f"[ERROR] input dir not found: {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    if args.clean:
        for p in output_dir.glob("*.pdf"):
            try:
                p.unlink()
            except Exception as e:
                print(f"[WARN] no pude borrar '{p.name}': {type(e).__name__}: {e}")

    txts = sorted(input_dir.glob("*.txt"))
    if not txts:
        print("[WARN] no hay .txt en input/")
        raise SystemExit(0)

    # Materia se usa sólo para que [FIG file="X.pdf"] pueda resolver PDFs típicos.
    if args.materia:
        materia = find_materia_root(Path(args.materia).resolve()).resolve()
    else:
        try:
            materia = find_materia_root().resolve()
        except FileNotFoundError:
            materia = input_dir.parent.resolve()


    any_error = False
    ok = 0
    for txt in txts:
        okb, err, pdf = build_one(txt_path=txt, output_dir=output_dir, strict=args.strict, materia=materia)
        if okb and pdf:
            ok += 1
            print(f"[OK] {txt.name} -> {pdf.name}")
        else:
            any_error = True
            print(f"[ERROR] {txt.name}: {err}")

    print(f"TOTAL: {ok}/{len(txts)} OK")
    raise SystemExit(1 if any_error else 0)


if __name__ == "__main__":
    main()
