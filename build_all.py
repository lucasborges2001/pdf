"""
Materia/Scripts/_pdf/build_all.py

Genera PDFs a partir de .txt en Practico/ y Taller/.

Convención:
  <Materia>/
    Practico/00Practico/00Practico.txt
    Taller/00Taller/00Taller.txt
    Scripts/_pdf/build_all.py

Header opcional (primera línea no vacía). No se imprime:
  [DOC key="value" include_toc=true toc_max_level=3 out="00PracticoResumen.pdf"]

Salida (copias):
  Por defecto copia TODOS los .pdf directo a: <Materia>/Resumenes/

Ejemplos:
  # Desde cualquier carpeta, pasando la Materia explícita
  python -m _pdf.build_all D:\ArqComp

  # Layout legacy (si _pdf está dentro de <Materia>/Scripts)
  python -m _pdf.build_all
  python3 -m _pdf.build_all
  python3 -m _pdf.build_all --area practico
  python3 -m _pdf.build_all --only 00 01
  python3 -m _pdf.build_all --strict
"""

from __future__ import annotations

import argparse
import os
import re
import shlex
import shutil
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union

from .framework import DocSpec, PdfCtx, PdfTheme, build_pdf
from .paths import find_materia_root, output_root, practico_dir, taller_dir
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


def _work_dirs(base: Path, keyword: str) -> List[Path]:
    if not base.is_dir():
        return []
    out: List[Path] = []
    for p in sorted(base.iterdir()):
        if not p.is_dir():
            continue
        name = p.name
        if name.startswith(".") or name in {"__pycache__", "_cache", "output", "_pdf"}:
            continue
        if len(name) >= 3 and name[:2].isdigit() and (keyword in name):
            out.append(p)
    return out


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


def _parse_doc_header(text: str) -> Tuple[Dict[str, Scalar], List[str], str]:
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


def _default_title(area_name: str, work_dir: Path) -> str:
    prefix = work_dir.name[:2] if work_dir.name[:2].isdigit() else ""
    area_label = "Práctico" if area_name.lower() == "practico" else "Taller"
    return f"{area_label} {prefix} — Resumen" if prefix else f"{area_label} — Resumen"


def _default_out_pdf(area_name: str, work_dir: Path, attrs: Dict[str, Scalar]) -> Path:
    v = attrs.get("out")
    if isinstance(v, str) and v.strip():
        p = (work_dir / v.strip())
    else:
        prefix = work_dir.name[:2] if work_dir.name[:2].isdigit() else ""
        name = f"{prefix}{area_name}Resumen.pdf" if prefix else f"{area_name}Resumen.pdf"
        p = work_dir / name
    return p if p.suffix.lower() == ".pdf" else p.with_suffix(".pdf")


def _resolve_pdf_factory(*, materia: Path, work_dir: Path):
    teo = materia / "Teorico"
    pra = materia / "Practico"
    tal = materia / "Taller"

    def resolve_pdf(filename: str) -> Path:
        candidates = [
            work_dir / filename,
            teo / filename,
            pra / filename,
            tal / filename,
            materia / filename,
        ]
        for p in candidates:
            if p.is_file():
                return p
        return candidates[0]

    return resolve_pdf


def _pick_txt_for_dir(work_dir: Path, *, area_name: str, pattern: str) -> Optional[Path]:
    prefix = work_dir.name[:2] if work_dir.name[:2].isdigit() else ""
    expected = f"{prefix}{area_name}.txt" if prefix else f"{area_name}.txt"
    p_exact = work_dir / expected
    if p_exact.is_file():
        return p_exact

    matches = sorted(work_dir.glob(pattern))
    return matches[0] if matches else None


def _build_from_txt(
    *,
    area_name: str,
    work_dir: Path,
    txt_path: Path,
    materia: Path,
    strict: bool,
) -> Tuple[bool, Optional[str], Optional[Path]]:
    try:
        raw = txt_path.read_text(encoding="utf-8", errors="replace")
        attrs, unknown, body = _parse_doc_header(raw)

        if unknown:
            msg = f"{txt_path.name}: claves DOC desconocidas: {', '.join(sorted(set(unknown)))}"
            if strict:
                return False, msg, None
            print(f"[WARN] {msg}")

        out_pdf = _default_out_pdf(area_name, work_dir, attrs)

        prefix = work_dir.name[:2] if work_dir.name[:2].isdigit() else ""
        default_footer_right = ("Práctico" if area_name.lower() == "practico" else "Taller") + (f" {prefix}" if prefix else "")

        spec = DocSpec(
            out_path=out_pdf,
            title=str(attrs.get("title") or _default_title(area_name, work_dir)),
            subtitle=str(attrs["subtitle"]) if isinstance(attrs.get("subtitle"), str) else None,
            meta_line=str(attrs["meta_line"]) if isinstance(attrs.get("meta_line"), str) else None,
            include_title_block=bool(attrs.get("include_title_block", True)),
            include_toc=bool(attrs.get("include_toc", True)),
            toc_title=str(attrs.get("toc_title") or "Contenido"),
            toc_max_level=int(attrs.get("toc_max_level", 3)) if isinstance(attrs.get("toc_max_level", 3), int) else 3,
            footer_left=str(attrs.get("footer_left") or "Lucas Borges"),
            footer_center=str(attrs.get("footer_center") or "Arquitectura de Computadoras"),
            footer_right=str(attrs.get("footer_right") or default_footer_right),
            footer_show_page=bool(attrs.get("footer_show_page", True)),
            footer_link_to_toc=bool(attrs.get("footer_link_to_toc", True)),
            author=str(attrs.get("author") or ""),
            subject=str(attrs.get("subject") or ""),
            keywords=str(attrs.get("keywords") or ""),
            system=str(attrs.get("system") or ""),
            contacto=str(attrs.get("contacto") or ""),
        )

        theme = PdfTheme()
        cache_dir = work_dir / "assets" / "_pdfpages"
        resolve_pdf = _resolve_pdf_factory(materia=materia, work_dir=work_dir)

        def content(ctx: PdfCtx):
            return txt_to_flowables(ctx, body, resolve_pdf=resolve_pdf, cache_dir=cache_dir)

        build_pdf(spec, content, theme)
        return True, None, out_pdf

    except Exception as e:
        return False, f"{type(e).__name__}: {e}", None


def _prepare_output_dir(out_dir: Path, *, clean: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if not clean:
        return
    for p in out_dir.glob("*.pdf"):
        try:
            p.unlink()
        except Exception as e:
            print(f"[WARN] no pude borrar '{p.name}': {type(e).__name__}: {e}")


def _copy_to_output_flat(*, pdf: Path, out_dir: Path) -> Tuple[bool, Optional[str], Optional[Path]]:
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        dst = out_dir / pdf.name
        shutil.copy2(pdf, dst)
        return True, None, dst
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", None


def build_area(
    *,
    area_name: str,   # "Practico" | "Taller"
    base: Path,
    only: Optional[Iterable[str]],
    txt_pattern: str,
    output: bool,
    out_dir: Optional[Path],
    strict: bool,
    materia: Path,
) -> Tuple[int, int, bool]:
    dirs = _work_dirs(base, area_name)

    only_set = {str(x).zfill(2) for x in only} if only else None

    any_error = False
    total_jobs = 0
    ok_jobs = 0

    print(f"\n=== {area_name} ===")
    for d in dirs:
        prefix = d.name[:2] if d.name[:2].isdigit() else None
        if only_set and (prefix not in only_set):
            continue

        txt_path = _pick_txt_for_dir(d, area_name=area_name, pattern=txt_pattern)
        if not txt_path:
            msg = f"{d.name}: no hay .txt que matchee '{txt_pattern}'"
            if strict:
                any_error = True
                print(f"[ERROR] {msg}")
            else:
                print(f"[skip] {msg}")
            continue

        total_jobs += 1
        ok, err, pdf = _build_from_txt(area_name=area_name, work_dir=d, txt_path=txt_path, materia=materia, strict=strict)

        if ok and pdf and pdf.exists():
            ok_jobs += 1
            print(f"[OK] {d.name} -> {pdf.name}")

            if output and out_dir:
                okc, errc, dst = _copy_to_output_flat(pdf=pdf, out_dir=out_dir)
                if not okc:
                    any_error = True
                    print(f"[ERROR] copy: {errc}")
                else:
                    print(f"     copy -> {dst.name}")
        else:
            any_error = True
            print(f"[ERROR] {d.name}: {err}")

    print(f"{area_name}: {ok_jobs}/{total_jobs} OK")
    return total_jobs, ok_jobs, any_error


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("materia_path", nargs="?", default=None,
                    help="Ruta a <Materia> (o a una subcarpeta dentro, ej: Practico/01Practico).")
    ap.add_argument("--materia", type=str, default=None,
                    help="Compat: Ruta a <Materia>. Recomendado usar el argumento posicional.")
    ap.add_argument("--area", type=str, choices=["practico", "taller", "both"], default="both")
    ap.add_argument("--only", nargs="*", default=None, help="Ej: --only 00 01 07")
    ap.add_argument("--txt-pattern", type=str, default=None, help="Glob de txt por carpeta. Default: *Practico.txt / *Taller.txt")
    ap.add_argument("--no-warn-missing-assets", action="store_true")
    ap.add_argument("--no-output", action="store_true")
    ap.add_argument("--output-dir", type=str, default=None, help="Default: <Materia>/Resumenes")
    ap.add_argument("--no-clean-output", action="store_true", help="Si NO está, borra *.pdf en Resumenes al inicio (una sola vez).")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()

    if not args.no_warn_missing_assets:
        os.environ.setdefault("PDF_WARN_MISSING_ASSETS", "1")

    start = Path(args.materia_path).resolve() if args.materia_path else (Path(args.materia).resolve() if args.materia else None)

    try:
        m = find_materia_root(start).resolve()
    except FileNotFoundError as e:
        raise SystemExit(f"[ERROR] {e}")
    out_root = Path(args.output_dir).resolve() if args.output_dir else output_root(m)

    do_output = not args.no_output
    clean_once = (not args.no_clean_output) and do_output

    # Clean SOLO una vez al principio
    if do_output:
        _prepare_output_dir(out_root, clean=clean_once)

    any_error = False
    total = 0
    ok = 0

    if args.area in {"practico", "both"}:
        t, k, err = build_area(
            area_name="Practico",
            base=practico_dir(m),
            only=args.only,
            txt_pattern=args.txt_pattern or "*Practico.txt",
            output=do_output,
            out_dir=out_root if do_output else None,
            strict=args.strict,
            materia=m,
        )
        total += t
        ok += k
        any_error = any_error or err

    if args.area in {"taller", "both"}:
        t, k, err = build_area(
            area_name="Taller",
            base=taller_dir(m),
            only=args.only,
            txt_pattern=args.txt_pattern or "*Taller.txt",
            output=do_output,
            out_dir=out_root if do_output else None,
            strict=args.strict,
            materia=m,
        )
        total += t
        ok += k
        any_error = any_error or err

    print(f"\nTOTAL: {ok}/{total} OK")
    raise SystemExit(1 if any_error else 0)


if __name__ == "__main__":
    main()
