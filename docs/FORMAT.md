# format/

`format/` define el **lenguaje de marcado** del `.txt` y el **render** final del PDF.

Contrato principal:

- El formato del `.txt` está especificado en `docs/FORMAT.md`.
- El parser que implementa esa especificación es `format/txtfmt.py`.

## 1) Qué vive en esta carpeta

- `format/txtfmt.py`
  - parser del `.txt` → lista de Flowables de ReportLab
  - sanitización (unicode, inline: **bold**, *italic*, `code`)
  - reglas UX de paginado (saltos automáticos, CondPageBreak)
  - directivas: headings, listas, tablas, code fences, callouts, `[FIG]`, `[IMG]`

- `format/images.py`
  - construcción de figuras (imágenes) escaladas para entrar en el Frame
  - export de páginas de PDF a PNG (PyMuPDF) para `[FIG]`
  - funciones: `fig(...)`, `fig_pdf_page(...)`

- `format/render.py`
  - construcción del PDF (ReportLab `BaseDocTemplate`)
  - frames First/Later, header/footer, línea superior
  - TOC y outline/bookmarks

## 2) Reglas de paginado (UX)

Archivo: `format/txtfmt.py`

Constantes de política:

- `_TOP_LEVEL_STARTS_NEW_PAGE`: headings nivel 1 comienzan página nueva.
- `_EXERCISE_STARTS_NEW_PAGE`: headings que contienen “Ejercicio” comienzan página nueva.
- `_MIN_SPACE_BEFORE_*`: umbrales para insertar `CondPageBreak` antes de callouts/figuras/código.

Estas constantes definen estabilidad visual y evitan `LayoutError`.

## 3) Figuras e imágenes

### 3.1 `[FIG]` (página de PDF → PNG → figura)

- Parser: `format/txtfmt.py` reconoce `[FIG file="..." page=N ...]`.
- Render: `format/images.py::fig_pdf_page()` exporta la página (si falta el PNG) y genera el Flowable.
- Cache:
  - Se escribe un PNG en `assets/_pdfpages/<pdf_stem>/pNNN_zZ.png`.

### 3.2 `[IMG]` (imagen local)

- Parser: `format/txtfmt.py` reconoce `[IMG file="..." ...]`.
- Render: `format/images.py::fig()` escala la imagen al tamaño del frame.

Regla de mantenimiento:

La lógica de escalado debe garantizar que la figura **entra en el frame** (ancho y alto). Este módulo es el único lugar donde se corrige `LayoutError` por tamaño de imágenes.

## 4) Render del PDF

Archivo: `format/render.py`

Responsabilidades:

- Construir `story` (title block, TOC, contenido).
- Crear frames First/Later con alturas diferentes (`first_page_reserved_top` / `later_page_reserved_top`).
- Dibujar header/footer con `onPage`.
- Generar bookmarks y TOC entries en `afterFlowable`.

Regla de mantenimiento:

`format/render.py` define el layout global. Cambios de layout actualizan `docs/runtime.md` y se prueban con un build simple (`_pdf/input/*.txt`).

## 5) Cómo agregar una directiva nueva

Proceso estándar (en un solo PR):

1) Definir la sintaxis en `docs/FORMAT.md`.
2) Implementar parser en `format/txtfmt.py`:
   - agregar regex de marcador/bloque
   - parsear parámetros
   - traducir a Flowables usando la API de `runtime/ctx.py`
3) Actualizar lint en `engine/scanlib.py::lint_txt()`:
   - validar sintaxis
   - validar assets si aplica
4) Agregar tests en `tests/`:
   - parsing mínimo
   - balance de bloques
   - resolución de assets (si aplica)
5) Agregar un ejemplo ejecutable en `input/` y documentarlo en `docs/USAGE.md` cuando impacta al usuario.
