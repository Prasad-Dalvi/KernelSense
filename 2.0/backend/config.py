"""
Configuration settings for KernelSense Backend
Loads .env first so all environment variables are available before any module reads them.
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Load .env from backend/ directory (same dir as this file)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"), override=True)

class Settings(BaseModel):
    app_name: str = "KernelSense Linux Operations & AI Diagnostics Backend"
    version: str = "1.0.0"
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: list = ["*"]
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

settings = Settings()
