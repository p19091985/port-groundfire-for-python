Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:repoRoot = Split-Path -Parent $PSScriptRoot
$script:venvPython = Join-Path $script:repoRoot ".venv\Scripts\python.exe"
$script:venvGroundfire = Join-Path $script:repoRoot ".venv\Scripts\groundfire.exe"
$script:versionCheck = "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)"
$script:runtimeCheck = "import os, sys; sys.path=[p for p in sys.path if p not in ('', os.getcwd())]; import pygame, groundfire_net; from importlib.metadata import version; version('groundfire'); raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)"

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
        foreach ($version in "3.13", "3.12", "3.11", "3.10") {
            if (Test-Interpreter -Command "py" -Arguments @("-$version")) {
                return @{
                    Command = "py"
                    Arguments = @("-$version")
                    Display = "py -$version"
                }
            }
        }
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        if (Test-Interpreter -Command "python") {
            return @{
                Command = "python"
                Arguments = @()
                Display = "python"
            }
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
    }
    else {
        Write-Host "Ambiente virtual nao encontrado. Instalando o sistema..."
    }

    $interpreter = Get-CompatibleInterpreter
    if (-not $interpreter) {
        Write-Error "Python compativel nao encontrado no PATH. Use Python 3.10, 3.11, 3.12 ou 3.13."
        return $false
    }

    Write-Host "Usando interpretador: $($interpreter.Display)"

    if ((Test-Path $script:venvPython) -and -not (Test-Interpreter -Command $script:venvPython)) {
        Write-Host "Ambiente virtual existente usa um Python incompativel. Recriando a .venv..."
        Remove-Item (Join-Path $script:repoRoot ".venv") -Recurse -Force
    }

    if (-not (Test-Path $script:venvPython)) {
        Write-Host "Criando ambiente virtual..."
        & $interpreter.Command @($interpreter.Arguments + @("-m", "venv", ".venv"))
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
    }

    if ($env:GROUNDFIRE_SKIP_PIP_UPGRADE -eq "1") {
        Write-Host "Upgrade de pip ignorado por GROUNDFIRE_SKIP_PIP_UPGRADE=1."
    }
    else {
        Write-Host "Atualizando pip..."
        & $script:venvPython -m pip install --upgrade pip
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
    }

    if (-not (Install-GameProject)) {
        return $false
    }

    if (-not ((Test-Path $script:venvPython) -and (Test-Path $script:venvGroundfire) -and (Test-Interpreter -Command $script:venvPython -Code $script:runtimeCheck))) {
        Write-Error "Falha: o ambiente virtual nao foi criado corretamente."
        return $false
    }

    return $true
}

function Install-GameProject {
    Write-Host "Instalando Groundfire em modo editavel..."
    & $script:venvPython -m pip install --only-binary=pygame -e $script:repoRoot
    if ($LASTEXITCODE -eq 0) {
        return $true
    }

    Write-Host "Instalacao com wheel precompilado do pygame falhou. Tentando fallback generico..."
    & $script:venvPython -m pip install -e $script:repoRoot
    return $LASTEXITCODE -eq 0
}

$exitCode = 0
Push-Location $script:repoRoot
try {
    if (-not (Ensure-GameEnvironment)) {
        exit 1
    }

    & $script:venvGroundfire @args
    $exitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}
exit $exitCode
