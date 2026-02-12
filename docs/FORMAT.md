# FORMAT.md — Formato de documentos .txt (Prácticos / Talleres)

Este documento define el **formato de texto** soportado por el framework `_pdf` para generar PDFs académicos
a partir de archivos `.txt` ubicados en `Practico/` y `Taller/`.

La idea: con **un solo `.txt`** por carpeta (`00Practico/00Practico.txt`, `01Taller/01Taller.txt`, etc.) podés:
- escribir el resumen con estructura (títulos, listas, código, figuras desde PDFs teóricos)
- generar PDF automáticamente con índice (TOC), outline/bookmarks y footer
- cachear páginas de PDFs como imágenes (`assets/_pdfpages/`)

---

## 0) Estructura de carpetas esperada

Ejemplo canónico:

<Materia>/
  Practico/
    00Practico/
      00Practico.txt
      assets/_pdfpages/         (se crea solo al exportar páginas de PDFs)
    01Practico/
      01Practico.txt
  Taller/
    00Taller/
      00Taller.txt
      assets/_pdfpages/
  Teorico/
    TxxAlgo.pdf
  Scripts/
    _pdf/
      build_all.py
      txtfmt.py
      render.py
      ctx.py
      images.py
      paths.py
      core.py

---

## 1) Cómo se compila

Ejecutar desde `<Materia>/Scripts`:

- Generar todo:
  `python3 -m _pdf.build_all`

- Solo prácticos:
  `python3 -m _pdf.build_all --area practico`

- Solo algunos números:
  `python3 -m _pdf.build_all --only 00 01 07`

- Modo estricto (falla ante claves DOC desconocidas):
  `python3 -m _pdf.build_all --strict`

Salida:
- El PDF se genera dentro de cada carpeta (por defecto `00PracticoResumen.pdf`, `00TallerResumen.pdf`, etc.)
- Luego se copia “plano” a `<Materia>/Resumenes/` (por defecto) y se limpia una sola vez al inicio (salvo `--no-clean-output`)

---

## 2) Selección del .txt dentro de cada carpeta

Por carpeta (ej. `01Practico/`) el builder busca:

1) Primero el nombre exacto esperado:
   - `01Practico.txt` para prácticos
   - `01Taller.txt` para talleres

2) Si no existe, toma el primer match del patrón:
   - `*Practico.txt` o `*Taller.txt` (configurable con `--txt-pattern`)

Recomendación: **siempre** usar el nombre exacto (evita sorpresas).

---

## 3) Header opcional: `[DOC ...]` (metadata + configuración)

### 3.1 Qué es
La **primera línea no vacía** del archivo puede ser un header DOC.
Ese header **no se imprime** en el PDF: solo configura el build.

Ejemplo:

[DOC out="00PracticoResumen.pdf" title="Práctico 00 — Resumen" subtitle="Arquitectura de Computadoras" include_toc=true toc_max_level=3 footer_right="Práctico 00"]

### 3.2 Sintaxis
- Debe estar en una sola línea
- Forma: `[DOC key=value key=value ...]`
- Se parsea con `shlex`: si un valor tiene espacios, **usá comillas**.

Ejemplos válidos:
- `include_toc=true`
- `toc_max_level=3`
- `title="Práctico 02 — Memorias"`
- `out=02PracticoResumen.pdf`

### 3.3 Claves permitidas (lista completa)
Estas son las únicas claves aceptadas por el builder:

- out                      (string)  Nombre del PDF a generar dentro de la carpeta
- title                    (string)  Título del documento (se imprime grande)
- subtitle                 (string)  Subtítulo (opcional)
- meta_line                (string)  Línea “chica” bajo el título (ej: "UDELAR · 2026")
- include_title_block      (bool)    Mostrar/ocultar bloque de título inicial
- include_toc              (bool)    Mostrar/ocultar índice (TOC)
- toc_title                (string)  Título del índice (default: "Contenido")
- toc_max_level            (int)     Profundidad máxima del TOC (1..3 recomendado)
- footer_left              (string)  Footer columna izquierda
- footer_center            (string)  Footer centro
- footer_right             (string)  Footer derecha
- footer_show_page         (bool)    Mostrar/ocultar “Página N”
- footer_link_to_toc       (bool)    Si hay TOC: link desde footer_center a la página del TOC
- author                   (string)  Metadata PDF
- subject                  (string)  Metadata PDF
- keywords                 (string)  Metadata PDF
- system                   (string)  Compatibilidad (se usa si footer_left/center no está)
- contacto                 (string)  Compatibilidad (se usa si footer_left/center no está)

### 3.4 Defaults importantes
Si NO ponés DOC:
- `include_title_block=true`
- `include_toc=true` (por cómo construye `DocSpec` el builder)
- `toc_title="Contenido"`
- `toc_max_level=3`
- output final copiado a `<Materia>/Resumenes/`

---

## 4) Reglas generales del texto

### 4.1 Espacios en blanco
- Líneas en blanco separan bloques.
- Varias líneas de texto “normal” seguidas se **unen** en un solo párrafo (ver §6).

### 4.2 Caracteres especiales / unicode
El parser normaliza algunos símbolos (para evitar problemas de fuentes PDF). Ejemplos:
- `→` se convierte a `->`
- `⇒` se convierte a `=>`
- `↔` se convierte a `<->`
- `✓` a `OK`
- `✗` a `NO`
- comillas “inteligentes” a comillas normales

Recomendación: si ves un símbolo raro en PDF, reemplazalo por ASCII.

---

## 5) Índice (TOC) y Outline (Bookmarks)

### 5.1 Qué entra al TOC
- Entran los títulos generados por el formato de **títulos** (§7)
- La profundidad está limitada por `toc_max_level`
- El título grande del documento y el propio heading “Contenido” **no** entran al TOC (por diseño)

### 5.2 Footer con link al TOC
Si `include_toc=true` y `footer_link_to_toc=true`, el footer center es clickeable y te lleva al TOC.

---

## 6) Párrafos (texto normal)

Cualquier línea que no sea un marcador especial se interpreta como texto.
Varias líneas seguidas se concatenan (separadas por espacio) formando un párrafo.

Ejemplo (esto es 1 párrafo):

La caché se organiza en líneas.
Cada línea tiene un tag y un bloque de datos.
Además puede haber un bit dirty.

---

## 7) Títulos / Secciones (Headings)

Hay dos formatos para headings.

### 7.1 Formato “simple” (una línea)
Soporta numeración tipo `1.`, `1.2.`, `3.1.4.`

Ejemplos:
- `1. Memorias`
- `1.2. Cache`
- `3.1.4. Write-back`

**Reglas:**
- El nivel se calcula por cantidad de puntos:
  - `1.` => nivel 1
  - `1.2.` => nivel 2
  - `1.2.3.` => nivel 3
- En PDF:
  - nivel 1 usa estilo H2
  - nivel >=2 usa estilo H3

### 7.2 Formato “bloque” (título entre reglas de =)
Sirve para que el título destaque más visualmente.

Ejemplo:

==========
1) Memorias
==========

o también:

==========
2.1) Caché
==========

Reglas:
- Deben ser 3 líneas: regla de `=` + línea de título + regla de `=`
- La línea de título puede llevar prefijo numérico con `)` o `.`
- Si no hay numeración, igual se genera un heading nivel 1.

### 7.3 Saltos de página automáticos antes de headings
Por defecto:
- Todo heading de nivel 1 comienza página nueva.
- Si el título contiene la palabra “Ejercicio” (case-insensitive), también comienza página nueva.

Si no querés esto, habría que cambiar el parser (no es configurable desde el .txt).

---

## 8) Separadores (líneas horizontales)

### 8.1 Regla con guiones
Una línea con 5 o más `-` genera un separador:

-----

### 8.2 Regla con iguales
Una línea con 10 o más `=` también genera separador, **si no** está formando un heading bloque.

==========

---

## 9) Saltos de página manuales

Usá una línea exacta:

- `[PAGEBREAK]`  o
- `[PB]`

Esto inserta un salto de página.

---

## 10) Formato inline (dentro de párrafos y celdas de tabla)

Estos formatos funcionan dentro de texto normal (y también dentro de celdas de tabla):

- **Negrita**
  `**texto**`

- *Cursiva*
  `*texto*`

- `código inline`
  `` `MOV AX, BX` ``

Notas:
- El parser NO permite HTML libre (se escapa).
- Solo se soporta el inline anterior.

---

## 11) Listas

### 11.1 Lista sin orden (bullets)
Reconoce ítems que empiezan con:
- `- `
- `* `
- `• `

Ejemplo:

- Primer punto
- Segundo punto
- Tercer punto

### 11.2 Lista numerada
Reconoce ítems:
- `1. `
- `2. `
- `1) `
- `2) `

Ejemplo:

1) Leer el tag
2) Comparar
3) Si miss, traer bloque

Notas:
- No hay soporte “formal” de sublistas (se puede simular con sangría, pero no se interpreta como estructura).

---

## 12) Código (bloques)

Hay dos formas.

### 12.1 Bloque fenced (recomendado)
Usá triple backtick. Idioma opcional:

```c
int main() {
  return 0;
}
```

- Se renderiza monoespaciado.
- Mantiene espacios e indentación.
- Es splittable: puede cortarse entre páginas sin romper.

### 12.2 Código por sangría (rápido)
Cualquier bloque de líneas que empiecen con 4 espacios (o tab) se interpreta como bloque de código.

Ejemplo:

    MOV AX, BX
    ADD AX, 1
    INT 21h

Se renderiza como “Procedimiento”.

---

## 13) Callouts (bloques resaltados)

### 13.1 Sintaxis nueva (preferida): `:::...`
Formato general:

:::KIND [título opcional]
(líneas de contenido)
:::

KIND soportados y su semántica visual:

- `def`   → Definición (note)
- `ej`    → Ejemplo (info)
- `error` → Error típico (danger)
- `tip`   → Tip (note)
- `warn`  → Atención (warn)
- `info`  → Info (info)
- `check` → Checklist (info)
- `table` → Tabla (ver §14)

Ejemplos:

:::def
Una caché write-back escribe a memoria recién al reemplazar un bloque dirty.
:::

:::ej Cache directa
Dirección = tag | línea | palabra
:::

:::error
Confundir “bloque” (cache line) con “palabra” (word).
:::

Notas:
- El contenido del callout se parsea como “mini-documento”: puede incluir listas, código, figuras, etc.
- Recomendación: evitá headings dentro de callouts (podrían terminar en el TOC).

### 13.2 Sintaxis legacy: `[NOTE]...[/NOTE]`
Sigue soportada por compatibilidad:

[NOTE title="Definición"]
Texto...
[/NOTE]

KINDs:
- NOTE, TIP, WARN, DANGER, INFO, CHECK

---

## 14) Tablas

Se definen como un bloque especial:

:::table
| Col1 | Col2 | Col3 |
|------|-----:|:----:|
| A    |  12  |  OK  |
| B    |   3  |  NO  |
:::

Reglas:
- Solo se toman líneas que empiecen con `|`
- La primera fila es encabezado (header)
- La segunda fila puede ser separador estilo Markdown (opcional):
  - `---` normal
  - `:---` alineado izquierda
  - `---:` alineado derecha
  - `:---:` centrado
- No hay “escape” para `|` dentro de una celda (si necesitás un pipe literal, reformulá el texto).
- Inline formatting funciona dentro de celdas (negrita/cursiva/código inline).

---

## 15) Figuras desde PDFs teóricos (captura de página)

Marcador:

[FIG file="T21JerarquiaDeMemoria.pdf" page=3 caption="Jerarquía de memoria" zoom=2.0]

Parámetros:
- file   (obligatorio): nombre del PDF
- page   (obligatorio): página **1-based** (la primera es 1)
- caption (opcional): texto bajo la figura
- zoom   (opcional): escala de render (default 2.0)

Resolución de `file`:
Se busca en este orden:
1) carpeta actual del trabajo (ej. `Practico/00Practico/`)
2) `Teorico/`
3) `Practico/`
4) `Taller/`
5) raíz de la materia

Cache:
- Se exporta la página a PNG en:
  `assets/_pdfpages/<pdf_stem>/pNNN_zZ.png`
- Si ya existe el PNG, no se reexporta.

Notas:
- Si falta PyMuPDF (`fitz`), las figuras desde PDF se omiten (y puede loguear WARN si está activado).

---

## 16) Cosas NO soportadas (importante)

- No hay directiva en `.txt` para insertar imágenes PNG/JPG “directo”.
  Hoy la inserción de imágenes está pensada para páginas de PDFs (`[FIG ...]`).
- No hay tablas “CSV” ni celdas multi-línea.
- No hay enlaces arbitrarios en texto (HTML se escapa).
- No hay soporte formal para sublistas (solo listas planas).

Si querés alguna de estas, se implementa como nueva directiva (pero hoy no existe).

---

## 17) Plantilla recomendada para un resumen de examen

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
if (hit) ...
else ...
```

==========
3) Posibles preguntas de examen
==========

- Explicar write-through vs write-back
- Interpretar dirección para caché directa / asociativa
- Diseñar tamaño/organización de una ROM
