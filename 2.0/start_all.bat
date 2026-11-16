@echo off
title KernelSense Full-Stack Launcher
echo ============================================================
echo   Launching KernelSense Platform (Interactive Desktop Mode)
echo ============================================================

set "BACKEND_DIR=%~dp0backend"
set "FRONTEND_DIR=%~dp0frontend"
set "VENV_DIR=%BACKEND_DIR%\.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo Creating Python virtual environment...
    py -3 -m venv "%VENV_DIR%"
    if errorlevel 1 exit /b 1
)

echo Installing/verifying backend dependencies...
"%VENV_PYTHON%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 exit /b 1

if not exist "%FRONTEND_DIR%\node_modules" (
    echo Installing frontend dependencies...
    pushd "%FRONTEND_DIR%"
    call npm ci
    if errorlevel 1 (popd & exit /b 1)
    popd
)

start "KernelSense Backend (Python ML)" cmd /k "cd /d ""%BACKEND_DIR%"" && ""%VENV_PYTHON%"" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
start "KernelSense Frontend (Vite)" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev -- --host 127.0.0.1"

echo.
echo Both Frontend (http://localhost:5173) and Backend (http://127.0.0.1:8000) are starting!
echo Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul
start http://localhost:5173
