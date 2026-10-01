# Windows equivalent of servico-externo.sh. All runtime files stay in this folder.
$ErrorActionPreference = 'Stop'
$serviceArgs = @($args)

function Test-ServicePython {
    param([string]$Executable, [string[]]$Prefix = @())
    try {
        & $Executable @Prefix -c 'import sys; raise SystemExit(not ((3, 11) <= sys.version_info[:2] < (3, 15)))' *> $null
        return ($LASTEXITCODE -eq 0)
    } catch {
        return $false
    }
}

function Invoke-ServiceChecked {
    param([string]$Executable, [string[]]$Arguments)
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Preparacao do servico falhou (codigo $LASTEXITCODE). Consulte a mensagem acima."
    }
}

$serviceExitCode = 3
Push-Location -LiteralPath $PSScriptRoot
try {
    $serviceVenv = Join-Path $PSScriptRoot '.venv'
    $servicePython = Join-Path $serviceVenv 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $servicePython)) {
        if (Test-Path -LiteralPath $serviceVenv) {
            throw 'A .venv local esta incompleta ou pertence a outro sistema. Mova essa pasta antes de tentar novamente; nenhum arquivo foi removido.'
        }
        $serviceBootstrap = $null
        $servicePrefix = @()
        if ($env:GF_SERVICE_PYTHON) {
            if (-not (Test-ServicePython $env:GF_SERVICE_PYTHON)) {
                throw 'GF_SERVICE_PYTHON deve apontar para um executavel Python 3.11 a 3.14, sem argumentos.'
            }
            $serviceBootstrap = $env:GF_SERVICE_PYTHON
        } else {
            if (Get-Command py.exe -ErrorAction SilentlyContinue) {
                foreach ($version in @('3.14', '3.13', '3.12', '3.11')) {
                    if (Test-ServicePython 'py.exe' @("-$version")) {
                        $serviceBootstrap = 'py.exe'
                        $servicePrefix = @("-$version")
                        break
                    }
                }
            }
            if (-not $serviceBootstrap) {
                foreach ($candidate in @('python.exe', 'python3.exe')) {
                    if (Test-ServicePython $candidate) {
                        $serviceBootstrap = $candidate
                        break
                    }
                }
            }
        }
        if (-not $serviceBootstrap) {
            throw 'Python 3.11 a 3.14 nao encontrado. Instale Python ou defina GF_SERVICE_PYTHON.'
        }
        Write-Host 'Criando ambiente virtual local do servico...'
        Invoke-ServiceChecked $serviceBootstrap ($servicePrefix + @('-m', 'venv', $serviceVenv))
    }
    if (-not (Test-ServicePython $servicePython)) {
        throw 'O Python da .venv local nao funciona ou esta fora das versoes 3.11 a 3.14.'
    }

    & $servicePython -c 'import importlib.util, sys; raise SystemExit(any(importlib.util.find_spec(name) is None for name in sys.argv[1:]))' fastapi uvicorn argon2 gf_service
    if ($LASTEXITCODE -ne 0) {
        Invoke-ServiceChecked $servicePython @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', 'requirements.lock')
        Invoke-ServiceChecked $servicePython @('-m', 'pip', 'install', '--disable-pip-version-check', '-e', '.', '--no-deps')
    }
    if ($serviceArgs.Count -gt 0 -and $serviceArgs[0] -eq 'test') {
        & $servicePython -c 'import importlib.util, sys; raise SystemExit(any(importlib.util.find_spec(name) is None for name in sys.argv[1:]))' pytest httpx
        if ($LASTEXITCODE -ne 0) {
            Invoke-ServiceChecked $servicePython @('-m', 'pip', 'install', '--disable-pip-version-check', '-r', 'requirements-test.lock')
        }
        $serviceTestArgs = @($serviceArgs | Select-Object -Skip 1)
        & $servicePython -m pytest @serviceTestArgs
    } else {
        & $servicePython -m gf_service @serviceArgs
    }
    $serviceExitCode = $LASTEXITCODE
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
} finally {
    Pop-Location
}
exit $serviceExitCode
