@echo off
setlocal EnableExtensions
rem Groundfire Python - iniciar-server standalone Windows (ST02, CMD nativo).
set "EDITION_DIR=%~dp0"
if "%EDITION_DIR:~-1%"=="\" set "EDITION_DIR=%EDITION_DIR:~0,-1%"
set "VENV_PY=%EDITION_DIR%\.venv\Scripts\python.exe"
set "VENV_SRV=%EDITION_DIR%\.venv\Scripts\groundfire-server.exe"
if not defined GROUNDFIRE_USERDATA_DIR set "GROUNDFIRE_USERDATA_DIR=%EDITION_DIR%\userdata"
set "PYTHONPATH=%EDITION_DIR%;%EDITION_DIR%\src"
set "GROUNDFIRE_EDITION_DIR=%EDITION_DIR%"
set "RT_SRV=%EDITION_DIR%\runtime\windows\groundfire-server.exe"
if not "%GROUNDFIRE_FORCE_SOURCE%"=="1" if exist "%RT_SRV%" (
    "%RT_SRV%" %*
    exit /b %ERRORLEVEL%
)
if exist "%VENV_SRV%" (
    "%VENV_SRV%" %*
    exit /b %ERRORLEVEL%
)
if exist "%VENV_PY%" (
    "%VENV_PY%" -m groundfire.server %*
    exit /b %ERRORLEVEL%
)
echo Ambiente local nao encontrado. Execute run_game.bat uma vez para criar .venv dentro desta pasta.
exit /b 1
