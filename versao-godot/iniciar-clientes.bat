@echo off
setlocal EnableExtensions
rem Groundfire Godot - iniciar-clientes standalone Windows (ST04, CMD nativo).
set "EDITION_DIR=%~dp0"
if "%EDITION_DIR:~-1%"=="\" set "EDITION_DIR=%EDITION_DIR:~0,-1%"
call "%EDITION_DIR%\run_game.bat" -- %*
exit /b %ERRORLEVEL%
