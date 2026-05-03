@echo off
setlocal
REM Script to run Groundfire using the project's virtual environment on Windows.

pushd "%~dp0"
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"
set "VENV_GROUNDFIRE=%~dp0.venv\Scripts\groundfire.exe"

call :ensure_venv
if errorlevel 1 goto :fail

"%VENV_GROUNDFIRE%" %*
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%

:ensure_venv
if exist "%VENV_PYTHON%" (
    if exist "%VENV_GROUNDFIRE%" (
        "%VENV_PYTHON%" -c "import os, sys; sys.path=[p for p in sys.path if p not in ('', os.getcwd())]; import pygame, groundfire_net; from importlib.metadata import version; version('groundfire'); raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
        if not errorlevel 1 exit /b 0
    )
    echo Ambiente virtual existente ausente do sistema, dependencias ou com Python incompativel. Reconfigurando...
) else (
    echo Ambiente virtual nao encontrado. Instalando o sistema...
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

if not exist "%VENV_GROUNDFIRE%" (
    echo Falha: o ambiente virtual nao foi criado corretamente.
    exit /b 1
)

"%VENV_PYTHON%" -c "import os, sys; sys.path=[p for p in sys.path if p not in ('', os.getcwd())]; import pygame, groundfire_net; from importlib.metadata import version; version('groundfire'); raise SystemExit(0 if (3, 10) <= sys.version_info[:2] <= (3, 13) else 1)" >nul 2>&1
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
echo Instalando Groundfire em modo editavel...
call ".venv\Scripts\python.exe" -m pip install --only-binary=pygame -e .
if not errorlevel 1 exit /b 0

echo Instalacao com wheel precompilado do pygame falhou. Tentando fallback generico...
call ".venv\Scripts\python.exe" -m pip install -e .
exit /b %ERRORLEVEL%

:fail
popd
pause
exit /b 1
