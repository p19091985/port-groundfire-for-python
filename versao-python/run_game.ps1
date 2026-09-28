Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Groundfire Python edition — launcher standalone (ST01/ST02).
# Usa somente arquivos dentro desta pasta (versao-python/).

$script:editionDir = $PSScriptRoot
$script:venvPython = Join-Path $script:editionDir ".venv\Scripts\python.exe"
$script:venvGroundfire = Join-Path $script:editionDir ".venv\Scripts\groundfire.exe"
if ($env:GROUNDFIRE_USERDATA_DIR) { $script:userdataDir = $env:GROUNDFIRE_USERDATA_DIR } else { $script:userdataDir = Join-Path $script:editionDir "userdata" }
$script:versionCheck = "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 14) else 1)"
$script:runtimeCheck = "import os, sys; sys.path=[p for p in sys.path if p not in ('', os.getcwd())]; import pygame, groundfire_net; from importlib.metadata import version; version('groundfire'); raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 14) else 1)"

function Test-UserdataWritable {
    try { New-Item -ItemType Directory -Force -Path $script:userdataDir | Out-Null } catch {
        Write-Error "Erro: pasta userdata nao e gravavel: $script:userdataDir"
        return $false
    }
    $probe = Join-Path $script:userdataDir ".writetest"
    try { Set-Content -Path $probe -Value "ok" -Encoding Ascii } catch {
        Write-Error "Erro: pasta userdata nao e gravavel: $script:userdataDir"
        return $false
    }
    Remove-Item $probe -Force -ErrorAction SilentlyContinue
    return $true
}

function Get-RuntimeBinary {
    $winBin = Join-Path $script:editionDir "runtime\windows\Groundfire.exe"
    $linuxBin = Join-Path $script:editionDir "runtime\linux\Groundfire"
    if (Test-Path $winBin) { return $winBin }
    if (Test-Path $linuxBin) { return $linuxBin }
    return $null
}

function Test-Interpreter {
    param(
        [string]$Command,
        [string[]]$Arguments = @(),
        [string]$Code = $script:versionCheck
    )
    & $Command @Arguments -c $Code *> $null
    return $LASTEXITCODE -eq 0
}

function Get-CompatibleInterpreter {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($version in "3.14", "3.13", "3.12", "3.11", "3.10") {
            if (Test-Interpreter -Command "py" -Arguments @("-$version")) {
                return @{ Command = "py"; Arguments = @("-$version"); Display = "py -$version" }
            }
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (Test-Interpreter -Command "python") {
            return @{ Command = "python"; Arguments = @(); Display = "python" }
        }
    }
    return $null
}

function Ensure-GameEnvironment {
    if ((Test-Path $script:venvPython) -and (Test-Path $script:venvGroundfire) -and (Test-Interpreter -Command $script:venvPython -Code $script:runtimeCheck)) {
        return $true
    }
    if (Test-Path $script:venvPython) {
        Write-Host "Ambiente virtual existente ausente do sistema, dependencias ou com Python incompativel. Reconfigurando..."
    } else {
        Write-Host "Ambiente virtual nao encontrado. Instalando o sistema..."
    }
    $interpreter = Get-CompatibleInterpreter
    if (-not $interpreter) {
        Write-Error "Python compativel nao encontrado no PATH. Use Python 3.10, 3.11, 3.12, 3.13 ou 3.14."
        return $false
    }
    Write-Host "Usando interpretador: $($interpreter.Display)"
    if ((Test-Path $script:venvPython) -and -not (Test-Interpreter -Command $script:venvPython)) {
        Write-Host "Ambiente virtual existente usa um Python incompativel. Recriando a .venv..."
        Remove-Item (Join-Path $script:editionDir ".venv") -Recurse -Force
    }
    if (-not (Test-Path $script:venvPython)) {
        Write-Host "Criando ambiente virtual..."
        & $interpreter.Command @($interpreter.Arguments + @("-m", "venv", (Join-Path $script:editionDir ".venv")))
        if ($LASTEXITCODE -ne 0) { return $false }
    }
    if ($env:GROUNDFIRE_SKIP_PIP_UPGRADE -eq "1") {
        Write-Host "Upgrade de pip ignorado por GROUNDFIRE_SKIP_PIP_UPGRADE=1."
    } else {
        Write-Host "Atualizando pip..."
        & $script:venvPython -m pip install --upgrade pip
        if ($LASTEXITCODE -ne 0) { return $false }
    }
    if (-not (Install-GameProject)) { return $false }
    if (-not ((Test-Path $script:venvPython) -and (Test-Path $script:venvGroundfire) -and (Test-Interpreter -Command $script:venvPython -Code $script:runtimeCheck))) {
        Write-Error "Falha: o ambiente virtual nao foi criado corretamente."
        return $false
    }
    return $true
}

function Install-GameProject {
    Write-Host "Instalando Groundfire (edicao versao-python) em modo editavel..."
    & $script:venvPython -m pip install --only-binary=pygame -e $script:editionDir
    if ($LASTEXITCODE -eq 0) { return $true }
    Write-Host "Instalacao com wheel precompilado do pygame falhou. Tentando fallback generico..."
    & $script:venvPython -m pip install -e $script:editionDir
    return $LASTEXITCODE -eq 0
}

if (-not (Test-UserdataWritable)) { exit 1 }

# Pacote portatil (ST02): binario interno sem Python/pip/rede.
$runtimeBin = Get-RuntimeBinary
if ($runtimeBin -and $env:GROUNDFIRE_FORCE_SOURCE -ne "1") {
    $env:GROUNDFIRE_EDITION_DIR = $script:editionDir
    $env:GROUNDFIRE_USERDATA_DIR = $script:userdataDir
    & $runtimeBin @args
    exit $LASTEXITCODE
}

$exitCode = 0
Push-Location $script:editionDir
try {
    if (-not (Ensure-GameEnvironment)) { exit 1 }
    $env:PYTHONPATH = "$script:editionDir;$script:editionDir\src" + ($(if ($env:PYTHONPATH) { ";$env:PYTHONPATH" } else { "" }))
    $env:GROUNDFIRE_EDITION_DIR = $script:editionDir
    $env:GROUNDFIRE_USERDATA_DIR = $script:userdataDir
    & $script:venvGroundfire @args
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $exitCode
