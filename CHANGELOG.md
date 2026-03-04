# Changelog

## 0.3.0 - 2026-03-04
- Refactor: controladores CLI en raíz y lógica reusable en subpaquetes (`engine/`, `format/`, `runtime/`).
- UX: salida de terminal centralizada en `term/` (help bonito, tablas, colores opcionales).
- Scan/Check: `scan` + `--check` reutilizan `engine.scanlib` y soportan `--show-skipped`, `--max-issues`, `--max-skipped`.
- Logging: `--log` (tee) y `--log-json` (reporte estructurado para scan/check).
- Flags comunes: `--quiet`, `--only-summary`, `--no-summary`, `-v/-vv`, `--no-color`, `--ascii`.
