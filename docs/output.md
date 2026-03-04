# output/

`output/` contiene PDFs generados por el **build simple** (`python -m _pdf.build`).

Contrato:

- Estos archivos son artefactos regenerables.
- No se editan a mano.
- Si se versionan, se versionan para:
  - tener snapshots comparables de layout
  - facilitar revisión visual en PRs

Regla de mantenimiento:

Cuando el PR cambia layout/estilo/formato, se regenera `output/` con `python -m _pdf.build` y se commitea el diff si el repo utiliza snapshots.
