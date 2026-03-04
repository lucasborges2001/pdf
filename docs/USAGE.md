# Uso

> Regla operativa: ejecutar los comandos desde la carpeta **padre** de `_pdf` (ej: `cd D:\scripts`) para que `python -m _pdf...` resuelva el paquete.

Este repo está pensado para estar **centralizado** (por ejemplo `D:\Scripts\_pdf\`) y compilar:

- **Build simple**: `_pdf/input/*.txt` → `_pdf/output/*.pdf`
- **Build por materia**: `<Materia>/**` → `<Materia>/Resumenes/**`
- **Scan**: validación rápida del formato (sin generar PDFs)

---

## Comandos

### 1) Help (solo lista comandos)
```bash
python -m _pdf.help
```

### 2) Build simple (input → output)
```bash
python -m _pdf.build
python -m _pdf.build --clean
python -m _pdf.build --check
python -m _pdf.build --check --show-skipped
```

### 3) Build por materia (materia → Resumenes)
```bash
python -m _pdf.build_materia --materia D:\ArqComp
python -m _pdf.build_materia --materia D:\ArqComp --area practico
python -m _pdf.build_materia --materia D:\ArqComp --only 00 01 07
python -m _pdf.build_materia --materia D:\ArqComp --check
python -m _pdf.build_materia --materia D:\ArqComp --check --show-skipped
python -m _pdf.build_materia --materia D:\ArqComp --check --strict
```

### 4) Scan (sin generar PDFs)
```bash
python -m _pdf.scan --input
python -m _pdf.scan --materia D:\ArqComp
python -m _pdf.scan --materia D:\ArqComp --show-skipped
python -m _pdf.scan --materia D:\ArqComp --strict
```

---

## Estructura esperada en una materia

El scan/build por materia recorre recursivamente y busca `.txt` **candidatos** (heurística del formato). Se recomienda:

```
<Materia>/
  Practico/
    ...
  Taller/
    ...
  Resumenes/          # generado
```

**Nota:** `Resumenes/`, `output/`, `__pycache__/`, `.git/`, `.venv/` se excluyen del scan.

---

## Resolución de assets (FIG/IMG)

Para que `[FIG file="..."]` / `[IMG file="..."]` encuentren recursos:

- Por defecto se busca en la carpeta del `.txt`
- En modo materia también se busca en `<Materia>/Practico`, `<Materia>/Taller`, `<Materia>/Teorico`, y raíz de la materia
- Podés sumar directorios extra:
  - `python -m _pdf.build --search-dir D:\Algo --search-dir D:\Otra`
  - o variable de entorno: `PDF_FIG_SEARCH_DIRS` (separador `;` en Windows)


## Flags comunes (salida en terminal)

Estos flags funcionan en `build`, `build_materia` y `scan`:

- `--quiet`: salida mínima (solo resumen/errores)
- `-v` / `-vv`: más detalle
- `--no-color`: desactiva colores ANSI
- `--ascii`: desactiva símbolos unicode
- `--max-issues N`: máximo de issues a imprimir (en `scan` y `--check`)
- `--show-skipped`: lista `.txt` descartados por heurística
- `--max-skipped N`: máximo de skipped a imprimir


## Flags de salida (comunes)

- `--quiet`: silencia si está OK; si hay errores, imprime mínimo.
- `--only-summary`: imprime solo el resumen final.
- `--no-summary`: no imprime resumen final (solo detalle).
- `-v` / `-vv`: más detalle.
- `--no-color`: desactiva ANSI.
- `--ascii`: usa ASCII.


## Logging de salida de terminal

Todos los comandos soportan `--log <archivo>` para guardar la salida (además de imprimirla en pantalla).
Ejemplo:

```powershell
python -m _pdf.build_materia --materia D:\ArqComp --check --log D:\logs\pdf_check.txt
```
