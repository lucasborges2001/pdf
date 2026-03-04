# Changelog

## 0.3.1 - 2026-03-04
- Fix: lint de fences ``` (el cierre ``` también matcheaba como apertura).
- Build materia: `--area` soporta `teorico|practico|taller|both|all` (default `all`) y el output se organiza por carpeta.
- Scan materia: excluye por defecto `Scripts/` y `_pdf/` (setup viejo con repo embebido en materias).

## 0.3.0 - 2026-03-04
- Refactor: controladores CLI en raíz y lógica reusable en subpaquetes (`engine/`, `format/`, `runtime/`).
- UX: salida de terminal centralizada en `term/` (help bonito, tablas, colores opcionales).
- Scan/Check: `scan` + `--check` reutilizan `engine.scanlib` y soportan `--show-skipped`, `--max-issues`, `--max-skipped`.
- Logging: `--log` (tee) y `--log-json` (reporte estructurado para scan/check).
- Flags comunes: `--quiet`, `--only-summary`, `--no-summary`, `-v/-vv`, `--no-color`, `--ascii`.
