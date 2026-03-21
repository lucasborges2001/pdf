# Uso operativo

## Flujo recomendado

### 1. Validar

Para una materia:

```powershell
python -m _pdf.scan --materia D:\SisOp
```

Para `input/` del repo:

```powershell
python -m _pdf.scan --input
```

### 2. Endurecer el pipeline

```powershell
python -m _pdf.scan --materia D:\SisOp --strict
```

o

```powershell
python -m _pdf.build --check --strict
```

### 3. Compilar

```powershell
python -m _pdf.build
python -m _pdf.build_materia --materia D:\SisOp
python -m _pdf.build_carpeta --carpeta D:\repo\docs\tutoriales
```

## Comandos

### Build simple

```powershell
python -m _pdf.build
python -m _pdf.build --clean
python -m _pdf.build --check
python -m _pdf.build --check --strict
python -m _pdf.build --materia D:\SisOp --search-dir D:\assets
```

### Build por materia

```powershell
python -m _pdf.build_materia --materia D:\SisOp
python -m _pdf.build_materia --materia D:\SisOp --area practico
python -m _pdf.build_materia --materia D:\SisOp --area both
python -m _pdf.build_materia --materia D:\SisOp --only 00 01 07
python -m _pdf.build_materia --materia D:\SisOp --check --strict
```

### Build por carpeta

```powershell
python -m _pdf.build_carpeta --carpeta D:\repo\docs\tutoriales
python -m _pdf.build_carpeta --carpeta D:\repo\docs\tutoriales --only crearUsuario cargarSaldo
python -m _pdf.build_carpeta --carpeta D:\repo\docs\tutoriales --check --strict
```

### Ayuda

```powershell
python -m _pdf.help
```

## Flags comunes

- `--quiet`
- `--only-summary`
- `--no-summary`
- `-v`, `-vv`
- `--no-color`
- `--ascii`
- `--log FILE`
- `--log-json FILE`
- `--max-issues N`
- `--show-skipped`
- `--max-skipped N`

## Exit codes

- `0`: ejecución correcta;
- `1`: errores, o warnings si se usa `--strict`;
- `2`: parámetro o ruta inválida.

## Resolución de assets

Orden de búsqueda:

1. carpeta del `.txt`;
2. `PDF_FIG_SEARCH_DIRS`;
3. `--search-dir`;
4. si hay materia: `Teorico/`, `Practico/`, `Taller/`, raíz de materia.

## Error típico resuelto

### Mensaje

```txt
DocSpec.__init__() missing 1 required positional argument: 'title'
```

### Estado actual

Ese error ya no debería aparecer como excepción tardía si el archivo pasa por el flujo actual.

Ahora se detecta antes con mensajes explícitos:

- `Falta header [DOC ...] en la primera línea no vacía.`
- `Header [DOC] debe incluir title.`
- `Header [DOC ...] inválido: ...`

## Tests

```powershell
python -m unittest discover -s tests -v
```

Notas:

- la suite está preparada para correr desde la raíz del repo;
- si `reportlab` no está instalado, los tests que ejercitan render/flowables se saltean;
- parser/header/discovery/lint siguen validándose sin esa dependencia.
