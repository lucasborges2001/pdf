# CLI (módulos de nivel raíz)

Los comandos del framework son módulos ejecutables con `python -m _pdf.<comando>`.

## 1) Comandos

### `help`

- Archivo: `help.py`
- Rol: imprime la lista de comandos y flags.
- No escanea ni compila.

### `build` (build simple)

- Archivo: `build.py`
- Fuente: `_pdf/input/*.txt`
- Destino: `_pdf/output/*.pdf`
- Modos:
  - `--check`: valida formato + assets (sin generar PDF)
  - `--clean`: borra output antes de compilar
  - `--materia` / `--search-dir`: ayudan a resolver assets cuando el input referencia PDFs/imagenes externas

### `build_materia` (build por materia)

- Archivo: `build_materia.py`
- Fuente: materia completa (recursivo)
- Destino:
  - `<Materia>/Resumenes/Practico/*.pdf`
  - `<Materia>/Resumenes/Taller/*.pdf`
- Modos:
  - `--check`: valida formato + assets (sin generar PDF)
  - `--area practico|taller|both`: filtra áreas
  - `--only 00 01 ...`: filtra jobs por prefijos en el path

### `scan` (lint)

- Archivo: `scan.py`
- Rol: diagnóstico rápido sin generar PDFs.
- Targets:
  - `--input`: escanea `_pdf/input/*.txt`
  - `--materia PATH`: escanea materia completa (recursivo)

## 2) Exit codes

- `0`: OK
- `1`: errores (o warnings cuando se usa `--strict`)
- `2`: parámetros inválidos o path inválido

## 3) Logging

Todos los comandos soportan:

- `--log <archivo>`: copia el output de terminal a un archivo (overwrite).
- `--log-json <archivo>`:
  - `scan` escribe un reporte JSON del lint.
  - `build --check` usa el mismo formato de reporte JSON.

El formato JSON se considera estable para consumo por scripts.
