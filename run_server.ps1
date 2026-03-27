# Script to run the standalone Groundfire dedicated server UI using the project's virtual environment on Windows.

Push-Location $PSScriptRoot
$script:venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$script:versionCheck = "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)"
$script:runtimeCheck = "import sys, pygame; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)"

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
    if ((Test-Path $script:venvPython) -and (Test-Interpreter -Command $script:venvPython -Code $script:runtimeCheck)) {
        return $true
    }

    if (Test-Path $script:venvPython) {
        Write-Host "Ambiente virtual existente ausente de dependencias ou com Python incompativel. Reconfigurando..."
    }
    else {
        Write-Host "Ambiente virtual nao encontrado. Instalando dependencias..."
    }

    $interpreter = Get-CompatibleInterpreter
    if (-not $interpreter) {
        Write-Error "Python compativel nao encontrado no PATH. Use Python 3.10, 3.11, 3.12 ou 3.13."
        return $false
    }

    Write-Host "Usando interpretador: $($interpreter.Display)"

    if ((Test-Path $script:venvPython) -and -not (Test-Interpreter -Command $script:venvPython)) {
        Write-Host "Ambiente virtual existente usa um Python incompativel. Recriando a .venv..."
        Remove-Item (Join-Path $PSScriptRoot ".venv") -Recurse -Force
    }

    if (-not (Test-Path $script:venvPython)) {
        Write-Host "Criando ambiente virtual..."
        & $interpreter.Command @($interpreter.Arguments + @("-m", "venv", ".venv"))
        if ($LASTEXITCODE -ne 0) {
            return $false
        }
    }

    Write-Host "Atualizando pip..."
    & $script:venvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    Write-Host "Instalando dependencias..."
    & $script:venvPython -m pip install --only-binary=pygame -r (Join-Path $PSScriptRoot "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    if (-not ((Test-Path $script:venvPython) -and (Test-Interpreter -Command $script:venvPython -Code $script:runtimeCheck))) {
        Write-Error "Falha: o ambiente virtual nao foi criado corretamente."
        return $false
    }

    return $true
}

if (-not (Ensure-GameEnvironment)) {
    Pop-Location
    exit 1
}

& $script:venvPython -m interface_net.server.demo
$exitCode = $LASTEXITCODE
Pop-Location
exit $exitCode
