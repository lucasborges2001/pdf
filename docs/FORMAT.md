# Contrato del formato `.txt`

## Estructura mínima

Todo documento válido tiene:

1. un header `[DOC ...]` en la primera línea no vacía;
2. un `title` dentro de ese header;
3. un cuerpo libre con bloques y texto.

Ejemplo mínimo:

```txt
[DOC title="Resumen base"]

Texto inicial.
```

## Header `[DOC ...]`

### Sintaxis

```txt
[DOC title="Práctico 01" include_toc=true toc_max_level=2 out="01.pdf"]
```

Reglas:

- una sola línea;
- pares `clave=valor`;
- strings con espacios entre comillas;
- booleanos `true` o `false`;
- enteros simples para campos numéricos.

### Claves aceptadas

- `title`
- `out`
- `subtitle`
- `meta_line`
- `include_title_block`
- `include_toc`
- `toc_title`
- `toc_max_level`
- `footer_left`
- `footer_center`
- `footer_right`
- `footer_show_page`
- `footer_link_to_toc`
- `author`
- `subject`
- `keywords`
- `system`
- `contacto`

### Validaciones

- si falta el header: `ERROR`;
- si el header está mal cerrado o mal tokenizado: `ERROR`;
- si falta `title`: `ERROR`;
- si hay claves desconocidas: `WARN`;
- en build, las claves desconocidas se ignoran en vez de romper `DocSpec`.

## Texto normal

- líneas consecutivas de texto se unen en un mismo párrafo;
- líneas en blanco cortan párrafos;
- el inline se sanitiza antes de renderizar.

## Títulos

### Dot headings jerárquicos

```txt
1.2. Memoria caché
2.1.3. Políticas de escritura
```

Siempre se interpretan como headings.

### Numeración simple

```txt
1. Introducción
```

Se interpreta como heading solo si la línea parece un título real:

- corta;
- sin puntuación final fuerte;
- con forma de título o mayúsculas.

Si aparece en secuencia como enumeración, se trata como lista ordenada.

### Títulos en bloque con `=`

```txt
==========
1) Tema
==========
```

Reglas:

- la línea de `=` debe tener al menos 10 caracteres;
- headings de nivel superior fuerzan salto de página;
- si el título contiene `Ejercicio`, también fuerza salto.

## Separadores

- `-----`: línea horizontal;
- `==========`: línea horizontal si no forma un heading en bloque.

## Listas

### No ordenadas

```txt
- item
* item
• item
```

### Ordenadas

```txt
1) item
2. item
```

La lista ordenada se detecta antes que el heading simple para evitar falsos positivos.

## Código

### Fence

````txt
```c
int main() { return 0; }
```
````

### Indentado

```txt
    MOV AX, BX
    ADD AX, 1
```

Validación:

- cierre sin apertura: `ERROR`;
- apertura sin cierre: `ERROR`.

## Callouts

### Sintaxis recomendada

```txt
:::def
Texto...
:::
```

Mapa principal:

- `def` -> note
- `ej` -> info
- `error` -> danger
- `tip` -> note
- `warn` -> warn
- `info` -> info
- `check` -> info

### Compatibilidad legacy

```txt
[NOTE title="Definición"]
Texto...
[/NOTE]
```

Validación:

- cierre sin apertura: `ERROR`;
- cierre que no matchea apertura: `ERROR`;
- bloque abierto sin cierre: `ERROR`.

## Tablas

```txt
:::table
| Columna | Valor |
|--------:|:-----:|
| A       |  10   |
:::
```

Reglas:

- solo cuentan filas que empiezan con `|`;
- la segunda fila puede definir alineación;
- no hay escape de `|` dentro de una celda.

## Saltos de página

```txt
[PB]
[PAGEBREAK]
```

## Figuras e imágenes

### Página de PDF

```txt
[FIG file="teorico.pdf" page=3 caption="Jerarquía" zoom=2.0]
```

### Imagen

```txt
[IMG file="diagrama.png" caption="Esquema" width=420]
```

Reglas:

- `file` es obligatorio en ambos;
- en `FIG`, `page` es obligatorio y es 1-based;
- `zoom` debe ser mayor a 0;
- en `IMG`, `width` es opcional y controla el ancho máximo;
- si falta el asset, scan marca `WARN`.

## Inline soportado

- negrita: `**texto**`
- cursiva: `*texto*`
- código inline: `` `texto` ``

No se soporta como contrato activo:

- color inline;
- links markdown renderizados;
- HTML libre.

Dentro de código inline no se aplican estilos de negrita/cursiva.

## Qué valida el lint

- header ausente/inválido;
- `title` faltante;
- fences desbalanceados;
- callouts desbalanceados;
- bloques `:::` desbalanceados;
- `[FIG]` o `[IMG]` inválidos;
- `[FIG]` con `page < 1` o `zoom <= 0`;
- assets faltantes en `FIG` o `IMG`.

Con `--strict`, los `WARN` afectan el exit code.
