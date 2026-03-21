# Changelog de documentación y estructura

## 2026-03-21

- Se reorganizó el proyecto por capas reales: `cli/`, `parser/`, `pipeline/`, `render/`, `runtime/`, `term/`, `docs/`, `tests/`.
- `engine/` y `format/` quedaron como wrappers de compatibilidad y dejaron de ser la fuente de verdad.
- Se formalizó el contrato temprano del header `[DOC ...]`:
  - falta de header -> `ERROR`;
  - header inválido -> `ERROR`;
  - falta de `title` -> `ERROR`;
  - claves desconocidas -> `WARN` e ignoradas en build.
- Se eliminó la rotura tardía de `DocSpec.__init__(...) missing 'title'` mediante validación previa a `DocSpec`.
- Se desacopló parser/lint del render:
  - `parser/header.py` y `parser/inline.py` no dependen de ReportLab;
  - scan y discovery pueden testearse sin stack de render.
- Se corrigió la inconsistencia entre contratos internos:
  - `candidate_asset_roots` acepta `extra` y `extra_dirs`;
  - discovery expone inventario explícito (`all/candidates/skipped`);
  - build filtra claves DOC no soportadas en lugar de romper por kwargs inesperados.
- Se completó soporte de `[IMG ...]` en el parser de flowables con `width` como parámetro real.
- Se corrigió el discovery para aplicar exclusiones sobre paths relativos a la raíz escaneada y no sobre ancestros externos.
- Se alineó la suite de tests con la estructura nueva y con el comportamiento real del proyecto.
- Se actualizó `Makefile` para apuntar a comandos existentes y no a `build_all` inexistente.

## 2026-03-14

- Se restringió la detección de dot headings a numeración jerárquica real (`1.2. ...`, `2.1.3. ...`).
- Se agregó heurística para distinguir `1. Título` de listas ordenadas simples.

## 2026-03-11

- Se aclaró que el header `[DOC ...]` debe ir en la primera línea no vacía.
- Se documentó `title` como requisito funcional para evitar fallas tardías al construir el documento.
