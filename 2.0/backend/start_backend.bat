@echo off
title KernelSense Backend Server (Interactive Desktop Session)
echo ============================================================
echo  Starting KernelSense Python ML/AI Backend (Interactive Mode)
echo ============================================================
cd /d "%~dp0"
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
pause
