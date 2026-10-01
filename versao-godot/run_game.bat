@echo off
setlocal EnableExtensions
rem Groundfire Godot edition - launcher standalone Windows (ST03, sem Git Bash).
set "EDITION_DIR=%~dp0"
if "%EDITION_DIR:~-1%"=="\" set "EDITION_DIR=%EDITION_DIR:~0,-1%"
if not defined GROUNDFIRE_USERDATA_DIR set "GROUNDFIRE_USERDATA_DIR=%EDITION_DIR%\userdata"
mkdir "%GROUNDFIRE_USERDATA_DIR%" 2>nul
del "%GROUNDFIRE_USERDATA_DIR%\.writetest" 2>nul
echo ok > "%GROUNDFIRE_USERDATA_DIR%\.writetest" 2>nul
if not exist "%GROUNDFIRE_USERDATA_DIR%\.writetest" (
    echo Erro: pasta userdata nao e gravavel: %GROUNDFIRE_USERDATA_DIR%
    exit /b 1
)
del "%GROUNDFIRE_USERDATA_DIR%\.writetest" 2>nul

set "GODOT_BIN_CANDIDATE="
if exist "%EDITION_DIR%\runtime\windows\Groundfire.exe" set "GODOT_BIN_CANDIDATE=%EDITION_DIR%\runtime\windows\Groundfire.exe"
if not defined GODOT_BIN_CANDIDATE if exist "%EDITION_DIR%\runtime\windows\Godot.exe" set "GODOT_BIN_CANDIDATE=%EDITION_DIR%\runtime\windows\Godot.exe"
if defined GODOT_BIN if exist "%GODOT_BIN%" set "GODOT_BIN_CANDIDATE=%GODOT_BIN%"
rem Checkout de desenvolvimento: reutiliza a engine instalada no repositorio.
rem A edicao copiada sozinha continua usando runtime\windows ou GODOT_BIN.
if not defined GODOT_BIN_CANDIDATE if exist "%EDITION_DIR%\..\tools\godot\Godot.exe" set "GODOT_BIN_CANDIDATE=%EDITION_DIR%\..\tools\godot\Godot.exe"
if not defined GODOT_BIN_CANDIDATE (
    for %%G in ("%EDITION_DIR%\..\tools\godot\Godot_v*_win64_console.exe") do if exist "%%~fG" set "GODOT_BIN_CANDIDATE=%%~fG"
)
if not defined GODOT_BIN_CANDIDATE (
    for %%G in ("%EDITION_DIR%\..\tools\godot\Godot_v*_win64.exe") do if exist "%%~fG" set "GODOT_BIN_CANDIDATE=%%~fG"
)
if not defined GODOT_BIN_CANDIDATE (
    where godot >nul 2>&1
    if not errorlevel 1 set "GODOT_BIN_CANDIDATE=godot"
)
if not defined GODOT_BIN_CANDIDATE (
    echo Godot nao encontrado. Coloque Godot.exe em runtime\windows\, instale em tools\godot\ no repositorio ou defina GODOT_BIN.
    exit /b 1
)
"%GODOT_BIN_CANDIDATE%" --path "%EDITION_DIR%\godot" %*
exit /b %ERRORLEVEL%
