Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
# Groundfire Godot - iniciar-server standalone Windows (ST04, PowerShell nativo).
$editionDir = $PSScriptRoot
if (-not $env:GROUNDFIRE_USERDATA_DIR) { $env:GROUNDFIRE_USERDATA_DIR = Join-Path $editionDir "userdata" }
$env:PYTHONPATH = "$editionDir\runtime\headless;$editionDir\runtime\headless\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$companion = Join-Path $editionDir "runtime\windows\groundfire-server.exe"
if (Test-Path $companion) { & $companion @args; exit $LASTEXITCODE }
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python 3.10 ou superior nao encontrado para o companion LAN."
    exit 1
}
& python -m groundfire.server @args
exit $LASTEXITCODE
