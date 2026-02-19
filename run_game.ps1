# Script to run Groundfire using Python on Windows (PowerShell)
# Equivalent to run_game.sh for Linux

Push-Location $PSScriptRoot
python src\main.py
Pop-Location
