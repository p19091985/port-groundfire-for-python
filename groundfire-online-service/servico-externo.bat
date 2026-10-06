@echo off
setlocal EnableExtensions
call "%~dp0groundfire-online-service.bat" %*
exit /b %ERRORLEVEL%
