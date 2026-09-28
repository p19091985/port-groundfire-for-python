@echo off
setlocal EnableExtensions
rem Groundfire Python - iniciar-all standalone Windows (ST02, CMD nativo).
set "EDITION_DIR=%~dp0"
if "%EDITION_DIR:~-1%"=="\" set "EDITION_DIR=%EDITION_DIR:~0,-1%"
call "%EDITION_DIR%\iniciar-server.bat" -A %*
exit /b %ERRORLEVEL%
