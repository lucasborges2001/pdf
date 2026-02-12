# _pdf — Framework de generación de PDFs (ReportLab)

Framework Python para convertir documentos `.txt` en PDFs consistentes (TOC, bloques, imágenes, tipografías y metadatos), pensado para vivir dentro de una materia/proyecto con esta estructura:

```
<Materia>/
  Practico/
  Taller/
  Resumenes/
  Scripts/
    _pdf/   <-- este repo
```

> Nota: este framework está diseñado para ejecutarse desde `<Materia>/Scripts` (el padre de `_pdf`).

## Requisitos

- Python 3.10+
- `reportlab` (y `pillow` si usás imágenes)

Instalación rápida:

```bash
python -m venv .venv
# Windows
.venv\Scripts\pip install -r _pdf\requirements.txt
# Linux/Mac
.venv/bin/pip install -r _pdf/requirements.txt
```

## Uso

Desde `<Materia>/Scripts`:

```bash
python -m _pdf.build_all
```

Atajos útiles:

```bash
python -m _pdf.build_all --area practico
python -m _pdf.build_all --area taller
python -m _pdf.build_all --only 00 01
python -m _pdf.build_all --strict
```

## Formato del `.txt`

La especificación de formato está en `docs/FORMAT.md`.

## Desarrollo

- `make -C _pdf help` (si tenés GNU Make)
- Scripts PowerShell en `scripts/`.

