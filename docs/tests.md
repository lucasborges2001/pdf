# tests/

`tests/` es la suite de regresión del framework. Se ejecuta con `unittest`.

## 1) Cómo ejecutar

Desde la raíz del repo:

```bash
python -m unittest discover -s _pdf/tests
```

## 2) Cobertura esperada

Los tests cubren contratos de semántica:

- `test_docheader.py`: parse y validación del header `[DOC ...]`.
- `test_assets_resolution.py`: orden de búsqueda de assets.
- `test_lint_balance.py`: balance de bloques (``` / ::: / [NOTE]...[/NOTE]).
- `test_scan_candidates.py`: heurística de “.txt candidato”.

Regla de mantenimiento:

1) Todo cambio que toque semántica del formato (`format/txtfmt.py`) ajusta tests de lint.
2) Todo cambio en docheader o keys ajusta `test_docheader.py`.
3) Todo cambio de búsqueda de assets ajusta `test_assets_resolution.py`.
