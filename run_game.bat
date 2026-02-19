@echo off
REM Script to run Groundfire using Python on Windows
REM Equivalent to run_game.sh for Linux

pushd "%~dp0"
python src\main.py
popd
