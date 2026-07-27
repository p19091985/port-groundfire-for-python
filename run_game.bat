@echo off
set "SCRIPT_DIR=%~dp0"
if not exist "%SCRIPT_DIR%versao-python\run_game.bat" (
    echo Falha: launcher Python nao encontrado: "%SCRIPT_DIR%versao-python\run_game.bat"
    exit /b 1
)
call "%SCRIPT_DIR%versao-python\run_game.bat" %*
exit /b %ERRORLEVEL%
