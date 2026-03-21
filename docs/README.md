# _pdf: arquitectura y mantenimiento

## Objetivo

Este proyecto compila `.txt` estructurados a PDF y se usa en dos contextos:

- material de facultad;
- informes, tutoriales y documentación operativa de trabajo.

La base quedó organizada por responsabilidades explícitas para que parser, pipeline, render y terminal puedan evolucionar sin contratos invisibles.

## Estructura canónica

- `cli/`: entrypoints reales de comandos.
- `parser/`: header `[DOC ...]`, sintaxis, saneado inline y parser del cuerpo.
- `pipeline/`: descubrimiento de `.txt`, resolución de assets, scan/lint, jobs y compilación.
- `render/`: integración con ReportLab e imágenes/figuras.
- `runtime/`: modelos compartidos (`DocSpec`, `PdfTheme`) y contexto PDF.
- `term/`: salida de consola, flags y formateo terminal.
- `docs/`: documentación centralizada.
- `tests/`: contratos de parser, discovery, lint y build.

## Compatibilidad

Las rutas viejas siguen existiendo como wrappers:

- `engine/` delega en `pipeline/` y `parser/`.
- `format/` delega en `parser/` y `render/`.
- `build.py`, `build_materia.py`, `build_carpeta.py`, `scan.py`, `help.py` delegan en `cli/`.

La fuente de verdad es la estructura nueva. Los wrappers viejos existen para no romper invocaciones existentes.

## Contratos principales

### Header

- El `.txt` debe empezar con `[DOC ...]` en la primera línea no vacía.
- `title` es obligatorio para build y lint.
- Header inválido y falta de `title` se detectan antes de construir `DocSpec`.
- Claves desconocidas se reportan como `WARN` y se ignoran al construir `DocSpec`.

### Parser

- `parser/header.py` es puro y no depende de ReportLab.
- `parser/inline.py` es puro y puede testearse sin dependencias de render.
- `parser/flowables.py` es la frontera entre parseo y render: recién ahí entra `PdfCtx` y ReportLab.

### Pipeline

- `pipeline/discovery.py` trabaja sobre paths relativos a la raíz escaneada.
- `pipeline/scan.py` comparte validaciones con el contrato del parser, no con internals privados de `format/`.
- `pipeline/compile.py` valida header antes de resolver `DocSpec` o tocar render.

## Reglas de mantenimiento

### Separación de responsabilidades

- Si un archivo mezcla parseo, heurística de discovery y render, está mal dividido.
- Si una función necesita ReportLab, no debe vivir en una capa pura de parser o discovery.
- Si una validación puede correr sin render, debe vivir en parser/pipeline, no en runtime/render.

### Tamaño de archivo

Partir un archivo cuando pase una de estas señales:

- mezcla dos capas distintas;
- supera aproximadamente 250-300 líneas y contiene más de un eje conceptual;
- necesita imports cruzados que obligan a conocer detalles internos de otro módulo;
- obliga a los tests a importar dependencias pesadas para validar lógica liviana.

### Dependencias

- `parser/` no debe depender de `render/`.
- `pipeline/` puede depender de `parser/` y `runtime/models`, pero debe evitar `runtime/ctx` salvo que ya esté entrando a render.
- `render/` puede depender de `runtime/` y `parser/inline`.
- `term/` no debe depender de parser/render.

## Errores y salida

- Build usa mensajes tempranos y concretos para header inválido o sin `title`.
- Scan distingue `ERROR` y `WARN`.
- `--strict` hace que los `WARN` afecten el exit code.
- La salida de consola se centraliza en `term/`.

## Testing

- `python -m unittest discover -s tests -v`

Notas:

- La suite está preparada para ejecutarse desde la raíz del repo.
- Los tests de parser/render basados en ReportLab se saltean si `reportlab` no está instalado.
- El resto de la suite valida parser/header/discovery/lint sin depender del stack de render.
