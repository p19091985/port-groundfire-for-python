Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
# Groundfire Python - iniciar-all standalone Windows (ST02, PowerShell nativo).
$editionDir = $PSScriptRoot
& (Join-Path $editionDir "iniciar-server.ps1") -A @args
exit $LASTEXITCODE
