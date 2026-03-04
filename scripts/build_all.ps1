param(
  [Parameter(Mandatory=$true, Position=0)]
  [string]$Materia,

  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

# Alias por compatibilidad de equipo: delega en build_materia.ps1.
& (Join-Path $PSScriptRoot "build_materia.ps1") $Materia @Args
