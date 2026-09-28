@echo off
setlocal EnableExtensions
rem Groundfire Godot - iniciar-all standalone Windows (ST04, CMD nativo).
set "EDITION_DIR=%~dp0"
if "%EDITION_DIR:~-1%"=="\" set "EDITION_DIR=%EDITION_DIR:~0,-1%"
start "Groundfire Godot Server" "%EDITION_DIR%\iniciar-server.bat" %*
start "Groundfire Godot Clients" "%EDITION_DIR%\iniciar-clientes.bat" %*
exit /b 0
