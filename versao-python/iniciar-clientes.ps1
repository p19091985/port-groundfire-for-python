Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
# Groundfire Python - iniciar-clientes standalone Windows (ST02, PowerShell nativo).
$editionDir = $PSScriptRoot
$venvPy = Join-Path $editionDir ".venv\Scripts\python.exe"
if (-not $env:GROUNDFIRE_USERDATA_DIR) { $env:GROUNDFIRE_USERDATA_DIR = Join-Path $editionDir "userdata" }
$env:PYTHONPATH = "$editionDir;$editionDir\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
$env:GROUNDFIRE_EDITION_DIR = $editionDir
$runtimeCli = Join-Path $editionDir "runtime\windows\Groundfire.exe"
if ($env:GROUNDFIRE_FORCE_SOURCE -ne "1" -and (Test-Path $runtimeCli)) { & $runtimeCli @args; exit $LASTEXITCODE }
if (Test-Path $venvPy) { & $venvPy -m groundfire.client @args; exit $LASTEXITCODE }
Write-Error "Ambiente local nao encontrado. Execute ./run_game.ps1 uma vez para criar .venv dentro desta pasta."
exit 1
