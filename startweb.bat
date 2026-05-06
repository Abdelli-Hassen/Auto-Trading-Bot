@echo off
rem ============================================================
rem  AI Trading Terminal - Optimized Web Launcher
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
echo  [⚡] ----------------------------------------
echo  [⚡]   AI Trading Terminal - Fast Launch
echo  [⚡] ----------------------------------------
echo.

rem 1. Start FastAPI backend (Port 8000)
echo [1/3] Launching Backend Engine...
start "Trading Bot API" cmd /c "%PYTHON_CMD% -m uvicorn api.server:app --host 127.0.0.1 --port 8000"

rem 2. Start Tailwind CSS Watcher (in background)
echo [2/3] Initializing Design System (Tailwind)...
start /b "Tailwind Watcher" cmd /c "cd /d %SCRIPT_DIR%ReactFront\trading_bot && npx @tailwindcss/cli -i ./src/index.css -o ./src/output.css --watch"

rem 3. Start React frontend (Port 3000)
echo [3/3] Starting Vite Dev Server...
start "Trading Bot UI" cmd /c "cd /d %SCRIPT_DIR%ReactFront\trading_bot && npm start"

rem Open the browser much faster (Vite is near-instant)
echo.
echo [⚡] Opening dashboard...
timeout /t 1 /nobreak >nul
start http://localhost:3000

echo.
echo  [SUCCESS] All systems active.
echo  Vite is now handling the frontend with ultra-fast startup.
echo.

endlocal
