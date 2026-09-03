"""
SQLite Audit & History Persistence Engine for KernelSense
Stores user queries, AI diagnostic reasoning outputs, and command approval lifecycles.
"""

import os
import sqlite3
import json
import uuid
import datetime
from typing import List, Dict, Any, Optional

class DatabaseEngine:
    def __init__(self):
        self.backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.db_dir = os.path.join(self.backend_dir, 'data')
        os.makedirs(self.db_dir, exist_ok=True)
        self.db_path = os.path.join(self.db_dir, 'kernelsense.db')
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id TEXT PRIMARY KEY,
                    query TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    commands_json TEXT,
                    result TEXT,
                    risk_level TEXT,
                    status TEXT,
                    root_cause_json TEXT
                )
            """)
            conn.commit()

    def add_history_entry(
        self,
        request_id: str,
        query: str,
        intent: str,
        commands: List[Dict[str, Any]],
        result: str,
        risk_level: str = "LOW",
        root_cause: Optional[Dict[str, Any]] = None
    ):
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO history (
                    id, query, timestamp, intent, commands_json, result, risk_level, status, root_cause_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id,
                query,
                now_str,
                intent,
                json.dumps(commands),
                result,
                risk_level,
                "success",
                json.dumps(root_cause) if root_cause else None
            ))
            conn.commit()

    def save_history(
        self,
        query: str,
        response_text: str,
        tools_used: List[str],
        root_cause_nodes: List[Dict[str, Any]],
        root_cause_edges: List[Dict[str, Any]],
        proposed_commands: List[Any],
        anomaly_score: float = 0.0,
        intent: str = "SYSTEM_DIAGNOSIS"
    ):
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        cmds = []
        for i, c in enumerate(proposed_commands):
            if isinstance(c, dict):
                cmds.append(c)
            else:
                cmds.append({"id": f"cmd-{i}", "command": str(c), "explanation": "System command"})

        self.add_history_entry(
            request_id=req_id,
            query=query,
            intent=intent,
            commands=cmds,
            result=response_text[:300],
            risk_level="LOW",
            root_cause={"nodes": root_cause_nodes, "edges": root_cause_edges}
        )

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            
            items = []
            for r in rows:
                items.append({
                    "id": r["id"],
                    "query": r["query"],
                    "timestamp": r["timestamp"],
                    "intent": r["intent"],
                    "commands": json.loads(r["commands_json"]) if r["commands_json"] else [],
                    "result": r["result"],
                    "risk_level": r["risk_level"],
                    "status": r["status"]
                })
            return items

db_engine = DatabaseEngine()
db = db_engine
