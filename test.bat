@echo off
REM Trading Bot - Test Suite Runner
REM This batch file runs all system tests

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

cls

echo.
echo ============================================================
echo          TRADING SYSTEM - TEST SUITE
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

echo Available Tests:
echo.
if exist "test_system.py" echo   1. test_system.py - System integration tests
if exist "test_design_system.py" echo   2. test_design_system.py - Design system tests
echo.

echo Running Design System Tests...
echo ============================================================
echo.

if exist "test_design_system.py" (
    python test_design_system.py
    set DESIGN_TEST_EXIT=%errorlevel%
) else (
    echo test_design_system.py not found
    set DESIGN_TEST_EXIT=1
)

echo.
echo Running System Tests...
echo ============================================================
echo.

if exist "test_system.py" (
    python test_system.py
    set SYSTEM_TEST_EXIT=%errorlevel%
) else (
    echo test_system.py not found
    set SYSTEM_TEST_EXIT=1
)

echo.
echo ============================================================
echo TEST SUMMARY
echo ============================================================
if %DESIGN_TEST_EXIT% equ 0 (
    echo ✓ Design System Tests: PASSED
) else (
    echo ✗ Design System Tests: FAILED
)

if %SYSTEM_TEST_EXIT% equ 0 (
    echo ✓ System Tests: PASSED
) else (
    echo ✗ System Tests: FAILED
)
echo ============================================================
echo.

REM Uncomment to keep window open
REM pause

endlocal
exit /b 0
