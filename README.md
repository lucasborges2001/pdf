# _pdf — Framework de generación de PDFs (ReportLab)

Framework Python para convertir documentos `.txt` en PDFs consistentes (TOC, bloques, imágenes, tipografías y metadatos).

Este repo está pensado para estar **centralizado** (por ejemplo `D:\scripts\_pdf\`) y compilar:

- `_pdf/input/*.txt` → `_pdf/output/*.pdf` (**build simple**)
- `<Materia>/**` → `<Materia>/Resumenes/**` (**build por materia**, pasando la ruta)

Entrada recomendada para mantenimiento: `docs/INDEX.md`.

---

## Quickstart

Ejecutar desde la carpeta **padre** de `_pdf` (para que `python -m _pdf...` funcione):

```powershell
cd D:\scripts
python -m _pdf.help
python -m _pdf.build --check
python -m _pdf.build
python -m _pdf.build_materia --materia D:\ArqComp --check
python -m _pdf.build_materia --materia D:\ArqComp
```

Para más detalle operativo ver `docs/USAGE.md`.

---

## Requisitos

- Python 3.10+
- `reportlab` (y `pillow` si usás imágenes)

Instalación rápida (en venv):

```powershell
python -m venv .venv
.venv\Scripts\pip install -r _pdf\requirements.txt
```

---

## Uso

### Build simple (input → output)

```powershell
python -m _pdf.build
python -m _pdf.build --clean
python -m _pdf.build --check
python -m _pdf.build --check --strict
```

### Build por materia (materia → Resumenes)

```powershell
python -m _pdf.build_materia --materia D:\ArqComp
python -m _pdf.build_materia --materia D:\ArqComp --area practico
python -m _pdf.build_materia --materia D:\ArqComp --area taller
python -m _pdf.build_materia --materia D:\ArqComp --only 00 01
python -m _pdf.build_materia --materia D:\ArqComp --check --strict
```

### Scan (sin generar PDFs)

```powershell
python -m _pdf.scan --input
python -m _pdf.scan --materia D:\ArqComp --strict
```

---

## Flags comunes (salida)

- `--quiet`
- `--only-summary`
- `--no-summary`
- `-v` / `-vv`
- `--no-color`
- `--ascii`
- `--max-issues N`
- `--show-skipped`
- `--max-skipped N`
- `--log FILE`
- `--log-json FILE`

---

## Formato del `.txt`

La especificación de formato está en `docs/FORMAT.md`.

---

## Tests

```powershell
python -m unittest discover -s _pdf\tests
```

---

## JSON (CI)

Ejemplos:

```powershell
python -m _pdf.scan --materia D:\ArqComp --log-json D:\logs\scan.json
python -m _pdf.build --check --log-json D:\logs\check.json
python -m _pdf.build_materia --materia D:\ArqComp --check --log-json D:\logs\check_materia.json
```
