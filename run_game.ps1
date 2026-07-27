Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Target = Join-Path $ScriptDir "versao-python/run_game.ps1"
if (-not (Test-Path $Target)) {
    Write-Error "Falha: launcher Python nao encontrado: $Target"
    exit 1
}
& $Target @args
exit $LASTEXITCODE
