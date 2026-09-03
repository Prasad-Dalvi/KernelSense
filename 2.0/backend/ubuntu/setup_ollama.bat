@echo off
title KernelSense - Ubuntu WSL Ollama & Llama Setup
echo ========================================================
echo   KernelSense: Setting up Ollama & Llama in Ubuntu WSL2
echo ========================================================
echo.
echo [1/3] Installing Ollama inside Ubuntu WSL...
wsl.exe -d Ubuntu bash -c "curl -fsSL https://ollama.com/install.sh | sh"

echo.
echo [2/3] Starting Ollama Background Daemon inside Ubuntu...
wsl.exe -d Ubuntu bash -c "nohup ollama serve > /tmp/ollama.log 2>&1 &"

echo.
echo [3/3] Pulling lightweight Llama model (llama3.2:1b)...
wsl.exe -d Ubuntu bash -c "ollama pull llama3.2:1b"

echo.
echo ========================================================
echo   Setup Complete! Local Ollama Llama is ready in WSL.
echo ========================================================
pause
