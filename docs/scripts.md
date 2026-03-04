# scripts/

`scripts/` contiene wrappers operativos para el equipo (Windows/PowerShell).

## Objetivo

- Ejecutar el framework desde una ubicación central (`...\_pdf\`) sin copiarlo dentro de cada materia.
- Estandarizar el working directory para que `python -m _pdf...` funcione siempre.

> Regla: los scripts hacen `cd` a la carpeta **padre** de `_pdf` y ejecutan módulos con `python -m`.

## 1) build_materia.ps1

Archivo: `scripts/build_materia.ps1`

Contrato:

- Requiere la ruta de la materia.
- Ejecuta `python -m _pdf.build_materia --materia <PATH> ...` desde la carpeta padre de `_pdf`.

Uso:

```powershell
# Desde cualquier ubicación
.\_pdf\scripts\build_materia.ps1 D:\ArqComp
.\_pdf\scripts\build_materia.ps1 D:\ArqComp --check
.\_pdf\scripts\build_materia.ps1 D:\ArqComp --area practico --only 00 01
```

## 2) build_all.ps1

Archivo: `scripts/build_all.ps1`

Contrato:

- Alias de `build_materia.ps1` (misma interfaz).
- Se mantiene para compatibilidad de equipo.

Uso:

```powershell
.\_pdf\scripts\build_all.ps1 D:\ArqComp --check
```

## 3) clean.ps1

Archivo: `scripts/clean.ps1`

Contrato:

- Elimina el cache de salida del build simple:
  - `_pdf/output/_cache/`

Uso:

```powershell
.\_pdf\scripts\clean.ps1
```
