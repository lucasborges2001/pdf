# runtime/

`runtime/` define el **API del generador**: tema (estilo visual), especificación del documento y un contexto (`PdfCtx`) con estilos y helpers para construir Flowables.

## 1) API pública

- `runtime/core.py`
  - `PdfTheme`: márgenes, fuentes, tamaños, colores, espaciados.
  - `DocSpec`: metadata del documento, TOC, assets (logo/icon) y footer.

- `runtime/ctx.py`
  - `PdfCtx`: construye estilos de ReportLab a partir de `PdfTheme`.
  - factories de Flowables: `p`, `hr`, `ul`, `ol`, `codeblock`, `table`, `callout`, `kv`, `fig`.

- `runtime/utils.py`
  - utilidades internas para color e imágenes (`hex_color`, `safe_draw_image`, etc.).

## 2) Cambios de estilo (tema)

Archivo: `runtime/core.py` (`PdfTheme`).

Cambios típicos:

- Márgenes y áreas reservadas:
  - `left_margin`, `right_margin`, `top_margin`, `bottom_margin`
  - `first_page_reserved_top`, `later_page_reserved_top`
- Tipografías y escala:
  - `body_font`, `body_size`, `body_leading`
  - `h1_size/h2_size/h3_size` y `*_leading`
- Paleta:
  - `text_color`, `muted_color`, `footer_color`, `line_color`, `accent_color`
- Callouts:
  - `callout_*`

Regla de mantenimiento:

Todo cambio de `PdfTheme` que afecte medidas se valida con un build de regresión que incluya:

1) una figura grande (`[IMG]` o `[FIG]`)
2) un codeblock largo
3) una tabla ancha

## 3) Cambios de estructura del documento (DocSpec)

Archivo: `runtime/core.py` (`DocSpec`).

`DocSpec` define:

- título/subtítulo y `meta_line`
- flags:
  - `include_title_block`
  - `include_toc`, `toc_title`, `toc_max_level`
- footer:
  - `footer_left`, `footer_center`, `footer_right`, `footer_show_page`, `footer_link_to_toc`
- metadata PDF:
  - `author`, `subject`, `keywords`
- assets:
  - `logo_left`, `icon_right`

Contrato:

Las claves del header `[DOC ...]` se mapean a campos de `DocSpec`. Toda clave nueva requiere actualización coordinada en `engine/docheader.py`, `docs/FORMAT.md` y tests.

## 4) Header/Footer y TOC

Archivo: `format/render.py`.

Este archivo define:

- la línea superior del header (`draw_header_line`)
- la lógica de header del primer page vs páginas siguientes
- el footer de 3 columnas (incluye link al TOC cuando `footer_link_to_toc=true` y `include_toc=true`)
- el TOC (ReportLab `TableOfContents`) y bookmarks (`afterFlowable`)

Regla de mantenimiento:

El layout del header/footer se considera parte del estándar visual del proyecto. Cambios de layout se validan con PDFs de ejemplo en `input/` y se documentan en este archivo.
