@echo off
cd /d "%~dp0\.."
start "" cmd /k "cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8080"
timeout /t 2 /nobreak >nul
start "" cmd /k "cd frontend && npm run dev"
timeout /t 3 /nobreak >nul
start http://localhost:5173