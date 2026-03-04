# Mapa del repo y guía de navegación

Este documento define **dónde tocar** cuando necesitás cambiar algo del generador.

## 1) Si querés cambiar X, abrí Y

| Necesidad | Documento | Código
|---|---|---|
| Cambiar estilo visual (márgenes, fuentes, tamaños, colores) | `docs/runtime.md` | `runtime/core.py`, `runtime/ctx.py`
| Cambiar header/footer, TOC, layout de páginas | `docs/runtime.md` | `format/render.py`
| Cambiar el formato `.txt` (directivas, parsing, sanitización) | `docs/FORMAT.md` + `docs/format.md` | `format/txtfmt.py`
| Cambiar figuras/imágenes (`[FIG]`, `[IMG]`), escalado y cache | `docs/format.md` | `format/images.py`
| Cambiar resolución de assets (dónde se buscan PDFs/PNGs/JPGs) | `docs/engine.md` | `engine/assets.py`
| Cambiar cómo se parsea/valida el header `[DOC ...]` | `docs/engine.md` | `engine/docheader.py`
| Cambiar heurística de “.txt candidato”, scan y lint | `docs/engine.md` | `engine/scanlib.py`
| Cambiar descubrimiento de jobs por materia | `docs/engine.md` | `engine/materia.py`
| Cambiar flags, colores, tablas y formato de salida en terminal | `docs/term.md` | `term/*`
| Cambiar comandos CLI (`build`, `build_materia`, `scan`, `help`) | `docs/cli.md` | `build.py`, `build_materia.py`, `scan.py`, `help.py`
| Mantener scripts de Windows (PowerShell) | `docs/scripts.md` | `scripts/*.ps1`
| Mantener tests y coverage de cambios | `docs/tests.md` | `tests/*`

## 2) Arquitectura (pipeline)

Flujo de compilación (build):

1. CLI (`build.py` / `build_materia.py`) prepara inputs y flags.
2. `engine.compile.compile_txt()` ejecuta:
   - parse de header `[DOC ...]` (`engine/docheader.py`)
   - armado de resolvers de assets (`engine/assets.py`)
3. `format.txtfmt.txt_to_flowables()` parsea el `.txt` y produce Flowables de ReportLab.
4. `format.render.build_pdf()` arma el `BaseDocTemplate`, frames, TOC, header/footer y escribe el PDF.

Flujo de diagnóstico (scan/check):

1. CLI (`scan.py` o `build --check`) llama a `engine.scanlib.*`.
2. El lint valida:
   - balance de bloques (``` / ::: / [NOTE]...[/NOTE])
   - marcadores `[FIG]` / `[IMG]`
   - búsqueda de assets en roots calculados
3. La salida se imprime vía `term/printers.py`.

## 3) Responsabilidad por carpeta

| Carpeta | Rol | Contrato
|---|---|---|
| `docs/` | documentación del framework | describe el comportamiento real del código
| `engine/` | orquestación: scan, lint, docheader, assets, jobs | no genera layout; prepara inputs para `format/` + `runtime/`
| `format/` | parser del `.txt` + render del PDF | `docs/FORMAT.md` es la especificación del formato
| `runtime/` | tema + estilos + utilidades base | `PdfTheme` y `DocSpec` son el API del generador
| `term/` | salida de terminal y flags comunes | no toca compilación; solo UX de CLI
| `scripts/` | scripts operativos (Windows) | wrappers reproducibles para equipo
| `tests/` | suite de regresión | cambios de semántica ajustan tests
| `input/` | ejemplos mínimos para build simple | smoke tests manuales
| `output/` | artefactos del build simple | se regenera; no define comportamiento
