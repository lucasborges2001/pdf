# scripts/

`scripts/` contiene wrappers operativos para el equipo (Windows/PowerShell).

<<<<<<< HEAD
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
=======
## 1) build_all.ps1
>>>>>>> a466de344d0bb9a968c160c1247e6dda6df08828

Archivo: `scripts/build_all.ps1`

Contrato:

<<<<<<< HEAD
- Alias de `build_materia.ps1` (misma interfaz).
- Se mantiene para compatibilidad de equipo.
=======
- Se ejecuta desde cualquier ubicación.
- Cambia el working directory a `<Materia>/Scripts`.
- Compila la materia actual con `python -m _pdf.build_materia <Materia>`.
>>>>>>> a466de344d0bb9a968c160c1247e6dda6df08828

Uso:

```powershell
<<<<<<< HEAD
.\_pdf\scripts\build_all.ps1 D:\ArqComp --check
```

## 3) clean.ps1
=======
./_pdf/scripts/build_all.ps1
./_pdf/scripts/build_all.ps1 --check
./_pdf/scripts/build_all.ps1 --area practico --only 00 01
```

## 2) clean.ps1
>>>>>>> a466de344d0bb9a968c160c1247e6dda6df08828

Archivo: `scripts/clean.ps1`

Contrato:

- Elimina el cache de salida del build simple:
  - `_pdf/output/_cache/`

Uso:

```powershell
<<<<<<< HEAD
.\_pdf\scripts\clean.ps1
=======
./_pdf/scripts/clean.ps1
>>>>>>> a466de344d0bb9a968c160c1247e6dda6df08828
```
