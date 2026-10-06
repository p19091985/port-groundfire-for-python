@echo off
setlocal EnableExtensions
rem Launcher Windows nativo; nao requer Git Bash ou WSL.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0groundfire-online-service.ps1" %*
exit /b %ERRORLEVEL%
