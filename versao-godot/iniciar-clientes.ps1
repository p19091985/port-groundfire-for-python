Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
# Groundfire Godot - iniciar-clientes standalone Windows (ST04, PowerShell nativo).
$editionDir = $PSScriptRoot
& (Join-Path $editionDir "run_game.ps1") -- @args
exit $LASTEXITCODE
