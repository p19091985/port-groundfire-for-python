@echo off
setlocal EnableExtensions
rem Launcher Windows nativo; nao requer Git Bash ou WSL.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0servico-externo.ps1" %*
exit /b %ERRORLEVEL%
