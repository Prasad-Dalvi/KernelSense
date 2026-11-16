# KernelSense
Local system-monitoring dashboard and AI-assisted troubleshooting application, with Windows host telemetry and optional WSL integrations.

## Run on Windows

The runnable full-stack app is in [`2.0`](./2.0/). Install Python 3.12+ and Node.js, then start it with:

```bat
cd 2.0
start_all.bat
```

The frontend reads live values from the backend; mock telemetry is not enabled. Windows host identity, process and storage details, and System/Application event records are collected from the running PC. The Assistant page records voice prompts in the browser and transcribes them locally with Whisper small via faster-whisper. The model downloads on first use; audio stays in memory and is not sent to an AI provider.

The launcher creates `2.0\backend\.venv`, installs the backend dependencies, and starts the API and frontend. If frontend dependencies are missing, it installs them with `npm ci`.

On the Assistant page, select **Gemini** or **Grok (xAI)** and enter the matching API key in the password field, or configure `GEMINI_API_KEY` / `GROK_API_KEY` in `2.0\backend\.env` (copy `2.0\backend\.env.example` first). Keys entered in the page remain only in browser memory and are sent to the local backend for requests; they are not saved to browser storage. The backend tries the selected provider first, then configured fallback providers, and uses the local planner if those are unavailable.

Project documentation, datasets, model files, and source files are retained; only generated caches/build output are treated as disposable.

See [PROJECT_GUIDE.md](./PROJECT_GUIDE.md) for architecture, APIs, ML details, limitations, and research-paper guidance.
