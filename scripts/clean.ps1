$RepoDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$CacheDir = Join-Path $RepoDir "output\_cache"
if (Test-Path $CacheDir) {
  Remove-Item -Recurse -Force $CacheDir
  Write-Host "Removed: $CacheDir"
} else {
  Write-Host "Nothing to clean: $CacheDir"
}
