Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
# Groundfire Godot - iniciar-all standalone Windows (ST04, PowerShell nativo).
$editionDir = $PSScriptRoot
Start-Process -FilePath (Join-Path $editionDir "iniciar-server.ps1") -ArgumentList @args
Start-Process -FilePath (Join-Path $editionDir "run_game.ps1") -ArgumentList @("--", @args)
exit 0
