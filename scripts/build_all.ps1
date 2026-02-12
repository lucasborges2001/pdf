param(
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

$ScriptsDir = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Push-Location $ScriptsDir
try {
  python -m _pdf.build_all @Args
} finally {
  Pop-Location
}
