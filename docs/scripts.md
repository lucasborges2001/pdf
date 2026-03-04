# scripts/

`scripts/` contiene wrappers operativos para el equipo (Windows/PowerShell).

## 1) build_all.ps1

Archivo: `scripts/build_all.ps1`

Contrato:

- Se ejecuta desde cualquier ubicación.
- Cambia el working directory a `<Materia>/Scripts`.
- Compila la materia actual con `python -m _pdf.build_materia <Materia>`.

Uso:

```powershell
./_pdf/scripts/build_all.ps1
./_pdf/scripts/build_all.ps1 --check
./_pdf/scripts/build_all.ps1 --area practico --only 00 01
```

## 2) clean.ps1

Archivo: `scripts/clean.ps1`

Contrato:

- Elimina el cache de salida del build simple:
  - `_pdf/output/_cache/`

Uso:

```powershell
./_pdf/scripts/clean.ps1
```
