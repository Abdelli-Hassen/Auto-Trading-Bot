@echo off
REM Start native Python desktop interface + trading bot

setlocal
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

REM Prefer virtualenv Python when available
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

echo ============================================================
echo      PYTHON DESKTOP UI + BOT STARTUP
echo ============================================================
echo.

REM Ensure dependencies for the desktop app exist
%PYTHON_CMD% -c "import dotenv, ccxt, pandas, numpy, statsmodels, PySide6" >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependencies from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Dependency installation failed.
        pause
        exit /b 1
    )
)

REM Launch native desktop UI window
if exist "design_python_desktop.py" (
    start "Design Python Desktop UI" cmd /k "%PYTHON_CMD% design_python_desktop.py"
) else (
    echo design_python_desktop.py not found.
)

REM Launch trading bot window
if exist "start.bat" (
    start "Trading Bot Engine" cmd /k "start.bat"
) else (
    echo start.bat not found.
)

echo Started:
echo   - Desktop UI: native Python window
echo   - Bot engine: separate terminal window
echo.

endlocal
exit /b 0
