@echo off
setlocal EnableExtensions
rem Groundfire Godot - iniciar-server standalone Windows (ST04, CMD nativo, sem Git Bash).
set "EDITION_DIR=%~dp0"
if "%EDITION_DIR:~-1%"=="\" set "EDITION_DIR=%EDITION_DIR:~0,-1%"
if not defined GROUNDFIRE_USERDATA_DIR set "GROUNDFIRE_USERDATA_DIR=%EDITION_DIR%\userdata"
set "PYTHONPATH=%EDITION_DIR%\runtime\headless;%EDITION_DIR%\runtime\headless\src"
if exist "%EDITION_DIR%\runtime\windows\groundfire-server.exe" (
    "%EDITION_DIR%\runtime\windows\groundfire-server.exe" %*
    exit /b %ERRORLEVEL%
)
where python >nul 2>&1
if errorlevel 1 (
    echo Python 3.10 ou superior nao encontrado para o companion LAN.
    exit /b 1
)
python "%EDITION_DIR%\scripts\check_udp_server.py" --help >nul 2>&1
python -m groundfire.server %*
exit /b %ERRORLEVEL%
