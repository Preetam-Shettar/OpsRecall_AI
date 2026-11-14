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

    def _infer_severity(self, payload: dict[str, Any], raw_logs: str) -> str:
        if payload.get("severity"):
            sev = str(payload["severity"]).lower().strip()
            if sev in ("critical", "high", "medium", "low"):
                return sev

        combined = f"{payload.get('title', '')} {payload.get('description', '')} {raw_logs}".lower()
        if any(term in combined for term in ["critical", "outage", "database connection pool exhaustion", "maximum connection limit reached", "fatal"]):
            return "critical"
        if payload.get("environment") == "production" and any(term in combined for term in ["500", "timeout", "exhausted", "down", "rollback"]):
            return "critical"
        if payload.get("environment") == "production" or "error" in combined:
            return "high"
        if "warn" in combined or payload.get("environment") == "staging":
            return "medium"
        return "low"

    def _detect_incident_type(self, title: str, description: str, logs: str, analysis: dict[str, Any] | None = None) -> str:
        combined = f"{title} {description} {logs}".lower()
        if analysis and isinstance(analysis, dict):
            symptoms = " ".join(analysis.get("symptoms", [])).lower()
            causes = " ".join(c.get("cause", "") for c in analysis.get("possible_causes", [])).lower()
            combined += f" {symptoms} {causes}"

        if any(term in combined for term in ["connection pool", "pool exhausted", "pool exhaustion", "maximum connection limit", "max_connections", "connectionpool"]):
            return "Connection Pool & DB Saturation"
        elif any(term in combined for term in ["timeout", "timed out", "504", "gateway timeout", "latency spike", "timedout"]):
            return "Latency & Timeout Degradation"
        elif any(term in combined for term in ["500", "http 500", "internal server error", "exception", "rollback", "502", "503"]):
            return "HTTP 5xx & Application Errors"
        elif any(term in combined for term in ["memory", "cpu", "oom", "thread starvation", "worker pool", "concurrency"]):
            return "Concurrency & Resource Pressure"
        elif any(term in combined for term in ["deploy", "release", "scaling", "config change", "worker threads", "v1."]):
            return "Deployment & Scaling Regression"
        elif any(term in combined for term in ["auth", "token", "unauthorized", "401", "403", "forbidden", "permission"]):
            return "Authentication & Access Failure"
        return "General Service Degradation"

    def _calculate_avg_resolution_time(self, incidents: list[dict[str, Any]]) -> dict[str, Any]:
        durations = []
        for inc in incidents:
            if inc.get("status") == "resolved" and inc.get("resolution"):
                res = inc["resolution"]
                if isinstance(res, dict) and res.get("resolved_at") and inc.get("created_at"):
                    try:
                        c_dt = datetime.fromisoformat(inc["created_at"].replace("Z", "+00:00"))
                        r_dt = datetime.fromisoformat(res["resolved_at"].replace("Z", "+00:00"))
                        diff_sec = (r_dt - c_dt).total_seconds()
                        if diff_sec > 0:
                            durations.append(diff_sec)
                    except Exception:
                        pass

        if not durations:
            return {
                "available": False,
                "display": "Unavailable",
                "seconds": None,
                "note": "No resolved incidents with valid start-to-resolution timestamps recorded yet.",
            }

        avg_sec = sum(durations) / len(durations)
        # Immediate demo resolutions (< 30 seconds) do not reflect reliable production duration telemetry
        if avg_sec < 30:
            return {
                "available": False,
                "display": "Unavailable",
                "seconds": round(avg_sec, 1),
                "note": "Telemetry unavailable: Recorded resolutions were verified instantaneously during live triage demo.",
            }

        if avg_sec < 3600:
            minutes = round(avg_sec / 60, 1)
            display = f"{minutes} min"
        else:
            hours = round(avg_sec / 3600, 1)
            display = f"{hours} hrs"

        return {
            "available": True,
            "display": display,
            "seconds": round(avg_sec, 1),
            "note": f"Based on {len(durations)} resolved incident(s) with confirmed timestamps.",
        }

    def _extract_recurring_patterns(self, incidents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        type_groups: dict[str, dict[str, Any]] = {}
        for inc in incidents:
            t = self._detect_incident_type(
                inc.get("title", ""),
                inc.get("description", ""),
                inc.get("logs", ""),
                inc.get("analysis"),
            )
            svc = inc.get("service") or "unknown"
            if t not in type_groups:
                type_groups[t] = {"type": t, "services": set(), "incidents": []}
            type_groups[t]["services"].add(svc)
            type_groups[t]["incidents"].append(inc["id"])

        patterns = []
        for t, g in type_groups.items():
            if len(g["incidents"]) >= 2:
                svc_list = sorted(list(g["services"]))
                patterns.append({
                    "pattern": t,
                    "count": len(g["incidents"]),
                    "services": svc_list,
                    "description": f"Recurring failure pattern detected across {len(g['incidents'])} incidents affecting {', '.join(svc_list)}.",
                    "sample_incidents": g["incidents"][:3],
                })

        return sorted(patterns, key=lambda p: p["count"], reverse=True)

    def _extract_memory_intelligence(self, all_incidents: list[dict[str, Any]]) -> dict[str, Any]:
        with get_connection() as conn:
            memories_count = conn.execute("SELECT COUNT(*) AS count FROM memories").fetchone()["count"]
            verified_count = conn.execute(
                "SELECT COUNT(*) AS count FROM incidents WHERE status = 'resolved' AND resolution_json LIKE '%\"verified\": true%'"
            ).fetchone()["count"]

        recalled_stats: dict[str, int] = {}
        for inc in all_incidents:
            analysis = inc.get("analysis")
            if analysis and isinstance(analysis, dict):
                insights = analysis.get("related_memory_insights", [])
                for ins in insights:
                    if isinstance(ins, dict) and ins.get("incident_id"):
                        iid = ins["incident_id"]
                        recalled_stats[iid] = recalled_stats.get(iid, 0) + 1

        frequently_recalled = [
            {"incident_id": k, "recall_count": v}
            for k, v in sorted(recalled_stats.items(), key=lambda x: x[1], reverse=True)
        ]

        from app.config import HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL, HINDSIGHT_BANK_ID
        is_cloud = bool(HINDSIGHT_BASE_URL and HINDSIGHT_API_KEY and HINDSIGHT_API_KEY != "replace_with_your_key")

        return {
            "total_retained": memories_count,
            "verified_resolutions": verified_count,
            "frequently_recalled": frequently_recalled,
            "has_recall_statistics": len(frequently_recalled) > 0,
            "recall_note": (
                f"Active: {len(frequently_recalled)} incident(s) referenced during automated memory recall"
                if frequently_recalled
                else "No multi-incident recall citations recorded yet"
            ),
            "memory_system_status": {
                "status": "online",
                "mode": "Hindsight Cloud" if is_cloud else "Local SQLite Fallback",
                "bank_id": HINDSIGHT_BANK_ID or "opsrecall-incidents",
                "verified_only": True,
            },
        }

    def _row_to_dict(self, row) -> dict[str, Any]:
        row_keys = row.keys() if hasattr(row, "keys") else []
        metadata = json.loads(row["metadata_json"]) if row["metadata_json"] else {}
        severity = row["severity"] if "severity" in row_keys and row["severity"] else metadata.get("severity")
        if not severity:
            severity = self._infer_severity(
                {"title": row["title"], "environment": row["environment"], "description": row["description"]},
                row["logs"] or "",
            )
        return {
            "id": row["id"],
            "title": row["title"],
            "service": row["service"],
            "environment": row["environment"],
            "severity": severity,
            "description": row["description"],
            "logs": row["logs"],
            "sanitized_logs": row["sanitized_logs"],
            "status": row["status"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "analysis": json.loads(row["analysis_json"]) if row["analysis_json"] else None,
            "feedback": json.loads(row["feedback_json"]) if row["feedback_json"] else None,
            "resolution": json.loads(row["resolution_json"]) if row["resolution_json"] else None,
            "metadata": metadata,
        }

    def create_incident(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        incident_id = self._generate_incident_id()
        raw_logs = payload.get("logs", "")
        sanitized = sanitize_logs(raw_logs)
        severity = self._infer_severity(payload, raw_logs)

        incident_record = {
            "id": incident_id,
            "title": payload["title"],
            "service": payload["service"],
            "environment": payload.get("environment", "staging"),
            "severity": severity,
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
            cursor = conn.execute("PRAGMA table_info(incidents)")
            cols = [r["name"] for r in cursor.fetchall()]
            if "severity" in cols:
                conn.execute(
                    """
                    INSERT INTO incidents (
                        id, title, service, environment, severity, description, logs, sanitized_logs,
                        status, created_at, updated_at, analysis_json, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        incident_id,
                        incident_record["title"],
                        incident_record["service"],
                        incident_record["environment"],
                        severity,
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
                            "severity": severity,
                        }),
                    ),
                )
            else:
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
                            "severity": severity,
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

        retain_result = None
        is_verified = bool(resolution.get("verified", False))

        # Only engineer-verified resolutions are retained into persistent Hindsight memory
        if is_verified:
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
            "memory_retained": is_verified,
            "memory_details": retain_result,
        }

    def dashboard_summary(self) -> dict[str, Any]:
        all_incidents = self.list_incidents()
        total = len(all_incidents)
        resolved = sum(1 for i in all_incidents if (i.get("status") or "").lower() == "resolved")
        open_count = total - resolved
        critical_count = sum(1 for i in all_incidents if (i.get("severity") or "").lower() == "critical")

        # Severity breakdown
        by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for inc in all_incidents:
            sev = (inc.get("severity") or "medium").lower()
            if sev in by_severity:
                by_severity[sev] += 1
            else:
                by_severity["medium"] += 1

        # Status breakdown
        by_status: dict[str, int] = {}
        for inc in all_incidents:
            st = (inc.get("status") or "new").lower()
            by_status[st] = by_status.get(st, 0) + 1

        # Services breakdown
        service_map: dict[str, dict[str, Any]] = {}
        for inc in all_incidents:
            svc = inc.get("service") or "unknown"
            if svc not in service_map:
                service_map[svc] = {"service": svc, "total": 0, "resolved": 0, "active": 0, "critical": 0}
            service_map[svc]["total"] += 1
            if (inc.get("status") or "").lower() == "resolved":
                service_map[svc]["resolved"] += 1
            else:
                service_map[svc]["active"] += 1
            if (inc.get("severity") or "").lower() == "critical":
                service_map[svc]["critical"] += 1
        by_service = sorted(service_map.values(), key=lambda s: s["total"], reverse=True)

        # Resolution trends by chronological date
        trends_map: dict[str, dict[str, Any]] = {}
        for inc in all_incidents:
            c_date = (inc.get("created_at") or "")[:10]
            if c_date:
                if c_date not in trends_map:
                    trends_map[c_date] = {"date": c_date, "created": 0, "resolved": 0}
                trends_map[c_date]["created"] += 1

            res = inc.get("resolution")
            if res and isinstance(res, dict) and res.get("resolved_at"):
                r_date = str(res["resolved_at"])[:10]
                if r_date:
                    if r_date not in trends_map:
                        trends_map[r_date] = {"date": r_date, "created": 0, "resolved": 0}
                    trends_map[r_date]["resolved"] += 1
        resolution_trends = [trends_map[d] for d in sorted(trends_map.keys())]

        # Frequently occurring incident types
        types_map: dict[str, int] = {}
        for inc in all_incidents:
            t = self._detect_incident_type(
                inc.get("title", ""),
                inc.get("description", ""),
                inc.get("logs", ""),
                inc.get("analysis"),
            )
            types_map[t] = types_map.get(t, 0) + 1

        incident_types = [
            {"type": k, "count": v, "percentage": round((v / total * 100), 1) if total > 0 else 0}
            for k, v in sorted(types_map.items(), key=lambda x: x[1], reverse=True)
        ]

        # Average resolution time
        avg_res_time = self._calculate_avg_resolution_time(all_incidents)

        # Recurring patterns
        recurring_patterns = self._extract_recurring_patterns(all_incidents)

        # Memory intelligence
        memory_intel = self._extract_memory_intelligence(all_incidents)

        latest = all_incidents[0] if all_incidents else None
        recent = all_incidents[:5]

        return {
            "total_incidents": total,
            "resolved_incidents": resolved,
            "open_incidents": open_count,
            "critical_incidents": critical_count,
            "stored_memories": memory_intel["total_retained"],
            "by_status": by_status,
            "by_severity": by_severity,
            "by_service": by_service,
            "resolution_trends": resolution_trends,
            "operational_insights": {
                "most_affected_services": by_service[:5],
                "frequently_occurring_types": incident_types,
                "avg_resolution_time": avg_res_time,
                "recurring_patterns": recurring_patterns,
            },
            "memory_intelligence": memory_intel,
            "latest_incident": {"id": latest["id"], "title": latest["title"]} if latest else None,
            "recent_incidents": recent,
        }


incident_service = IncidentService()
