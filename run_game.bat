@echo off
setlocal
REM Script to run Groundfire using the project's virtual environment on Windows.

pushd "%~dp0"
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"

call :ensure_venv
if errorlevel 1 goto :fail

"%VENV_PYTHON%" "%~dp0src\main.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%

:ensure_venv
if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" -c "import sys, pygame, msgpack; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
    if not errorlevel 1 exit /b 0
    echo Ambiente virtual existente ausente de dependencias ou com Python incompativel. Reconfigurando...
) else (
    echo Ambiente virtual nao encontrado. Instalando dependencias...
)

call :find_python
if errorlevel 1 exit /b 1

echo Usando interpretador: %PYTHON_CMD%

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
    if errorlevel 1 (
        echo Ambiente virtual existente usa um Python incompativel. Recriando a .venv...
        rmdir /s /q ".venv"
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo Criando ambiente virtual...
    call %PYTHON_CMD% -m venv .venv
    if errorlevel 1 exit /b 1
)

echo Atualizando pip...
call ".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1

call :install_requirements
if errorlevel 1 exit /b 1

if not exist "%VENV_PYTHON%" (
    echo Falha: o ambiente virtual nao foi criado corretamente.
    exit /b 1
)

"%VENV_PYTHON%" -c "import sys, pygame, msgpack; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
if errorlevel 1 (
    echo Falha: o ambiente virtual nao foi criado corretamente.
    exit /b 1
)

exit /b 0

:find_python
set "PYTHON_CMD="

where py >nul 2>&1
if not errorlevel 1 (
    call :try_py_launcher 3.13
    if defined PYTHON_CMD exit /b 0
    call :try_py_launcher 3.12
    if defined PYTHON_CMD exit /b 0
    call :try_py_launcher 3.11
    if defined PYTHON_CMD exit /b 0
    call :try_py_launcher 3.10
    if defined PYTHON_CMD exit /b 0
)

where python >nul 2>&1
if not errorlevel 1 (
    python -c "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
        exit /b 0
    )
)

echo Python compativel nao encontrado no PATH.
echo Use Python 3.10, 3.11, 3.12 ou 3.13.
exit /b 1

:try_py_launcher
py -%~1 -c "import sys; raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
if errorlevel 1 exit /b 0
set "PYTHON_CMD=py -%~1"
exit /b 0

:install_requirements
echo Instalando dependencias...
call ".venv\Scripts\python.exe" -m pip install --only-binary=pygame -r requirements.txt
if not errorlevel 1 exit /b 0

echo Instalacao com wheel precompilado do pygame falhou. Tentando fallback generico...
call ".venv\Scripts\python.exe" -m pip install -r requirements.txt
exit /b %ERRORLEVEL%

:fail
popd
pause
exit /b 1
