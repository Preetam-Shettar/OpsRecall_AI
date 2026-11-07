import json
import os
from typing import Any

import httpx

from app.config import HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL
from app.database import get_connection


class HindsightMemoryClient:
    def __init__(self):
        self.base_url = HINDSIGHT_BASE_URL
        self.api_key = HINDSIGHT_API_KEY
        self.bank_id = "opsrecall-incidents"

    def _store_local_memory(self, content: str, context: str | None) -> dict[str, Any]:
        with get_connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT NOT NULL, context TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)"
            )
            conn.execute(
                "INSERT INTO memories (content, context) VALUES (?, ?)",
                (content, context or "opsrecall-agent"),
            )
        return {"status": "stored_locally", "content": content, "context": context}

    def retain(self, content: str, context: str | None = None) -> dict[str, Any]:
        payload = {"bank_id": self.bank_id, "content": content, "context": context or "opsrecall-agent"}
        if self.base_url and self.api_key:
            try:
                response = httpx.post(
                    f"{self.base_url.rstrip('/')}/retain",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=10,
                )
                if response.status_code in (200, 201):
                    return response.json()
            except Exception:
                pass
        return self._store_local_memory(content, context)

    def recall(self, query: str, budget: str = "mid") -> list[dict[str, Any]]:
        if self.base_url and self.api_key:
            try:
                response = httpx.post(
                    f"{self.base_url.rstrip('/')}/recall",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"bank_id": self.bank_id, "query": query, "budget": budget},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and isinstance(data.get("results"), list):
                        return data["results"]
            except Exception:
                pass

        with get_connection() as conn:
            rows = conn.execute(
                "SELECT content, context, created_at FROM memories WHERE content LIKE ? OR context LIKE ? ORDER BY created_at DESC LIMIT 5",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        return [
            {
                "incident_id": f"INC-{index + 1:03d}",
                "content": row["content"],
                "context": row["context"],
                "created_at": row["created_at"],
            }
            for index, row in enumerate(rows)
        ]

    def reflect(self, query: str, budget: str = "mid") -> str:
        if self.base_url and self.api_key:
            try:
                response = httpx.post(
                    f"{self.base_url.rstrip('/')}/reflect",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"bank_id": self.bank_id, "query": query, "budget": budget},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        return data.get("text") or data.get("summary") or "No summary available."
            except Exception:
                pass

        memories = self.recall(query, budget)
        if not memories:
            return "No prior incident lessons are available yet."
        joined = "; ".join(item.get("content", "") for item in memories[:3])
        return f"Past lessons suggest: {joined}"


memory_client = HindsightMemoryClient()
