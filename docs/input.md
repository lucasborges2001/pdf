# input/

`input/` contiene documentos `.txt` de ejemplo para el **build simple**.

Contrato:

- Estos `.txt` se compilan con `python -m _pdf.build`.
- Sirven como smoke test manual del render (TOC, headings, tablas, callouts, figuras, código).
- Cada ejemplo cubre una feature del formato.

Regla de mantenimiento:

Cuando se modifica el formato o el layout, se actualizan estos ejemplos para que ejerzan el cambio y permitan validar el resultado en PDF.
