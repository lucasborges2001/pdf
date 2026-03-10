# Uso operativo del submódulo `pdf`

> **Objetivo**: documentar cómo ejecutar el submódulo y qué hace cada comando de CLI.

---

## 0) Convención de módulo

El código está en `pdf/`. Según cómo lo integres, el paquete puede invocarse como `pdf` o `_pdf`.

En los ejemplos se usa `<pkg>` para evitar ambigüedad:

- `python -m <pkg>.build`
- `python -m <pkg>.scan`

## 1) Comandos principales

### 1.1 Ayuda

```powershell
python -m <pkg>.help
```

### 1.2 Build simple (`input/*.txt` -> `output/*.pdf`)

```powershell
python -m <pkg>.build
python -m <pkg>.build --clean
python -m <pkg>.build --check
python -m <pkg>.build --check --strict
python -m <pkg>.build --materia D:\ArqComp --search-dir D:\assets
```

Comportamiento:

- Compilación normal: toma `pdf/input/*.txt` y genera `pdf/output/*.pdf`.
- `--check`: valida formato/markers y no genera PDFs.
- `--clean`: borra `pdf/output/` antes de compilar.
- `--materia` y `--search-dir`: agregan contexto para resolver assets en modo build.

### 1.3 Build por materia

```powershell
python -m <pkg>.build_materia --materia D:\ArqComp
python -m <pkg>.build_materia --materia D:\ArqComp --area practico
python -m <pkg>.build_materia --materia D:\ArqComp --area taller
python -m <pkg>.build_materia --materia D:\ArqComp --area teorico
python -m <pkg>.build_materia --materia D:\ArqComp --area both
python -m <pkg>.build_materia --materia D:\ArqComp --only 00 01 07
python -m <pkg>.build_materia --materia D:\ArqComp --check --strict
```

Comportamiento:

- Descubre `.txt` recursivamente en la materia (con exclusiones de carpetas técnicas).
- Genera salida en `<Materia>/Resumenes/<Area>/`.
- Además deja una copia junto al `.txt` origen.

### 1.4 Build recursivo por carpeta

```powershell
python -m <pkg>.build_carpeta --carpeta D:\repo\docs\tutoriales_cargadores
python -m <pkg>.build_carpeta --carpeta D:\repo\docs\tutoriales_cargadores --only crearUsuario
python -m <pkg>.build_carpeta --carpeta D:\repo\docs\tutoriales_cargadores --check --strict
```

Comportamiento:

- Recorre una carpeta arbitraria en forma recursiva.
- Genera cada PDF en la misma carpeta del `.txt`.
- `--only` filtra por nombre de carpeta o stem del archivo.

### 1.5 Scan/Lint (sin generar PDF)

```powershell
python -m <pkg>.scan --input
python -m <pkg>.scan --materia D:\ArqComp
python -m <pkg>.scan --materia D:\ArqComp --strict
python -m <pkg>.scan --materia D:\ArqComp --show-skipped
```

## 2) Flags comunes

Aplica a `build`, `build_materia`, `build_carpeta`, `scan` (y en parte `help`):

- `--quiet`
- `--only-summary`
- `--no-summary`
- `-v`, `-vv`
- `--no-color`
- `--ascii`
- `--log <archivo>`
- `--log-json <archivo>`
- `--max-issues <N>`
- `--show-skipped`
- `--max-skipped <N>`

## 3) Exit codes

- `0`: ejecución OK.
- `1`: errores de lint/build (o `WARN` en modo `--strict`).
- `2`: parámetros inválidos o ruta inválida (ejemplo: `--materia` inexistente).

## 4) Resolución de assets (`[FIG]` y `[IMG]`)

Orden de búsqueda real (`engine/assets.py`):

1) carpeta del `.txt`
2) rutas de `PDF_FIG_SEARCH_DIRS`
3) rutas repetidas en `--search-dir`
4) si hay `materia`: `Teorico/`, `Practico/`, `Taller/`, raíz de materia

Si no se encuentra el archivo:

- Scan/check: `WARN`.
- Build: puede omitir la figura o fallar según el caso concreto del render.

## 5) Descubrimiento de `.txt` en modo materia/carpeta

Exclusiones por defecto del scan recursivo:

- `Resumenes`
- `output`
- `__pycache__`
- `.git`
- `.venv`, `venv`
- `.mypy_cache`, `.pytest_cache`
- `Scripts`
- `_pdf`

Heurística de candidato (`scanlib._is_candidate_txt`): se lint-ea un `.txt` si detecta header `[DOC ...]` o tokens como `[FIG`, `[IMG`, `:::`, `[NOTE]`, `[WARN]`, `[TIP]`, `[PB]`.

## 6) Checklist de ejecución

- Verificar que el `.txt` cumple `docs/FORMAT.md`.
- Ejecutar `--check` antes de build masivo.
- Usar `--strict` para pipelines CI o validaciones de calidad.
- Si faltan assets, revisar rutas y `PDF_FIG_SEARCH_DIRS`.
