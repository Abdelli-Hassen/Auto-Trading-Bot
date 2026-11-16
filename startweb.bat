@echo off
rem NexTrade AI - paper trading launcher (backend :8000, frontend :3000)
setlocal
cd /d %~dp0
set PYTHON_CMD=python
if exist ".venv\Scripts\python.exe" set PYTHON_CMD=.venv\Scripts\python.exe

if not exist "ReactFront\trading_bot\node_modules" (
    echo Installing frontend dependencies...
    pushd ReactFront\trading_bot
    call npm install
    popd
)
start "Trading Bot API" cmd /k "%PYTHON_CMD% -m uvicorn api.server:app --host 127.0.0.1 --port 8000"
start "Trading Bot UI" cmd /k "cd /d %~dp0ReactFront\trading_bot && npm start"
timeout /t 3 /nobreak >nul
start http://localhost:3000
endlocal
