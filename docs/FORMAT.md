# format/format.md — Formato de documentos `.txt` para `_pdf`

Este documento especifica **el formato exacto** de los `.txt` que el framework `_pdf` puede renderizar a PDF.
La idea es que con **solo este archivo** cualquiera pueda escribir un `.txt` válido, entender cómo se interpreta,
y predecir el PDF resultante sin mirar el código.

> Fuente de verdad: el parser `Scripts/_pdf/txtfmt.py` y los builders `Scripts/_pdf/build_all.py` / `Scripts/_pdf/build.py`.

---

## 1) Conceptos clave (modelo mental)

Un `.txt` se procesa como una secuencia de **bloques**. El parser recorre línea a línea y decide:

- **Marcadores**: líneas especiales (ej. `[PB]`, `[FIG ...]`, `:::def`, ``` ```).
- **Bloques estructurados**: headings, listas, tablas, callouts, código.
- **Párrafos**: cualquier línea “normal” (no-marcador). Varias líneas normales seguidas se **unen** en un solo párrafo.

Separación:
- Una **línea en blanco** separa bloques.
- Las líneas se consideran por su `strip()` en la mayoría de los casos (espacios al inicio/fin suelen ignorarse para detectar marcadores).

---

## 2) Dónde vive el `.txt` y cómo se compila (dos builders)

### 2.1 Builder “materia” (Práctico/Taller): `build_all`
Convención típica:
```
<Materia>/
  Practico/
    00Practico/00Practico.txt
  Taller/
    00Taller/00Taller.txt
  Teorico/
    TxxAlgo.pdf
  Scripts/_pdf/
```

Se ejecuta desde `<Materia>/Scripts`:
- Todo: `python3 -m _pdf.build_all`
- Solo prácticos: `python3 -m _pdf.build_all --area practico`
- Solo algunos: `python3 -m _pdf.build_all --only 00 01 07`
- Estricto (falla con claves DOC desconocidas): `python3 -m _pdf.build_all --strict`

Salida:
- Genera el PDF dentro de cada carpeta (`00PracticoResumen.pdf`, etc.)
- Luego copia “plano” a `<Materia>/Resumenes/` (por defecto) y limpia una sola vez al inicio (salvo `--no-clean-output`).

### 2.2 Builder simple (input/output): `build`
Convención:
```
Scripts/_pdf/input/*.txt  ->  Scripts/_pdf/output/*.pdf
```

Se ejecuta:
- `python3 -m _pdf.build`
- Opcional: `--clean`, `--strict`, `--input-dir`, `--output-dir`

---

## 3) Header opcional `[DOC ...]` (metadata + configuración)

### 3.1 Qué es
La **primera línea no vacía** del archivo puede ser un header DOC:

- Se parsea.
- **No se imprime** en el PDF.
- Ajusta título, TOC, footer, output, metadata, etc.

Ejemplo:
```
[DOC out="00PracticoResumen.pdf" title="Práctico 00 — Resumen" subtitle="Arquitectura de Computadoras" include_toc=true toc_max_level=3 footer_right="Práctico 00"]
```

### 3.2 Sintaxis exacta
- Debe estar en **una sola línea**.
- Forma: `[DOC key=value key=value ...]`
- Se parsea con `shlex`: si un valor tiene espacios, **usá comillas**.

Ejemplos válidos:
- `include_toc=true`
- `toc_max_level=3`
- `title="Práctico 02 — Memorias"`
- `out=02PracticoResumen.pdf`

Tipos:
- bool: `true|false` (case-insensitive)
- int: `123`, `-5`
- string: todo lo demás

### 3.3 Claves permitidas (lista completa)
Estas son las **únicas** claves aceptadas:

- `out` (string)  
  Nombre del PDF a generar.
  - En `build_all`: se genera **dentro de la carpeta** del práctico/taller.
  - En `build`: se respeta el nombre pero siempre se escribe bajo `output_dir`.

- `title` (string)  
  Título grande (bloque de título).

- `subtitle` (string | opcional)  
  Subtítulo debajo del título.

- `meta_line` (string | opcional)  
  Línea chica bajo el título (ej: `UDELAR · 2026`).

- `include_title_block` (bool)  
  Mostrar/ocultar bloque inicial (título + meta_line + subtitle + línea horizontal).

- `include_toc` (bool)  
  Mostrar/ocultar índice (TOC).

- `toc_title` (string)  
  Título del TOC (default típico: `Contenido`).

- `toc_max_level` (int)  
  Profundidad máxima del TOC/outline (recomendado 1..3).

- `footer_left` (string)
- `footer_center` (string)
- `footer_right` (string)

- `footer_show_page` (bool)  
  Si true, agrega `Página N` en el footer derecho.

- `footer_link_to_toc` (bool)  
  Si hay TOC, el footer center actúa como link interno hacia el TOC.

- `author` (string) — metadata PDF
- `subject` (string) — metadata PDF
- `keywords` (string) — metadata PDF

- `system` (string) — compatibilidad legacy
- `contacto` (string) — compatibilidad legacy

### 3.4 Defaults importantes (si NO ponés `[DOC ...]`)
Depende del builder, pero en la práctica:
- `include_title_block=true`
- `include_toc=true` (los builders lo fuerzan como default aunque `DocSpec` tenga otro default)
- `toc_title="Contenido"`
- `toc_max_level=3`

---

## 4) Texto normal (párrafos)

Cualquier línea que no sea un marcador especial se interpreta como texto.

**Regla crítica**: varias líneas normales seguidas se concatenan en un solo párrafo, separadas por espacio.

Ejemplo (esto se vuelve 1 párrafo):
```
La caché se organiza en líneas.
Cada línea tiene un tag y un bloque de datos.
Además puede haber un bit dirty.
```

Para forzar párrafos separados, poné una línea en blanco entre bloques.

---

## 5) Formato inline dentro de párrafos y celdas de tabla

Dentro de texto normal y dentro de celdas de tabla se soporta:

- Negrita: `**texto**`
- Cursiva: `*texto*`
- Código inline: `` `MOV AX, BX` ``

Notas:
- El parser **escapa** HTML (no se permite HTML libre).
- El código inline se renderiza con fuente monoespaciada.
- Dentro de código inline (`...`) **no** se aplica ningún otro formato inline (negrita/cursiva/color/links): el contenido es literal.
- Recomendado para notación formal con `*` (Σ*, r*, (a|b)*, etc.).

---

## 6) Normalización / Unicode / símbolos

Por compatibilidad con fuentes base PDF (Helvetica/Courier), el parser normaliza:

- Flechas: `→` => `->`, `⇒` => `=>`, `↔` => `<->`, etc.
- Checks: `✓` => `OK`, `✗` => `NO`
- Ciertas comillas “inteligentes” -> comillas normales
- Emojis frecuentes: `🟢` => `OK`, `🟡` => `WARN`, `🔴` => `CRIT`, etc.
- Emojis restantes suelen eliminarse

Recomendación práctica:
- Si algo “raro” no sale bien en el PDF, reemplazalo por ASCII.

---

## 7) Headings / Secciones (títulos) + TOC/Outline

Hay **dos** formatos de headings.

### 7.1 Heading “dot” (una línea)
Sintaxis:
```
1. Memorias
1.2. Caché
3.1.4. Write-back
```

Reglas:
- Debe ser: `NUMERO_CON_PUNTOS + "." + espacio + título`
  - Ej: `1. Título`
  - Ej: `1.2. Título`
- Nivel = `1 + cantidad_de_puntos_en_el_numero`
  - `1.` => nivel 1
  - `1.2.` => nivel 2
  - `1.2.3.` => nivel 3

Render:
- nivel 1 -> estilo visual H2
- nivel 2+ -> estilo visual H3

TOC/Outline:
- Los headings fuera de callouts entran al TOC y al outline, hasta `toc_max_level`.

### 7.2 Heading “bloque” (entre reglas de `=`)

Forma exacta (3 líneas):
```
==========
1) Memorias
==========

==========
2.1) Caché
==========
```

Reglas:
- La regla de `=` debe tener **10 o más** `=` (puede ser más).
- Son 3 líneas: regla, título, regla.
- El título puede tener prefijo numérico con `)` o `.`:
  - `1) ...`
  - `2.1) ...`
  - `2.1. ...`  (sí: `.` como delimitador final también)
- Si no hay numeración, igual se crea heading nivel 1.

### 7.3 Saltos de página automáticos antes de headings
Por UX el parser puede insertar saltos:
- Todo heading de **nivel 1** empieza página nueva.
- Si el título contiene `Ejercicio` (case-insensitive), empieza página nueva.

Esto NO es configurable desde el `.txt` (es política del parser).

### 7.4 Duplicados de headings y anchors internos
Cada heading genera un anchor interno (bookmark).
Si dos headings “colisionan” en el slug, el parser desambigua con sufijos `-2`, `-3`, etc.
(Esto solo importa si dependés de anchors internos; para el usuario final suele ser invisible.)

---

## 8) Separadores (líneas horizontales)

### 8.1 Regla con guiones
Una línea con **5 o más** `-` (y solo `-`) genera separador:
```
-----
```

### 8.2 Regla con iguales
Una línea con **10 o más** `=` genera separador:
```
==========
```

OJO:
- Si hay patrón de heading-bloque (regla + título + regla), se interpreta como heading, no como separador.

---

## 9) Saltos de página manuales

Una línea exacta:
- `[PAGEBREAK]`
- `[PB]`

Inserta salto de página.

---

## 10) Código (bloques)

### 10.1 Código fenced (recomendado)
Usá triple backtick. Idioma opcional:

```c
int main() {
  return 0;
}
```

Propiedades:
- Monoespaciado.
- Mantiene indentación.
- Es “splittable”: puede cortar entre páginas si es largo.

### 10.2 Código por sangría (rápido)
Cualquier bloque de líneas que empiecen con:
- 4 espacios, o
- tab

Se interpreta como bloque de código (“Procedimiento”):

    MOV AX, BX
    ADD AX, 1
    INT 21h

Limitación:
- No hay “continuación” de código mezclando líneas con y sin sangría: el bloque termina al primer corte.

---

## 11) Listas

### 11.1 Lista sin orden (bullets)
Se detecta si la línea (ignorando indentación) empieza con:
- `- `
- `* `
- `• `

Ejemplo:
```
- Primer punto
- Segundo punto
- Tercer punto
```

Limitación:
- No hay soporte formal de sublistas (no anida estructura).

### 11.2 Lista numerada
Se detecta si la línea empieza con:
- `1. `
- `2. `
- `1) `
- `2) `

Ejemplo:
```
1) Leer el tag
2) Comparar
3) Si miss, traer bloque
```

Limitación:
- No hay items multi-línea. Si querés “texto largo” por item, reescribilo como párrafo + lista.

---

## 12) Callouts (bloques resaltados)

### 12.1 Sintaxis recomendada: `:::kind [título] ... :::`
Formato general:
```
:::KIND [título opcional]
(líneas de contenido)
:::
```

Cierre:
- La línea de cierre debe ser exactamente `:::` (sola).

**No anidar** callouts: si en el cuerpo aparece una línea `:::`, va a cerrar el bloque.

#### Kinds soportados (sugar)
Estos `KIND` activan estilo + título default:

- `def`   → note, título default: “Definición”
- `ej`    → info, título default: “Ejemplo”
- `error` → danger, título default: “Error típico”
- `tip`   → note, título default: “Tip”
- `warn`  → warn, título default: “Atención”
- `info`  → info, título default: “Info”
- `check` → info, título default: “Checklist”

Ejemplos:
```
:::def
Una caché write-back escribe a memoria recién al reemplazar un bloque dirty.
:::

:::ej Cache directa
Dirección = tag | línea | palabra
:::

:::warn
Ojo con el tamaño de bloque vs tamaño de palabra.
:::
```

Contenido:
- El cuerpo del callout se parsea como “mini-documento”: puede tener listas, código, `[FIG]`, tablas, etc.
- Headings dentro de callouts **no entran** al TOC/outline (para evitar ruido).

### 12.2 Sintaxis legacy (compatibilidad)
Formato:
```
[NOTE title="Definición"]
Texto...
[/NOTE]
```

KINDs legacy:
- `NOTE`, `TIP`, `WARN`, `DANGER`, `INFO`, `CHECK`

---

## 13) Tablas (`:::table`)

Se definen como un bloque especial:

```
:::table
| Col1 | Col2 | Col3 |
|------|-----:|:----:|
| A    |  12  |  OK  |
| B    |   3  |  NO  |
:::
```

Reglas:
- Solo se toman líneas que empiecen con `|`
- La primera fila es encabezado.
- La segunda fila puede ser separador estilo Markdown (opcional) y define alineación:
  - `---`   normal (sin alineación explícita)
  - `:---`  izquierda
  - `---:`  derecha
  - `:---:` centro
- No hay “escape” de `|` dentro de una celda (si necesitás un pipe literal, reformulá).
- Inline formatting funciona dentro de celdas (`** **`, `* *`, `` ` ` ``).

---

## 14) Figuras desde PDFs (captura de página): `[FIG ...]`

Marcador (línea completa):
```
[FIG file="T21JerarquiaDeMemoria.pdf" page=3 caption="Jerarquía de memoria" zoom=2.0]
```

### 14.1 Sintaxis exacta (importante)
El parser espera el orden:
1) `file="..."`
2) `page=N`
3) opcional `caption="..."`
4) opcional `zoom=2.0`

Notas:
- `file` y `caption` requieren comillas dobles.
- `page` es entero.
- `zoom` es float con punto (ej: `2.0`, `1.5`).
- `page` es **1-based** (la primera página es 1).

Si omitís caption, se usa default:
- `Fuente: <file>, pág. <page>`

### 14.2 Cómo se busca el PDF (`file=...`)
El builder resuelve el PDF buscando en este orden típico:
1) carpeta actual del trabajo (ej. `Practico/00Practico/`)
2) `Teorico/`
3) `Practico/`
4) `Taller/`
5) raíz de la materia

Si no existe, el marcador no revienta el build: puede omitirse con warning.

### 14.3 Cache de páginas exportadas
Para no renderizar la página en cada build:

- Se exporta la página a PNG:
  `.../<cache_dir>/<pdf_stem>/pNNN_zZ.png`

Dónde cae `cache_dir`:
- En `build_all`: `assets/_pdfpages/` dentro de la carpeta del práctico/taller.
- En `build`: `output/_cache/<txt_stem>/...`

### 14.4 Dependencias
Para extraer páginas de PDF se usa PyMuPDF (`fitz`).
Si no está instalado:
- Se omiten figuras desde PDF (y opcionalmente se loguea warning).

---

## 15) Índice (TOC) y outline (bookmarks)

### 15.1 Qué entra al TOC
- Entran headings generados por §7, hasta `toc_max_level`.
- El título grande del documento (bloque de título) **no** entra al TOC.
- El heading del TOC (“Contenido” por defecto) **no** se lista dentro del propio TOC.

### 15.2 Link al TOC desde el footer
Si:
- `include_toc=true`, y
- `footer_link_to_toc=true`

Entonces el footer center es clickeable y te lleva al TOC.
(El link solo se activa a partir de la página 2 en adelante.)

---

## 16) Limitaciones (lo que NO existe hoy)

- No hay directiva en `.txt` para insertar imágenes PNG/JPG “directo”.
  Hoy la inserción en `.txt` está pensada para páginas de PDF vía `[FIG ...]`.
- No hay soporte formal para sublistas.
- No hay celdas multi-línea en tablas.
- No hay enlaces arbitrarios en texto (HTML se escapa).

Si se necesita alguna, se implementa como nueva directiva en `txtfmt.py`.

---

## 17) Plantillas recomendadas (copiar/pegar)

### 17.1 Plantilla general de resumen
```
[DOC title="Práctico 02 — Memorias" subtitle="Arquitectura de Computadoras" include_toc=true toc_max_level=3 footer_right="Práctico 02"]

==========
1) Resumen rápido
==========

:::check
- Definición + ejemplo mínimo
- Error típico
- 3 preguntas tipo examen
:::

==========
2) Conceptos
==========

2.1. Memoria principal

:::def
Definición...
:::

:::ej
Ejemplo...
:::

:::error
Error típico...
:::

2.2. Caché

[FIG file="T21JerarquiaDeMemoria.pdf" page=3 caption="Jerarquía de memoria" zoom=2.0]

:::table
| Política | ¿Escribe a memoria? | Tráfico de bus |
|----------|---------------------:|:--------------:|
| write-through | siempre | alto |
| write-back    | al reemplazo | menor |
:::

```c
// pseudocódigo de acceso
if (hit) { ... }
else { ... }
```

==========
3) Preguntas tipo examen
==========

- Explicar write-through vs write-back
- Interpretar dirección para caché directa / asociativa
- Diseñar tamaño/organización de una ROM
```

### 17.2 Checklist de “archivo sano”
Antes de compilar, revisá:

- ¿El `[DOC ...]` (si existe) está en la primera línea no vacía?
- ¿Los headings “dot” terminan en `.` antes del espacio? (`1.2. Título`)
- ¿Los callouts abren con `:::kind` y cierran con `:::` en línea sola?
- ¿Las tablas están dentro de `:::table ... :::` y cada fila empieza con `|`?
- ¿Los `[FIG ...]` respetan el orden `file`, `page`, `caption`, `zoom`?
- ¿Evitaste emojis/símbolos raros cuando no aportan?

---

## 18) Troubleshooting rápido

- “No aparece mi heading en el TOC”:
  - Puede estar dentro de un callout (los headings en callouts se excluyen del TOC).
  - Puede exceder `toc_max_level`.

- “No se ve una figura [FIG]”:
  - Verificá que el PDF existe y que `page` sea 1-based.
  - Si no está PyMuPDF (`fitz`), se omite la exportación de páginas.

- “El PDF se corta feo alrededor de una figura/callout/código”:
  - El engine mete saltos condicionales, pero si el bloque es enorme, reestructurá:
    - partí un callout en 2
    - mové una figura a otra sección
    - insertá `[PB]` manual.

---

Fin.
