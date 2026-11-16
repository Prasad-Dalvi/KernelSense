"""
FastAPI Server Entry Point for KernelSense
Exposes all REST API endpoints for Live System Telemetry, Process Management,
NLP Log Classification, SQLite History, and ReAct AI Assistant Operations.
"""

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool
from typing import Any, Dict, List, Literal, Optional

from config import settings
from core.live_telemetry import telemetry_collector
from core.process_engine import process_engine
from core.log_engine import log_engine
from core.voice_engine import voice_engine
from core.command_safety import command_safety_engine
from core.database import db_engine
from core.ai_agent import ai_agent
from core.ml_inference import ml_engine

# Initialize FastAPI App
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Real-time host monitoring and AI-assisted system diagnostics backend"
)

# Enable CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------
# Request / Response Schemas
# -------------------------------------------------------------
class AskRequest(BaseModel):
    query: str
    provider: Literal["gemini", "grok"] = "gemini"
    api_key: Optional[str] = Field(default=None, max_length=512, repr=False)

class CommandApprovalRequest(BaseModel):
    command_id: str
    request_id: Optional[str] = None
    command: Optional[str] = None

class CommandRejectRequest(BaseModel):
    command_id: str
    request_id: Optional[str] = None

MAX_VOICE_AUDIO_BYTES = 2_000_000

# -------------------------------------------------------------
# Root & Health Endpoints
# -------------------------------------------------------------
@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "KernelSense ML/AI Telemetry Backend",
        "version": settings.version,
        "models_loaded": {
            "telemetry_anomaly_detector": ml_engine.telemetry_bundle is not None,
            "nlp_log_classifier": ml_engine.log_bundle is not None
        }
    }

# -------------------------------------------------------------
# AI Assistant & Operations Endpoints (Member 1)
# -------------------------------------------------------------
@app.post("/ask")
def handle_ask(req: AskRequest):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    return ai_agent.ask(req.query, provider=req.provider, api_key=req.api_key)

@app.post("/voice/transcribe")
async def transcribe_voice(request: Request):
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "audio/wav":
        raise HTTPException(status_code=415, detail="Send a WAV audio recording.")

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_VOICE_AUDIO_BYTES:
                raise HTTPException(status_code=413, detail="Recording must be 60 seconds or shorter.")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid content length.") from exc

    chunks = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_VOICE_AUDIO_BYTES:
            raise HTTPException(status_code=413, detail="Recording must be 60 seconds or shorter.")
        chunks.append(chunk)

    try:
        transcript = await run_in_threadpool(voice_engine.transcribe, b"".join(chunks))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return {"text": transcript}

@app.post("/commands/approve")
def handle_approve_command(req: CommandApprovalRequest):
    # Lookup command or run directly if passed
    cmd_to_run = req.command
    if not cmd_to_run:
        # Search history for command_id
        history = db_engine.get_history(limit=20)
        for h in history:
            for c in h.get("commands", []):
                if c.get("id") == req.command_id:
                    cmd_to_run = c.get("command")
                    break
            if cmd_to_run:
                break
                
    if not cmd_to_run:
        return {
            "success": True,
            "output": f"Command '{req.command_id}' approved and marked as completed.",
            "status": "success"
        }
        
    res = command_safety_engine.execute_command(cmd_to_run)
    return res

@app.post("/commands/reject")
def handle_reject_command(req: CommandRejectRequest):
    return {
        "success": True,
        "message": f"Command {req.command_id} rejected by operator.",
        "status": "rejected"
    }

# -------------------------------------------------------------
# System Telemetry Endpoints (Member 2)
# -------------------------------------------------------------
@app.get("/system/stats")
@app.get("/system/all")
def get_system_stats():
    return telemetry_collector.get_all_stats()

@app.get("/system/info")
def get_system_info():
    return telemetry_collector.get_host_info()

@app.get("/system/cpu")
def get_cpu():
    return telemetry_collector.get_cpu_stats()

@app.get("/system/memory")
def get_memory():
    return telemetry_collector.get_memory_stats()

@app.get("/system/storage")
def get_storage():
    return telemetry_collector.get_storage_stats()

@app.get("/system/network")
def get_network():
    return telemetry_collector.get_network_stats()

@app.get("/system/health")
def get_health():
    return telemetry_collector.get_system_health()

@app.get("/system/events")
def get_events(limit: int = Query(default=10, ge=1, le=50)):
    return log_engine.get_logs(limit=limit)

# -------------------------------------------------------------
# Process Management Endpoints
# -------------------------------------------------------------
@app.get("/processes")
def get_processes(limit: int = Query(default=100, ge=1, le=500)):
    procs = process_engine.list_processes(limit=limit)
    return {"processes": procs}

@app.post("/processes/{pid}/kill")
def kill_process(pid: int):
    res = process_engine.kill_process(pid)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Failed to kill process."))
    return res

# -------------------------------------------------------------
# System Logs & Audit History
# -------------------------------------------------------------
@app.get("/logs")
def get_logs(
    severity: Optional[str] = None,
    service: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=150, ge=1, le=500)
):
    logs = log_engine.get_logs(severity=severity, service=service, search=search, limit=limit)
    return {"logs": logs}

@app.get("/history")
def get_history(limit: int = Query(default=50, ge=1, le=200)):
    items = db_engine.get_history(limit=limit)
    return {"items": items}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
