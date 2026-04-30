@echo off
REM Full startup script: launches frontend + bot in separate windows

setlocal
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

REM Prefer project virtual environment if available
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

echo ============================================================
echo      AUTONOMOUS TRADING SYSTEM - FULL STARTUP
echo ============================================================
echo.
echo Launching frontend and bot in separate windows...
echo.

REM Frontend window (if available)
if exist "web_server.py" (
    start "Trading Bot Frontend" cmd /k "%PYTHON_CMD% web_server.py"
) else (
    echo web_server.py not found, frontend not launched.
)

REM Bot window
if exist "start.bat" (
    start "Trading Bot Engine" cmd /k "start.bat"
) else (
    echo start.bat not found, bot not launched.
)

echo Done. You should now see:
echo   - Trading Bot Frontend window
echo   - Trading Bot Engine window
echo.

endlocal
exit /b 0
