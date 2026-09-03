@echo off
title KernelSense Full-Stack Launcher
echo ============================================================
echo   Launching KernelSense Platform (Interactive Desktop Mode)
echo ============================================================

start "KernelSense Backend (Python ML)" cmd /c "cd /d %~dp0backend && python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
start "KernelSense Frontend (Vite)" cmd /c "cd /d %~dp0frontend && npm run dev"

echo.
echo Both Frontend (http://localhost:5173) and Backend (http://127.0.0.1:8000) are starting!
echo Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul
start http://localhost:5173
