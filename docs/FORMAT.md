# Formato `.txt` aceptado por el submódulo `pdf`

> **Objetivo**: definir el contrato funcional del archivo `.txt` que el submódulo necesita para compilar a PDF.

---

## 0) Alcance

- Este documento describe lo que el parser acepta hoy (`pdf/format/txtfmt.py`).
- La compilación depende del header `[DOC ...]` parseado por `pdf/engine/docheader.py`.
- El lint/check se ejecuta en `pdf/engine/scanlib.py`.

## 1) Estructura base del archivo

1) La primera línea no vacía debe ser un header `[DOC ...]` válido.
2) El resto del archivo es el cuerpo del documento.
3) Los bloques se separan con líneas en blanco.
4) Líneas de texto normal consecutivas se concatenan en un mismo párrafo.

## 2) Header `[DOC ...]`

### 2.1 Sintaxis

```txt
[DOC title="Práctico 01" include_toc=true toc_max_level=2 footer_right="P1"]
```

Reglas:

- Debe estar en una sola línea.
- Se parsea como pares `clave=valor`.
- Si un valor tiene espacios, usar comillas dobles.
- Booleanos: `true`/`false`.
- Enteros: `-1`, `0`, `3`, etc.

### 2.2 Claves aceptadas

| Clave | Tipo | Default | Uso |
|---|---|---|---|
| `title` | string | sin default | Título del documento. Obligatorio para compilar. |
| `out` | string | `<txt_stem>.pdf` | Nombre del PDF de salida. |
| `subtitle` | string | `None` | Subtítulo del bloque de título. |
| `meta_line` | string | `None` | Línea chica debajo del título. |
| `include_title_block` | bool | `true` | Muestra/oculta bloque inicial de título. |
| `include_toc` | bool | `false` | Activa índice (TOC). |
| `toc_title` | string | `Contenido` | Título del TOC. |
| `toc_max_level` | int | `3` | Profundidad máxima de TOC/outline. |
| `footer_left` | string | `Lucas Borges` | Texto de pie de página izquierdo. |
| `footer_center` | string | `Arquitectura de Computadoras` | Texto de pie de página centro. |
| `footer_right` | string | `""` | Texto de pie de página derecho. |
| `footer_show_page` | bool | `true` | Agrega número de página en footer derecho. |
| `footer_link_to_toc` | bool | `true` | Link del centro del footer al TOC (si hay TOC). |
| `author` | string | `""` | Metadata PDF. |
| `subject` | string | `""` | Metadata PDF. |
| `keywords` | string | `""` | Metadata PDF. |
| `system` | string | `""` | Campo legacy de compatibilidad. |
| `contacto` | string | `""` | Campo legacy de compatibilidad. |

### 2.3 Validaciones de header

- Claves desconocidas: el scan las marca como `WARN`.
- Claves desconocidas en build: pueden romper compilación (argumento no soportado por `DocSpec`).
- Header mal formado (ejemplo: comillas sin cerrar): `ERROR`.

## 3) Bloques y directivas

### 3.1 Salto de página manual

```txt
[PB]
[PAGEBREAK]
```

### 3.2 Títulos y secciones

Formato en línea (dot heading):

```txt
1. Introducción
1.2. Memoria caché
2.1.3. Políticas de escritura
```

Formato en bloque con reglas de `=`:

```txt
==========
1) Tema principal
==========
```

Reglas:

- La regla de `=` debe tener al menos 10 caracteres.
- Se inserta salto de página automático antes de títulos de nivel 1.
- Si el título contiene `Ejercicio`, también fuerza salto de página.

### 3.3 Separadores

```txt
-----
==========
```

- `-----` (5 o más `-`) crea línea horizontal.
- `==========` (10 o más `=`) crea línea horizontal si no forma bloque de título.

### 3.4 Código

Bloque fenced:

````txt
```c
int main() { return 0; }
```
````

Bloque indentado (4 espacios o tab):

```txt
    MOV AX, BX
    ADD AX, 1
```

### 3.5 Listas

No ordenada:

```txt
- item
* item
• item
```

Ordenada:

```txt
1) item
2. item
```

### 3.6 Callouts

Sintaxis recomendada:

```txt
:::def
Texto...
:::
```

Mapa de `kind`:

| `kind` | Estilo | Título default |
|---|---|---|
| `def` | note | Definición |
| `ej` | info | Ejemplo |
| `error` | danger | Error típico |
| `tip` | note | Tip |
| `warn` | warn | Atención |
| `info` | info | Info |
| `check` | info | Checklist |

Compatibilidad legacy:

```txt
[NOTE title="Definición"]
Texto...
[/NOTE]
```

KIND legacy válidos: `NOTE`, `WARN`, `DANGER`, `INFO`, `TIP`, `CHECK`.

### 3.7 Tablas

```txt
:::table
| Columna | Valor |
|--------:|:-----:|
| A       |  10   |
:::
```

Reglas:

- Solo se consideran filas que empiecen con `|`.
- La segunda fila puede definir alineación (`:---`, `---:`, `:---:`).
- No hay escape de `|` dentro de celdas.

### 3.8 Figuras e imágenes

Página de PDF (`[FIG]`):

```txt
[FIG file="teorico.pdf" page=3 caption="Jerarquía" zoom=2.0]
```

Imagen (`[IMG]`):

```txt
[IMG file="diagrama.png" caption="Esquema" max_w=420 max_h=260]
```

Reglas:

- `file` es obligatorio.
- En `[FIG]`, `page` es obligatorio y 1-based.
- En `[FIG]`, `zoom` debe ser mayor a 0.
- Si el asset no se encuentra, el scan marca `WARN`.

## 4) Formato inline

Se soporta:

- Negrita: `**texto**`
- Cursiva: `*texto*`
- Código inline: `` `texto` ``
- Link markdown: `[label](https://ejemplo.com)`
- URL plana: `https://ejemplo.com`
- Color inline: `[color=#2563EB]texto[/color]` o `[c=blue]texto[/c]`

Comportamiento relevante:

- Dentro de `` `...` `` no se aplica negrita/cursiva/color/link.
- El HTML libre no se interpreta (el parser escapa contenido).
- Símbolos Unicode y emojis se normalizan para mantener compatibilidad de fuentes PDF.

## 5) Reglas de lint/check

El lint detecta, entre otros:

- Fence de código abierto sin cierre o cierre sin apertura (`ERROR`).
- Bloques `:::` abiertos/cerrados incorrectamente (`ERROR`).
- Callouts legacy mal cerrados (`ERROR`).
- Marcadores `[FIG]`/`[IMG]` inválidos (`ERROR`).
- `[FIG]` con `page < 1` o `zoom <= 0` (`ERROR`).
- Asset faltante en `[FIG]` o `[IMG]` (`WARN`).
- Claves DOC desconocidas (`WARN`).

Con `--strict`, los `WARN` cuentan como error de salida.

## 6) Plantilla mínima recomendada

```txt
[DOC title="Resumen base" include_toc=true toc_max_level=2]

==========
1) Objetivo
==========

:::def
Definición corta.
:::

1.1. Ejemplo

- Punto A
- Punto B

[IMG file="esquema.png" caption="Diagrama general" max_w=420]
```

## 7) Checklist operativo

- Header `[DOC ...]` válido en primera línea no vacía.
- `title` definido en header.
- Bloques `:::` y fences ``` cerrados.
- Marcadores `[FIG]` y `[IMG]` con sintaxis exacta.
- Assets disponibles en rutas de búsqueda.
