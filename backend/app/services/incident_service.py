import json
from datetime import datetime, timezone

from app.database import get_connection
from app.services.analysis_service import AnalysisService
from app.services.hindsight_service import memory_client
from app.services.log_parser import sanitize_logs


class IncidentService:
    def __init__(self):
        self.analysis_service = AnalysisService()

    def _generate_incident_id(self) -> str:
        now = datetime.now(timezone.utc)
        return f"INC-{now.strftime('%Y%m%d%H%M%S')}"

    def _row_to_dict(self, row):
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

    def create_incident(self, payload: dict) -> dict:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        incident_id = self._generate_incident_id()
        sanitized_logs = sanitize_logs(payload.get("logs", ""))
        incident = {
            "id": incident_id,
            "title": payload["title"],
            "service": payload["service"],
            "environment": payload.get("environment", "staging"),
            "description": payload["description"],
            "logs": payload.get("logs", ""),
            "sanitized_logs": sanitized_logs,
            "status": "analyzed",
            "created_at": now,
            "updated_at": now,
        }

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
                    incident["title"],
                    incident["service"],
                    incident["environment"],
                    incident["description"],
                    incident["logs"],
                    sanitized_logs,
                    incident["status"],
                    now,
                    now,
                    None,
                    json.dumps({
                        "deployment_context": payload.get("deployment_context"),
                        "incident_timestamp": payload.get("incident_timestamp"),
                    }),
                ),
            )

        recall_results = memory_client.recall(
            f"{incident['service']} {incident['environment']} {incident['description']} {sanitized_logs}"
        )
        analysis = self.analysis_service.analyze_incident(incident, recall_results)
        with get_connection() as conn:
            conn.execute(
                "UPDATE incidents SET analysis_json = ?, updated_at = ? WHERE id = ?",
                (json.dumps(analysis), now, incident_id),
            )

        incident["analysis"] = analysis
        incident["related_memories"] = analysis.get("related_memory_insights", [])
        incident["recommendations"] = analysis.get("recommended_checks", [])
        return incident

    def get_incident(self, incident_id: str) -> dict | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if not row:
                return None
            return self._row_to_dict(row)

    def list_incidents(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM incidents ORDER BY created_at DESC").fetchall()
            return [self._row_to_dict(row) for row in rows]

    def save_feedback(self, incident_id: str, payload: dict) -> dict:
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

    def save_resolution(self, incident_id: str, payload: dict) -> dict:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
            if not row:
                raise ValueError("Incident not found")
            resolution = {
                "root_cause": payload["root_cause"],
                "resolution": payload["resolution"],
                "verified": payload.get("verified", True),
                "engineer": payload.get("engineer"),
            }
            conn.execute(
                "UPDATE incidents SET resolution_json = ?, status = 'resolved', updated_at = ? WHERE id = ?",
                (json.dumps(resolution), datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), incident_id),
            )

        memory_text = (
            f"Incident ID: {incident_id}\n"
            f"Service: {row['service']}\n"
            f"Environment: {row['environment']}\n"
            f"Symptoms: {row['description']}\n"
            f"Confirmed root cause: {payload['root_cause']}\n"
            f"Verified resolution: {payload['resolution']}\n"
            f"Outcome: resolved\n"
            f"Verification: confirmed by engineer"
        )
        memory_client.retain(memory_text, context=f"OpsRecall resolution {incident_id}")
        return {"status": "resolved", "resolution": resolution}

    def dashboard_summary(self) -> dict:
        with get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) AS count FROM incidents").fetchone()["count"]
            resolved = conn.execute("SELECT COUNT(*) AS count FROM incidents WHERE status = 'resolved'").fetchone()["count"]
            by_status = {
                row["status"]: row["count"]
                for row in conn.execute(
                    "SELECT status, COUNT(*) AS count FROM incidents GROUP BY status"
                ).fetchall()
            }
            latest = conn.execute("SELECT id, title FROM incidents ORDER BY created_at DESC LIMIT 1").fetchone()
        return {
            "total_incidents": total,
            "resolved_incidents": resolved,
            "by_status": by_status,
            "latest_incident": {"id": latest["id"], "title": latest["title"]} if latest else None,
        }


incident_service = IncidentService()
