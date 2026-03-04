# engine/

`engine/` implementa la capa de **orquestación** del framework: descubre `.txt`, valida (scan/lint), resuelve assets y ejecuta la compilación.

## 1) Puntos de entrada

- Compilación de un `.txt`:
  - `engine/compile.py::compile_txt()`
- Scan/Lint (sin generar PDF):
  - `engine/scanlib.py::scan_input()`
  - `engine/scanlib.py::scan_materia()`
- Descubrimiento de jobs por materia:
  - `engine/materia.py::discover_jobs()`

## 2) Header `[DOC ...]` (parse y contrato)

Archivo: `engine/docheader.py`

Responsabilidad:

1) Detectar el header en la **primera línea no vacía**.
2) Parsear tokens `key=value` con semántica `shlex`.
3) Convertir escalares (bool/int/str) y devolver:
   - `attrs`: dict con claves parseadas
   - `unknown_keys`: lista de claves no reconocidas
   - `rest`: cuerpo del documento sin el header
   - `header_err`: string de error si el header es inválido

Regla de mantenimiento:

Cuando se agrega una nueva clave de documento (por ejemplo un nuevo campo en `DocSpec`), se actualizan en el mismo PR:

1) `engine/docheader.py` (allowlist y parsing)
2) `docs/FORMAT.md` (lista de claves)
3) tests en `tests/test_docheader.py`

## 3) Resolución de assets (PDF/IMG)

Archivo: `engine/assets.py`

Este módulo define:

- `candidate_asset_roots(...)`: orden de búsqueda de assets.
- `find_asset(name, roots)`: búsqueda por nombre (sin reescritura de path).

Orden de roots:

1) carpeta del `.txt`
2) roots típicos de la materia (cuando hay `materia=` o se infiere): `Teorico/`, `Practico/`, `Taller/`, raíz
3) directorios extra (`--search-dir` o variable `PDF_FIG_SEARCH_DIRS`)

Regla de compatibilidad:

El orden de búsqueda es parte del contrato del framework porque define qué archivo se incrusta si hay colisiones de nombres.
Todo cambio en el orden actualiza `docs/USAGE.md` y agrega un test en `tests/test_assets_resolution.py`.

## 4) Scan/Lint (diagnóstico)

Archivo: `engine/scanlib.py`

Responsabilidades:

- Descubrimiento recursivo de `.txt` (`discover_txts`) con exclusiones fijas (`Resumenes`, `output`, `__pycache__`, `.git`, `.venv`, etc.).
- Heurística de “candidato” (`_is_candidate_txt`): evita lint sobre `.txt` que no pertenecen al formato.
- Lint estructural (`lint_txt`): valida balance de bloques y sintaxis de marcadores.
- Validación de assets: verifica que `[FIG file=...]` y `[IMG file=...]` existan en los roots calculados.

Contrato del lint:

- ERROR rompe build/check (`exit code 1`).
- WARN no rompe por defecto; con `--strict` se considera error.

Cuando se agrega una directiva nueva en `format/txtfmt.py`, se agrega su validación en `lint_txt` para que el scan detecte errores antes de compilar.

## 5) Descubrimiento de jobs por materia

Archivo: `engine/materia.py`

`discover_jobs()`:

- Recorre la materia con `discover_txts()`.
- Clasifica el área según el path (`Practico`, `Taller`, `Teorico`, `Other`).
- Aplica filtros:
  - `--area practico|taller|both`
  - `--only 00 01 ...` (match por prefijo en cualquier parte del path)
- Determina el nombre de salida:
  - `out` desde header `[DOC out="..."]` cuando existe
  - o nombre por convención (si `Carpeta/Carpeta.txt` entonces `Carpeta.pdf`)
- Define el destino:
  - `<Materia>/Resumenes/Practico/`
  - `<Materia>/Resumenes/Taller/`

Regla de mantenimiento:

La definición de “job” se mantiene estable para permitir scripts del equipo (ej. CI que consume `--log-json`). Todo cambio de naming o rutas se refleja en `docs/USAGE.md`.
