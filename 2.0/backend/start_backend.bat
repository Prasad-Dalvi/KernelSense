@echo off
title KernelSense Backend Server (Interactive Desktop Session)
echo ============================================================
echo  Starting KernelSense Python ML/AI Backend (Interactive Mode)
echo ============================================================
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Creating Python virtual environment...
    py -3 -m venv ".venv"
    if errorlevel 1 exit /b 1
)
".venv\Scripts\python.exe" -m pip install -r "requirements.txt"
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
