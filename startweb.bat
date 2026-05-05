@echo off
rem ============================================================
rem  AI Trading Terminal - Web Launcher
rem  Starts the FastAPI backend + React frontend simultaneously
rem ============================================================

setlocal
set SCRIPT_DIR=%~dp0
cd /d %SCRIPT_DIR%

rem Prefer virtualenv Python when available
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" (
    set PYTHON_CMD=.venv\Scripts\python.exe
)

echo.
echo  ========================================
echo   AI Trading Terminal - Web Interface
echo  ========================================
echo.

rem Start FastAPI backend on port 8000
echo [1/2] Starting FastAPI backend on http://localhost:8000 ...
start "Trading Bot API" cmd /k "%PYTHON_CMD% -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload"

rem Give the backend a moment to boot
timeout /t 3 /nobreak >nul

rem Build Tailwind CSS to output.css first to avoid Webpack PostCSS hangs
echo [2/3] Building Tailwind CSS...
start /b "Tailwind Build" cmd /c "cd /d %SCRIPT_DIR%ReactFront\trading_bot && npm run tailwind:build"

rem Give Tailwind a moment to compile
timeout /t 2 /nobreak >nul

rem Start React frontend on port 3000
echo [3/3] Starting React frontend on http://localhost:3000 ...
start "Trading Bot UI" cmd /k "cd /d %SCRIPT_DIR%ReactFront\trading_bot && npm start"

rem Wait for React dev server to compile
timeout /t 5 /nobreak >nul

rem Open the browser
echo.
echo Opening browser...
start http://localhost:3000

echo.
echo  Both servers are running in separate windows.
echo  Close those windows to stop the servers.
echo.

endlocal
