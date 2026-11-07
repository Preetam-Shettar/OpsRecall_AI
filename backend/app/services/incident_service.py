import json
import uuid
from datetime import datetime, timezone
from typing import Any

from app.database import get_connection
from app.services.analysis_service import AnalysisService
from app.services.hindsight_service import memory_client
from app.services.log_parser import sanitize_logs


class IncidentService:
    def __init__(self):
        self.analysis_service = AnalysisService()

    def _generate_incident_id(self) -> str:
        now = datetime.now(timezone.utc)
        unique_suffix = uuid.uuid4().hex[:4].upper()
        return f"INC-{now.strftime('%Y%m%d-%H%M%S')}-{unique_suffix}"

    def _row_to_dict(self, row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "title": row["title"],
            "service": row["service"],
            "environment": row["environment"],
            "description": row["description"],
            "logs": row["logs"],
            "sanitized_logs": row["sanitized_logs"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "analysis": json.loads(row["analysis_json"]) if row["analysis_json"] else None,
            "feedback": json.loads(row["feedback_json"]) if row["feedback_json"] else None,
            "resolution": json.loads(row["resolution_json"]) if row["resolution_json"] else None,
            "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else None,
        }

    def create_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        incident_id = self._generate_incident_id()
        raw_logs = payload.get("logs", "")
        sanitized = sanitize_logs(raw_logs)

        incident_record = {
            "id": incident_id,
            "title": payload["title"],
            "service": payload["service"],
            "environment": payload.get("environment", "staging"),
            "description": payload["description"],
            "logs": raw_logs,
            "sanitized_logs": sanitized,
            "status": "analyzed",
            "created_at": now,
            "updated_at": now,
            "deployment_context": payload.get("deployment_context"),
        }

        # Step 1: Recall relevant previous incidents from Hindsight memory
        memory_query = (
            f"{incident_record['service']} {incident_record['environment']} "
            f"{incident_record['description']} {sanitized}"
        )
        recalled_memories = memory_client.recall(memory_query, budget="mid", limit=4)

        # Step 2: Analyze current evidence with LLM + recalled memory
        analysis = self.analysis_service.analyze_incident(incident_record, recalled_memories)

        # Step 3: Store incident in application database
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO incidents (
                    id, title, service, environment, description, logs, sanitized_logs,
                    status, created_at, updated_at, analysis_json, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    incident_id,
                    incident_record["title"],
                    incident_record["service"],
                    incident_record["environment"],
                    incident_record["description"],
                    raw_logs,
                    sanitized,
                    incident_record["status"],
                    now,
                    now,
                    json.dumps(analysis),
                    json.dumps({
                        "deployment_context": payload.get("deployment_context"),
                        "incident_timestamp": payload.get("incident_timestamp"),
                    }),
                ),
            )

        incident_record["analysis"] = analysis
        incident_record["related_memories"] = analysis.get("related_memory_insights", [])
        incident_record["recommendations"] = analysis.get("recommended_checks", [])
        return incident_record

    def get_incident(self, incident_id: str) -> dict[str, Any] | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def list_incidents(self, search: str | None = None, service: str | None = None, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT * FROM incidents WHERE 1=1"
        params = []
        if search:
            query += " AND (title LIKE ? OR description LIKE ? OR service LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term, term])
        if service:
            query += " AND service = ?"
            params.append(service)
        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(row) for row in rows]

    def save_feedback(self, incident_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if not row:
                raise ValueError("Incident not found")
            feedback = payload if isinstance(payload, dict) else {"helpful": bool(payload)}
            conn.execute(
                "UPDATE incidents SET feedback_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(feedback), datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), incident_id),
            )
        return {"status": "saved", "feedback": feedback}

    def save_resolution(self, incident_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if not row:
                raise ValueError("Incident not found")

            outcome = payload.get("outcome", "resolved")
            resolution = {
                "root_cause": payload["root_cause"],
                "resolution": payload["resolution"],
                "outcome": outcome,
                "verified": payload.get("verified", True),
                "engineer": payload.get("engineer", "On-call Engineer"),
                "resolved_at": now_iso,
            }
            conn.execute(
                "UPDATE incidents SET resolution_json = ?, status = ?, updated_at = ? WHERE id = ?",
                (json.dumps(resolution), outcome, now_iso, incident_id),
            )

        # Formulate structured memory representation per Section 7.5
        memory_text = (
            f"Incident ID: {incident_id}\n"
            f"Service: {row['service']}\n"
            f"Environment: {row['environment']}\n"
            f"Symptoms: {row['description']}\n"
            f"Confirmed root cause: {payload['root_cause']}\n"
            f"Verified resolution: {payload['resolution']}\n"
            f"Outcome: {outcome}\n"
            f"Verification: confirmed by engineer {payload.get('engineer') or 'on-call'}\n"
            f"Timestamp: {now_iso}"
        )

        retain_result = memory_client.retain(
            content=memory_text,
            context=f"OpsRecall resolution {incident_id}",
            incident_id=incident_id,
            service=row["service"],
            outcome=outcome,
        )

        return {
            "status": outcome,
            "resolution": resolution,
            "memory_retained": True,
            "memory_details": retain_result,
        }

    def dashboard_summary(self) -> dict[str, Any]:
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS count FROM incidents").fetchone()["count"]
            resolved = conn.execute("SELECT COUNT(*) AS count FROM incidents WHERE status = 'resolved'").fetchone()["count"]
            open_count = conn.execute("SELECT COUNT(*) AS count FROM incidents WHERE status != 'resolved'").fetchone()["count"]
            memories_count = conn.execute("SELECT COUNT(*) AS count FROM memories").fetchone()["count"]
            by_status = {
                row["status"]: row["count"]
                for row in conn.execute(
                    "SELECT status, COUNT(*) AS count FROM incidents GROUP BY status"
                ).fetchall()
            }
            recent = [
                self._row_to_dict(row)
                for row in conn.execute("SELECT * FROM incidents ORDER BY created_at DESC LIMIT 5").fetchall()
            ]
            latest = recent[0] if recent else None

        return {
            "total_incidents": total,
            "resolved_incidents": resolved,
            "open_incidents": open_count,
            "stored_memories": memories_count,
            "by_status": by_status,
            "latest_incident": {"id": latest["id"], "title": latest["title"]} if latest else None,
            "recent_incidents": recent,
        }


incident_service = IncidentService()
