@echo off
rem Launch trading bot engine (main.py)

setlocal
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

rem Prefer virtualenv Python when available
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

rem Run the bot
%PYTHON_CMD% main.py
endlocal
