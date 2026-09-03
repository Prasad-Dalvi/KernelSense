"""
Dynamic Zero-Shot Intent Classification & Entity Extraction Engine for KernelSense
Powered by Google Gemini API via UniversalLLMProvider (No hardcoded keyword tables).

Dynamically resolves:
- Conversational Greetings ("hi", "who are you", "what can you do")
- Core Linux & OS Commands ("find ip address", "what is username", "lscpu", "show open ports")
- Natural Language File Discovery ("find resume.pdf", "open USS1.pdf")
- Dynamic Web URL & Browser Launching (resolves ANY website without static lists)
- Desktop Application Launching (notepad, calculator, terminal, paint, etc.)
- Deep Hardware Diagnostics & Sluggishness Root-Cause Analysis
- General Knowledge & Code Generation
"""

import os
import re
import logging
from typing import Dict, Any, Optional
from ai.llm_provider import llm_gateway

logger = logging.getLogger("kernelsense.intent")


def resolve_target_url(text: str, browser: str = "chrome") -> str:
    """
    Dynamically resolves any website name to a valid HTTPS URL using Gemini LLM.
    Zero hardcoded URL directories.
    """
    clean = text.strip()
    if clean.startswith("http://") or clean.startswith("https://"):
        return clean
    if "." in clean and " " not in clean:
        return f"https://{clean}"
    
    # Use Gemini reasoning to resolve the website URL dynamically
    try:
        res = llm_gateway.reason_and_plan(f"open website {clean}")
        if res and res.get("target_url"):
            return res["target_url"]
    except Exception as e:
        logger.warning(f"Dynamic URL resolution fallback: {e}")
    
    return f"https://www.{clean.lower().replace(' ', '')}.com"


def classify_intent(query: str, telemetry_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Zero-shot intent classification and entity extraction powered by Google Gemini API.
    Replaces static keyword tables with real AI reasoning.
    """
    q_clean = query.strip()
    if not q_clean:
        return {
            "intent": "GENERAL_QUERY",
            "primary_intent": "GENERAL_QUERY",
            "confidence": 0.5
        }

    # Query the Gemini AI gateway
    try:
        ai_result = llm_gateway.reason_and_plan(q_clean, telemetry_context)
    except Exception as e:
        logger.warning(f"Gemini intent classification error: {e}")
        ai_result = None

    if ai_result:
        intent = ai_result.get("intent", "GENERAL_QUERY")
        action_type = ai_result.get("action_type", "NONE")

        result = {
            "intent": intent,
            "primary_intent": intent,
            "action_type": action_type,
            "confidence": 0.99,
            "provider": ai_result.get("provider", "gemini"),
            "thought_process": ai_result.get("thought_process", ""),
            "response_markdown": ai_result.get("response_markdown", ""),
            "recommendations": ai_result.get("recommendations", [])
        }

        # Map entity extractions
        if intent == "FILE_SEARCH" or ai_result.get("search_target"):
            result["search_target"] = ai_result.get("search_target") or q_clean

        if intent == "LINUX_CORE_COMMAND" or ai_result.get("linux_command"):
            result["command"] = ai_result.get("linux_command", "")
            result["task_type"] = ai_result.get("linux_task_type", "RAW_COMMAND")
            result["title"] = ai_result.get("linux_title", "🐧 Linux Command Execution")
            result["explanation"] = ai_result.get("linux_explanation", "Executes command in Ubuntu Linux.")

        if intent == "OPEN_URL_IN_APP" or action_type == "OPEN_URL":
            result["url"] = ai_result.get("target_url")
            result["browser"] = ai_result.get("browser", "chrome")

        if intent == "OPEN_APPLICATION" or action_type == "OPEN_APP":
            result["target_app"] = ai_result.get("target_app")

        return result

    # ── Minimal Offline Fallback (Only if Gemini and all fallbacks are unreachable) ──
    q_lower = q_clean.lower()
    if any(q_lower.startswith(g) for g in ["hi", "hello", "hey"]):
        return {"intent": "GREETING", "primary_intent": "GREETING", "confidence": 0.9}
    
    file_match = re.search(r'([a-zA-Z0-9_\-\s]+\.(?:pdf|docx|pptx|xlsx|txt|csv|py|md))\b', q_clean, re.I)
    if file_match:
        return {"intent": "FILE_SEARCH", "primary_intent": "FILE_SEARCH", "search_target": file_match.group(1).strip(), "confidence": 0.9}

    return {
        "intent": "GENERAL_QUERY",
        "primary_intent": "GENERAL_QUERY",
        "confidence": 0.7
    }
