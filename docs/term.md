# term/

`term/` centraliza la UX de terminal: colores, símbolos, tablas, flags comunes y “printers” de reportes.

Objetivo:

- Los comandos (`build`, `build_materia`, `scan`, `help`) imprimen siempre con el mismo estándar.
- La lógica funcional vive fuera de `term/` (en `engine/` y `format/`).

## 1) Componentes

- `term/flags.py`
  - define flags comunes para todos los comandos (`--quiet`, `--only-summary`, `--no-summary`, `-v/-vv`, `--no-color`, `--ascii`, `--log`, `--log-json`)
  - construye `Console` desde args (`console_from_args`)
  - define el modo de salida (`normal` | `only_summary` | `quiet`)

- `term/console.py`
  - wrapper de impresión con colores y logging a archivo (`--log`)
  - helpers de símbolos (`ok`, `warn`, `err`, `arrow`) y estilos

- `term/fmt.py`
  - helpers de formateo (truncado, padding)

- `term/style.py`
  - paleta ANSI y estilos consistentes

- `term/printers.py`
  - impresiones de alto nivel:
    - `print_help()`
    - `print_scan_report()`
    - `print_build_summary()`

## 2) Contrato de salida

Reglas estables:

- `--quiet` no imprime nada en OK; en error imprime mínimo.
- `--only-summary` imprime solo el resumen (sin detalle).
- `--no-summary` imprime detalle pero omite el resumen final.

Estas reglas se aplican igual en `build`, `build_materia` y `scan`.

## 3) Extender la CLI sin romper UX

Checklist para agregar un comando nuevo al paquete:

1) Implementar lógica funcional fuera de `term/`.
2) Reusar `add_common_flags()` del comando.
3) Usar `Console` para impresión.
4) Crear un printer nuevo en `term/printers.py` si el comando imprime reportes estructurados.
5) Actualizar `term/printers.py::print_help()` para listar el comando.
6) Documentar el comando en `docs/USAGE.md` y en `docs/INDEX.md`.
