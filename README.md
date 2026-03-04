# _pdf — Framework de generación de PDFs (ReportLab)

Framework Python para convertir documentos `.txt` en PDFs consistentes (TOC, bloques, imágenes, tipografías y metadatos).

Este repo está pensado para estar **centralizado** (por ejemplo `D:\Scripts\_pdf\`) y compilar tanto:

- `_pdf/input/*.txt` → `_pdf/output/*.pdf` (build simple)
- `<Materia>/**` → `<Materia>/Resumenes/**` (build por materia)

## Quickstart

```bash
python -m _pdf.help
python -m _pdf.build --check
python -m _pdf.build
python -m _pdf.build_materia D:\ArqComp --check
python -m _pdf.build_materia D:\ArqComp
```

Para más detalles ver `docs/USAGE.md`.

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


### Flags de salida (comunes)

- `--quiet`
- `--only-summary`
- `--no-summary`
- `-v` / `-vv`
- `--no-color`
- `--ascii`


### Guardar salida de terminal

Podés agregar `--log <archivo>` a cualquier comando para guardar el output en un archivo.


## Tests

Ejecutar suite mínima:

```powershell
python -m unittest discover -s _pdf/tests
```


## JSON (CI)

Para scan/check:

```powershell
python -m _pdf.scan --materia D:\ArqComp --log-json D:\logs\scan.json
python -m _pdf.build --check --log-json D:\logs\check.json
```
