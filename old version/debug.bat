@echo off
REM Trading Bot - Development/Debug Mode
REM This batch file starts the bot in debug mode with extra output

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

cls

echo.
echo ============================================================
echo     AUTONOMOUS TRADING SYSTEM - DEVELOPMENT MODE
echo ============================================================
echo.
echo This mode provides extra debugging information
echo The console will remain open for inspection
echo.
echo Press Ctrl+C to stop the application
echo.
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    echo.
    pause
    exit /b 1
)

echo Python Version:
python --version
echo.

echo System Information:
echo   Script Directory: %SCRIPT_DIR%
echo   Current Time: %date% %time%
echo   Platform: %OS%
echo.

echo Project Files:
if exist "main.py" echo   ✓ main.py
if exist "config.py" echo   ✓ config.py
if exist "utils" echo   ✓ utils/
if exist "design_integration.py" echo   ✓ design_integration.py
echo.

echo Starting application in DEBUG mode...
echo ============================================================
echo.

REM Run with verbose output
python -u main.py

set EXIT_CODE=%errorlevel%

echo.
echo ============================================================
echo DEBUG MODE ENDED
echo Exit Code: %EXIT_CODE%
echo ============================================================
echo.

REM Always pause in debug mode for inspection
pause

endlocal
exit /b %EXIT_CODE%
