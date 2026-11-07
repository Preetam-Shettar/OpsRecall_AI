import logging
import os
import re
from typing import Any

import httpx

from app.config import HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL, HINDSIGHT_BANK_ID
from app.database import get_connection

logger = logging.getLogger(__name__)


class HindsightMemoryClient:
    def __init__(self):
        self.base_url = HINDSIGHT_BASE_URL
        self.api_key = HINDSIGHT_API_KEY
        self.bank_id = HINDSIGHT_BANK_ID or "opsrecall-incidents"

    def _store_local_memory(
        self,
        content: str,
        context: str | None = None,
        incident_id: str | None = None,
        service: str | None = None,
        outcome: str = "resolved",
    ) -> dict[str, Any]:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO memories (bank_id, incident_id, service, content, context, outcome, verified)
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (self.bank_id, incident_id, service, content, context or f"OpsRecall incident {incident_id or 'unknown'}", outcome),
            )
        return {
            "status": "stored_locally",
            "bank_id": self.bank_id,
            "incident_id": incident_id,
            "content": content,
            "context": context,
            "source": "local_memory_bank",
        }

    def retain(
        self,
        content: str,
        context: str | None = None,
        incident_id: str | None = None,
        service: str | None = None,
        outcome: str = "resolved",
    ) -> dict[str, Any]:
        """
        Retains verified incident outcome and diagnostic knowledge into Hindsight.
        """
        payload = {
            "bank_id": self.bank_id,
            "content": content,
            "context": context or f"OpsRecall incident {incident_id or 'unknown'}",
        }

        # Also ensure local database backup is always recorded
        local_result = self._store_local_memory(
            content=content,
            context=context,
            incident_id=incident_id,
            service=service,
            outcome=outcome,
        )

        if self.base_url and self.api_key:
            try:
                response = httpx.post(
                    f"{self.base_url.rstrip('/')}/retain",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=10,
                )
                if response.status_code in (200, 201):
                    res_json = response.json()
                    res_json["source"] = "hindsight_api"
                    return res_json
                else:
                    logger.warning(
                        "Hindsight API retain returned status %s: %s",
                        response.status_code,
                        response.text,
                    )
            except Exception as exc:
                logger.warning("Hindsight API retain connection error: %s", exc)

        return local_result

    def recall(self, query: str, budget: str = "mid", limit: int = 5) -> list[dict[str, Any]]:
        """
        Recalls historical incidents and verified resolutions relevant to the query.
        """
        if self.base_url and self.api_key:
            try:
                response = httpx.post(
                    f"{self.base_url.rstrip('/')}/recall",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"bank_id": self.bank_id, "query": query, "budget": budget},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and isinstance(data.get("results"), list):
                        results = []
                        for item in data["results"]:
                            item["source"] = "hindsight_api"
                            results.append(item)
                        if results:
                            return results
            except Exception as exc:
                logger.warning("Hindsight API recall error: %s", exc)

        # Fallback to local memory retrieval with keyword scoring
        query_terms = [t for t in re.findall(r"[a-zA-Z0-9_\-]+", query.lower()) if len(t) > 2]
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id, incident_id, service, content, context, outcome, created_at FROM memories ORDER BY created_at DESC"
            ).fetchall()

        if not rows:
            return []

        scored = []
        for row in rows:
            text = f"{row['content']} {row['context'] or ''} {row['service'] or ''}".lower()
            score = sum(1 for term in query_terms if term in text)
            scored.append((score, row))

        # Sort by relevance score, then recent
        scored.sort(key=lambda x: x[0], reverse=True)

        matched_results = []
        for index, (score, row) in enumerate(scored[:limit]):
            inc_id = row["incident_id"] or f"INC-M{row['id']:03d}"
            matched_results.append({
                "incident_id": inc_id,
                "service": row["service"],
                "content": row["content"],
                "context": row["context"],
                "outcome": row["outcome"],
                "created_at": row["created_at"],
                "score": score,
                "source": "local_memory_bank",
            })

        return matched_results

    def reflect(self, query: str, budget: str = "mid") -> str:
        """
        Reflects across accumulated incident memories to synthesize high-level patterns.
        """
        if self.base_url and self.api_key:
            try:
                response = httpx.post(
                    f"{self.base_url.rstrip('/')}/reflect",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={"bank_id": self.bank_id, "query": query, "budget": budget},
                    timeout=10,
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        text = data.get("text") or data.get("summary")
                        if text:
                            return text
            except Exception as exc:
                logger.warning("Hindsight API reflect error: %s", exc)

        memories = self.recall(query, budget=budget, limit=5)
        if not memories:
            return "No prior incident memories have been stored in the bank yet."

        summaries = []
        for mem in memories[:3]:
            inc = mem.get("incident_id", "Prior incident")
            content = mem.get("content", "").replace("\n", " ")
            summaries.append(f"[{inc}] {content[:180]}")

        joined = " | ".join(summaries)
        return f"[Local Memory Fallback] Cross-incident synthesis across {len(memories)} matching records: {joined}"


memory_client = HindsightMemoryClient()
