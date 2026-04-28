@echo off
REM Trading Bot Startup Script
REM This batch file starts the Autonomous Trading System

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

REM Prefer project virtual environment if available
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

REM Color codes for console output
REM This sets up color support
cls

echo.
echo ============================================================
echo          AUTONOMOUS TRADING SYSTEM - STARTUP
echo ============================================================
echo.
echo Script Location: %SCRIPT_DIR%
echo Timestamp: %date% %time%
echo.

REM Check if Python is installed
echo Checking Python installation...
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Python is not installed or not in PATH
    echo If using a virtual environment, ensure .venv\Scripts\python.exe exists.
    echo Please install Python 3.11+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

%PYTHON_CMD% --version
echo.

REM Ensure core dependencies are installed
echo Checking Python dependencies...
%PYTHON_CMD% -c "import dotenv, ccxt, pandas, numpy, statsmodels" >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependencies from requirements.txt...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERROR: Dependency installation failed.
        echo Try running manually: %PYTHON_CMD% -m pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)
echo ✓ Dependencies ready
echo.

REM Check if required files exist
echo Checking project files...
if not exist "main.py" (
    echo ERROR: main.py not found in %SCRIPT_DIR%
    echo.
    pause
    exit /b 1
)
echo ✓ main.py found
echo.

REM Check if config.py exists
if not exist "config.py" (
    echo WARNING: config.py not found. Using defaults.
) else (
    echo ✓ config.py found
)
echo.

REM Check if design_replica exists
if exist "design_replica" (
    echo ✓ Design system replica found
) else (
    echo ! Design system replica not found - optional
)
echo.

REM Start frontend web server if available
if exist "web_server.py" (
    echo Checking frontend dependencies...
    %PYTHON_CMD% -c "import flask, flask_cors" >nul 2>&1
    if errorlevel 1 (
        echo ! Flask dependencies missing - skipping frontend server
        echo   Install with: %PYTHON_CMD% -m pip install flask flask-cors
    ) else (
        echo Frontend ready at: http://127.0.0.1:5000
        echo Launch it manually in a second terminal with:
        echo   %PYTHON_CMD% web_server.py
    )
) else (
    echo Frontend server file web_server.py not found - skipping frontend.
)
echo.

REM List key directories
echo Project Structure:
if exist "data" echo   ✓ data/
if exist "strategies" echo   ✓ strategies/
if exist "execution" echo   ✓ execution/
if exist "risk" echo   ✓ risk/
if exist "backtest" echo   ✓ backtest/
if exist "monitoring" echo   ✓ monitoring/
if exist "utils" echo   ✓ utils/
echo.

echo ============================================================
echo Starting Autonomous Trading System...
echo ============================================================
echo.

REM Start the main program
%PYTHON_CMD% main.py

REM Capture exit code
set EXIT_CODE=%errorlevel%

REM Show exit status
echo.
echo ============================================================
if %EXIT_CODE% equ 0 (
    echo Application exited successfully
) else (
    echo Application exited with code: %EXIT_CODE%
)
echo ============================================================
echo.

REM Optional: Keep window open for debugging
REM Uncomment the line below to see output before window closes
REM pause

endlocal
exit /b %EXIT_CODE%
