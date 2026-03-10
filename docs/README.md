# Documentación mínima del submódulo `pdf`

> **Objetivo**: dejar una base corta, útil y mantenible para operar el submódulo sin depender de documentación histórica ni archivos gigantes.

---

## 0) Principios

1) Un archivo por responsabilidad.
2) Fuente de verdad: el código actual (`pdf/*`).
3) Todo en español.
4) Cambios funcionales se reflejan en estas guías en el mismo PR.

## 1) Archivos oficiales de `pdf/docs`

- `FORMAT.md`: contrato del formato `.txt` (directivas, bloques, inline y validaciones).
- `USAGE.md`: uso de CLI (`build`, `build_materia`, `build_carpeta`, `scan`) y flags.
- `CHANGELOG.md`: cambios puntuales de esta documentación.

## 2) Mapa rápido de código

- Parseo del `.txt`: `pdf/format/txtfmt.py`
- Render final a PDF: `pdf/format/render.py`
- Parseo del header `[DOC ...]`: `pdf/engine/docheader.py`
- Lint/scan: `pdf/engine/scanlib.py`
- Resolución de assets: `pdf/engine/assets.py`
- Compilación de un `.txt`: `pdf/engine/compile.py`

## 3) Regla de mantenimiento

- Si cambia el contrato del `.txt`, actualizar `FORMAT.md`.
- Si cambia CLI o flujo operativo, actualizar `USAGE.md`.
- Si se agrega o elimina documentación en esta carpeta, registrar el cambio en `CHANGELOG.md`.
