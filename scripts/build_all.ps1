param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

$ScriptsDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Push-Location $ScriptsDir
try {
  # Wrapper estable: compila la materia actual (el padre de <Materia>\Scripts)
  $Materia = Resolve-Path (Join-Path $ScriptsDir "..")
  python -m _pdf.build_materia $Materia @Args
} finally {
  Pop-Location
}
