Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
# Groundfire Python - iniciar-server standalone Windows (ST02, PowerShell nativo).
$editionDir = $PSScriptRoot
$venvPy = Join-Path $editionDir ".venv\Scripts\python.exe"
$venvSrv = Join-Path $editionDir ".venv\Scripts\groundfire-server.exe"
if (-not $env:GROUNDFIRE_USERDATA_DIR) { $env:GROUNDFIRE_USERDATA_DIR = Join-Path $editionDir "userdata" }
$env:PYTHONPATH = "$editionDir;$editionDir\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$env:GROUNDFIRE_EDITION_DIR = $editionDir
$runtimeSrv = Join-Path $editionDir "runtime\windows\groundfire-server.exe"
if ($env:GROUNDFIRE_FORCE_SOURCE -ne "1" -and (Test-Path $runtimeSrv)) { & $runtimeSrv @args; exit $LASTEXITCODE }
if (Test-Path $venvSrv) { & $venvSrv @args; exit $LASTEXITCODE }
if (Test-Path $venvPy) { & $venvPy -m groundfire.server @args; exit $LASTEXITCODE }
Write-Error "Ambiente local nao encontrado. Execute ./run_game.ps1 uma vez para criar .venv dentro desta pasta."
exit 1
