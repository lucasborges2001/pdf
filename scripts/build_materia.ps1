param(
  [Parameter(Mandatory=$true, Position=0)]
  [string]$Materia,

  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

# Este script vive en: <...>\_pdf\scripts
# Para que `python -m _pdf...` funcione, hay que ejecutar desde la carpeta padre de `_pdf`.
$RepoParent = Resolve-Path (Join-Path $PSScriptRoot "..\..")

Push-Location $RepoParent
try {
  python -m _pdf.build_materia --materia $Materia @Args
} finally {
  Pop-Location
}
