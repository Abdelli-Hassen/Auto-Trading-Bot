@echo off
REM Trading Bot - Backtest Runner
REM This batch file runs backtesting for the trading system

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

cls

echo.
echo ============================================================
echo          TRADING SYSTEM - BACKTEST MODE
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

REM Check for run_backtest.py
if not exist "run_backtest.py" (
    echo ERROR: run_backtest.py not found
    echo.
    pause
    exit /b 1
)

echo Starting backtest...
echo.

python run_backtest.py

set EXIT_CODE=%errorlevel%

echo.
echo ============================================================
if %EXIT_CODE% equ 0 (
    echo Backtest completed successfully
    echo.
    echo Results saved to:
    if exist "backtest_equity.csv" echo   - backtest_equity.csv
    if exist "backtest_trades.csv" echo   - backtest_trades.csv
) else (
    echo Backtest failed with code: %EXIT_CODE%
)
echo ============================================================
echo.

REM Uncomment to keep window open
REM pause

endlocal
exit /b %EXIT_CODE%
