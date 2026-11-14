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

        # Step 4: Emit initial timeline events for incident detection and analysis
        self.record_timeline_event(
            incident_id=incident_id,
            event_type="incident_created",
            description=f"Incident registered for service '{incident_record['service']}' in {incident_record['environment']}. Severity: {severity.upper()}.",
            actor="OpsRecall AI",
            actor_type="ai",
            created_at=now,
        )
        summary_snippet = analysis.get("summary") or "Diagnostic analysis generated."
        if len(summary_snippet) > 140:
            summary_snippet = summary_snippet[:137] + "..."
        self.record_timeline_event(
            incident_id=incident_id,
            event_type="analysis_completed",
            description=f"AI diagnostic investigation completed. Summary: {summary_snippet}",
            actor="OpsRecall AI",
            actor_type="ai",
            created_at=now,
        )

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

        # Emit chronological timeline events for resolution and verification
        eng_name = resolution["engineer"] or "On-call Engineer"
        self.record_timeline_event(
            incident_id=incident_id,
            event_type="resolution_submitted",
            description=f"Resolution submitted by {eng_name}. Confirmed root cause: {payload['root_cause'][:120]}.",
            actor=eng_name,
            actor_type="engineer",
            created_at=now_iso,
        )
        if is_verified:
            self.record_timeline_event(
                incident_id=incident_id,
                event_type="resolution_verified",
                description="Resolution verified by engineer. Stored in institutional memory bank.",
                actor=eng_name,
                actor_type="engineer",
                created_at=now_iso,
            )
            self.record_timeline_event(
                incident_id=incident_id,
                event_type="incident_resolved",
                description=f"Incident closed with outcome: {outcome.upper()}.",
                actor="OpsRecall AI",
                actor_type="system",
                created_at=now_iso,
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

        # Action plan and response tracking telemetry
        with get_connection() as conn:
            has_act_table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='incident_actions'"
            ).fetchone()
            if has_act_table:
                total_acts = conn.execute("SELECT COUNT(*) as c FROM incident_actions").fetchone()["c"]
                comp_acts = conn.execute("SELECT COUNT(*) as c FROM incident_actions WHERE status = 'completed'").fetchone()["c"]
                block_acts = conn.execute("SELECT COUNT(*) as c FROM incident_actions WHERE status = 'blocked'").fetchone()["c"]
                inprog_acts = conn.execute("SELECT COUNT(*) as c FROM incident_actions WHERE status = 'in_progress'").fetchone()["c"]
                pend_acts = conn.execute("SELECT COUNT(*) as c FROM incident_actions WHERE status = 'pending'").fetchone()["c"]
            else:
                total_acts = comp_acts = block_acts = inprog_acts = pend_acts = 0

        actions_summary = {
            "total_actions": total_acts,
            "completed_actions": comp_acts,
            "blocked_actions": block_acts,
            "in_progress_actions": inprog_acts,
            "pending_actions": pend_acts,
            "completion_rate": round((comp_acts / total_acts * 100), 1) if total_acts > 0 else 0,
            "blocked_rate": round((block_acts / total_acts * 100), 1) if total_acts > 0 else 0,
        }

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
                "actions_summary": actions_summary,
            },
            "actions_summary": actions_summary,
            "memory_intelligence": memory_intel,
            "latest_incident": {"id": latest["id"], "title": latest["title"]} if latest else None,
            "recent_incidents": recent,
        }

    def _get_storage_provider(self) -> str:
        """
        Determines the active memory storage provider.
        Does NOT infer cloud connectivity from bank_id; checks valid cloud credentials.
        """
        from app.config import HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL
        is_cloud = bool(
            HINDSIGHT_BASE_URL
            and HINDSIGHT_API_KEY
            and HINDSIGHT_API_KEY.strip()
            and HINDSIGHT_API_KEY.strip() != "replace_with_your_key"
        )
        return "Hindsight Cloud" if is_cloud else "Local SQLite Fallback"

    def _parse_memory_content(self, content: str) -> dict[str, Any]:
        """
        Extracts structured operational fields from memory content text as fallback
        when the parent incident record is missing or was deleted.
        """
        extracted = {
            "incident_id": None,
            "service": None,
            "environment": "production",
            "symptoms": None,
            "root_cause": "Verified resolution recorded in memory bank.",
            "resolution": "Applied verified remediation.",
            "outcome": "resolved",
            "engineer": None,
            "timestamp": None,
            "severity": "medium",
        }
        if not content:
            return extracted

        for line in content.splitlines():
            line_str = line.strip()
            if line_str.startswith("Incident ID:"):
                extracted["incident_id"] = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Service:"):
                extracted["service"] = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Environment:"):
                env_val = line_str.split(":", 1)[1].strip().lower()
                extracted["environment"] = env_val
                if env_val == "production":
                    extracted["severity"] = "critical"
            elif line_str.startswith("Symptoms:"):
                extracted["symptoms"] = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Confirmed root cause:"):
                extracted["root_cause"] = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Verified resolution:"):
                extracted["resolution"] = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Outcome:"):
                extracted["outcome"] = line_str.split(":", 1)[1].strip()
            elif line_str.startswith("Verification:"):
                v_text = line_str.split(":", 1)[1].strip()
                extracted["engineer"] = v_text.replace("confirmed by engineer", "").strip()
            elif line_str.startswith("Timestamp:"):
                extracted["timestamp"] = line_str.split(":", 1)[1].strip()

        return extracted

    def _get_citation_map(self) -> tuple[dict[str, int], dict[str, list[dict[str, Any]]]]:
        """
        Calculates de-duplicated recall citation statistics from actual incident analyses.
        Counting rule: an incident citing a target memory (even multiple times in its analysis)
        is counted exactly once for that memory to prevent inflation or duplicate counts.
        """
        citation_counts: dict[str, int] = {}
        citation_refs: dict[str, list[dict[str, Any]]] = {}

        with get_connection() as conn:
            rows = conn.execute("SELECT id, title, service, environment, analysis_json FROM incidents").fetchall()

        for row in rows:
            if not row["analysis_json"]:
                continue
            try:
                analysis = json.loads(row["analysis_json"])
                insights = analysis.get("related_memory_insights", [])
                cited_in_this_incident: set[str] = set()
                for item in insights:
                    if isinstance(item, dict) and item.get("incident_id"):
                        cited_in_this_incident.add(str(item["incident_id"]).strip())

                for target_id in cited_in_this_incident:
                    citation_counts[target_id] = citation_counts.get(target_id, 0) + 1
                    if target_id not in citation_refs:
                        citation_refs[target_id] = []
                    citation_refs[target_id].append({
                        "id": row["id"],
                        "title": row["title"],
                        "service": row["service"],
                        "environment": row["environment"],
                    })
            except Exception:
                pass

        return citation_counts, citation_refs

    def list_memories(
        self,
        search: str | None = None,
        service: str | None = None,
        severity: str | None = None,
        environment: str | None = None,
        verified: bool | None = True,
        page: int = 1,
        page_size: int = 10,
    ) -> dict[str, Any]:
        """
        Retrieves a paginated list of incident memories from the database.
        Default: verified=True (only verified memories in the trusted catalog).
        """
        # Defensive parameter normalization (supports direct Python calls with Query defaults)
        if hasattr(page, "default"):
            page = 1
        else:
            try:
                page = int(page)
            except (ValueError, TypeError):
                page = 1

        if hasattr(page_size, "default"):
            page_size = 10
        else:
            try:
                page_size = int(page_size)
            except (ValueError, TypeError):
                page_size = 10

        search = None if hasattr(search, "default") else (str(search) if search else None)
        service = None if hasattr(service, "default") else (str(service) if service else None)
        severity = None if hasattr(severity, "default") else (str(severity) if severity else None)
        environment = None if hasattr(environment, "default") else (str(environment) if environment else None)
        if hasattr(verified, "default"):
            verified = True
        elif verified is not None:
            verified = bool(verified)

        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 10
        elif page_size > 100:
            page_size = 100

        citation_counts, _ = self._get_citation_map()
        storage_provider = self._get_storage_provider()

        with get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(incidents)")
            inc_cols = [r["name"] for r in cursor.fetchall()]
            has_severity = "severity" in inc_cols
            sev_sql = "i.severity" if has_severity else "NULL as severity"

            query = f"""
            SELECT m.*, i.title, {sev_sql}, i.environment as inc_env,
                   i.description as inc_desc, i.resolution_json, i.sanitized_logs, i.logs
            FROM memories m
            LEFT JOIN incidents i ON m.incident_id = i.id
            ORDER BY m.created_at DESC, m.id DESC
            """
            rows = conn.execute(query).fetchall()

        all_memories = []
        for r in rows:
            m_dict = dict(r)
            content = m_dict.get("content") or ""
            fallback = self._parse_memory_content(content)

            has_parent = r["title"] is not None
            inc_id = r["incident_id"] or fallback.get("incident_id") or f"MEM-{r['id']}"
            svc = r["service"] or fallback.get("service") or "unknown"
            env = r["inc_env"] or fallback.get("environment") or "production"

            res_obj = None
            if r["resolution_json"]:
                try:
                    res_obj = json.loads(r["resolution_json"])
                except Exception:
                    pass

            root_cause = (
                (res_obj.get("root_cause") if res_obj else None)
                or fallback.get("root_cause")
                or "Confirmed root cause recorded in memory bank."
            )
            resolution = (
                (res_obj.get("resolution") if res_obj else None)
                or fallback.get("resolution")
                or "Verified remediation applied."
            )
            engineer = (res_obj.get("engineer") if res_obj else None) or fallback.get("engineer")
            outcome = r["outcome"] or (res_obj.get("outcome") if res_obj else None) or "resolved"

            sev = r["severity"] or fallback.get("severity") or ("critical" if env == "production" else "medium")
            title = r["title"] or f"{svc.upper()} - {root_cause[:45]}"

            is_verified = bool(r["verified"] if r["verified"] is not None else 1)
            rec_count = citation_counts.get(inc_id, 0)

            all_memories.append({
                "id": r["id"],
                "incident_id": inc_id,
                "title": title,
                "service": svc,
                "environment": env,
                "severity": sev.lower(),
                "root_cause": root_cause,
                "resolution": resolution,
                "outcome": outcome,
                "verified": is_verified,
                "engineer": engineer,
                "created_at": r["created_at"],
                "storage_provider": storage_provider,
                "bank_id": r["bank_id"] or "opsrecall-incidents",
                "recall_count": rec_count,
                "has_parent_incident": has_parent,
            })

        # Apply filtering
        filtered = all_memories

        # Default: True (only verified records)
        if verified is not None:
            filtered = [m for m in filtered if m["verified"] is verified]

        if service:
            s_clean = service.lower().strip()
            filtered = [m for m in filtered if m["service"].lower() == s_clean]

        if severity:
            sev_clean = severity.lower().strip()
            filtered = [m for m in filtered if m["severity"] == sev_clean]

        if environment:
            env_clean = environment.lower().strip()
            filtered = [m for m in filtered if m["environment"].lower() == env_clean]

        if search:
            q = search.lower().strip()
            filtered = [
                m for m in filtered
                if q in m["incident_id"].lower()
                or q in m["service"].lower()
                or q in m["title"].lower()
                or q in m["root_cause"].lower()
                or q in m["resolution"].lower()
            ]

        total = len(filtered)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = filtered[start_idx:end_idx]
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "verified_only": verified is True,
        }

    def get_memory_detail(self, memory_id: int | str) -> dict[str, Any] | None:
        """
        Retrieves detailed memory intelligence for a specific record.
        Includes sanitized evidence logs, root cause, resolution, and citation references.
        Handles missing parent incidents gracefully.
        """
        citation_counts, citation_refs = self._get_citation_map()
        storage_provider = self._get_storage_provider()

        with get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(incidents)")
            inc_cols = [r["name"] for r in cursor.fetchall()]
            has_severity = "severity" in inc_cols
            sev_sql = "i.severity" if has_severity else "NULL as severity"

            # Check if memory_id is integer or string incident_id
            int_val = None
            try:
                int_val = int(memory_id)
            except ValueError:
                pass

            if int_val is not None:
                row = conn.execute(
                    f"""
                    SELECT m.*, i.id as inc_full_id, i.title, {sev_sql}, i.environment as inc_env,
                           i.description as inc_desc, i.resolution_json, i.sanitized_logs, i.logs
                    FROM memories m
                    LEFT JOIN incidents i ON m.incident_id = i.id
                    WHERE m.id = ?
                    """,
                    (int_val,),
                ).fetchone()
            else:
                row = conn.execute(
                    f"""
                    SELECT m.*, i.id as inc_full_id, i.title, {sev_sql}, i.environment as inc_env,
                           i.description as inc_desc, i.resolution_json, i.sanitized_logs, i.logs
                    FROM memories m
                    LEFT JOIN incidents i ON m.incident_id = i.id
                    WHERE m.incident_id = ?
                    ORDER BY m.id DESC LIMIT 1
                    """,
                    (str(memory_id),),
                ).fetchone()

            if not row:
                return None

            # Find related incident IDs sharing the same service
            svc_name = row["service"]
            related_ids = []
            if svc_name:
                rel_rows = conn.execute(
                    "SELECT id FROM incidents WHERE service = ? AND id != ? LIMIT 5",
                    (svc_name, row["incident_id"] or ""),
                ).fetchall()
                related_ids = [r["id"] for r in rel_rows]

        content = row["content"] or ""
        fallback = self._parse_memory_content(content)
        has_parent = row["title"] is not None

        inc_id = row["incident_id"] or fallback.get("incident_id") or f"MEM-{row['id']}"
        svc = row["service"] or fallback.get("service") or "unknown"
        env = row["inc_env"] or fallback.get("environment") or "production"

        res_obj = None
        if row["resolution_json"]:
            try:
                res_obj = json.loads(row["resolution_json"])
            except Exception:
                pass

        root_cause = (
            (res_obj.get("root_cause") if res_obj else None)
            or fallback.get("root_cause")
            or "Confirmed root cause recorded in memory bank."
        )
        resolution = (
            (res_obj.get("resolution") if res_obj else None)
            or fallback.get("resolution")
            or "Verified remediation applied."
        )
        engineer = (res_obj.get("engineer") if res_obj else None) or fallback.get("engineer")
        outcome = row["outcome"] or (res_obj.get("outcome") if res_obj else None) or "resolved"
        sev = row["severity"] or fallback.get("severity") or ("critical" if env == "production" else "medium")
        title = row["title"] or f"{svc.upper()} - {root_cause[:45]}"

        # Always sanitize evidence logs before returning
        raw_logs = row["sanitized_logs"] or row["logs"]
        evidence_logs = sanitize_logs(raw_logs) if raw_logs else fallback.get("symptoms")

        # De-duplicated recall citations
        rec_count = citation_counts.get(inc_id, 0)
        recalled_in = citation_refs.get(inc_id, [])

        return {
            "id": row["id"],
            "incident_id": inc_id,
            "title": title,
            "service": svc,
            "environment": env,
            "severity": sev.lower(),
            "root_cause": root_cause,
            "resolution": resolution,
            "outcome": outcome,
            "verified": bool(row["verified"] if row["verified"] is not None else 1),
            "engineer": engineer,
            "created_at": row["created_at"],
            "storage_provider": storage_provider,
            "bank_id": row["bank_id"] or "opsrecall-incidents",
            "recall_count": rec_count,
            "has_parent_incident": has_parent,
            "content": content,
            "context": row["context"],
            "evidence_logs": evidence_logs,
            "symptoms": row["inc_desc"] or fallback.get("symptoms"),
            "related_incident_ids": related_ids,
            "recalled_in_incidents": recalled_in,
        }

    # =========================================================================
    # Part 4: Guided Incident Response, Action Plan & Timeline Tracking
    # =========================================================================

    def _generate_action_id(self, incident_id: str) -> str:
        unique_suffix = uuid.uuid4().hex[:6].upper()
        inc_tag = incident_id.replace("INC-", "").split("-")[-1] if "INC-" in incident_id else incident_id[:6]
        return f"ACT-{inc_tag}-{unique_suffix}"

    def record_timeline_event(
        self,
        incident_id: str,
        event_type: str,
        description: str,
        actor: str = "OpsRecall AI",
        actor_type: str = "ai",
        related_action_id: str | None = None,
        created_at: str | None = None,
    ) -> dict[str, Any]:
        now_iso = created_at or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO incident_timeline (
                    incident_id, event_type, description, actor, actor_type, related_action_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (incident_id, event_type, sanitize_logs(description), actor, actor_type, related_action_id, now_iso),
            )
            event_id = cursor.lastrowid
        return {
            "id": event_id,
            "incident_id": incident_id,
            "event_type": event_type,
            "description": description,
            "actor": actor,
            "actor_type": actor_type,
            "related_action_id": related_action_id,
            "created_at": now_iso,
        }

    def create_action(self, incident_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        incident = self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found")

        action_id = self._generate_action_id(incident_id)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        title = payload.get("title", "").strip()
        if not title:
            raise ValueError("Action title cannot be empty")

        category = payload.get("category", "read_only")
        if category not in ("read_only", "active_validation", "mitigation"):
            category = "read_only"

        priority = payload.get("priority", "medium")
        if priority not in ("critical", "high", "medium", "low"):
            priority = "medium"

        assigned_engineer = payload.get("assigned_engineer")
        command_hint = sanitize_logs(payload.get("command_hint") or "") if payload.get("command_hint") else None
        description = sanitize_logs(payload.get("description") or "")
        actor = payload.get("actor") or assigned_engineer or "On-call Engineer"

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO incident_actions (
                    id, incident_id, title, description, category, priority, status,
                    assigned_engineer, command_hint, completion_notes, blocked_reason,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?, NULL, NULL, ?, ?)
                """,
                (
                    action_id,
                    incident_id,
                    title,
                    description,
                    category,
                    priority,
                    assigned_engineer,
                    command_hint,
                    now_iso,
                    now_iso,
                ),
            )

        cat_label = category.replace("_", " ").upper()
        self.record_timeline_event(
            incident_id=incident_id,
            event_type="action_created",
            description=f"Action '{title}' added to response plan [{cat_label}].",
            actor=actor,
            actor_type="engineer" if actor != "OpsRecall AI" else "ai",
            related_action_id=action_id,
            created_at=now_iso,
        )

        return self.get_action(incident_id, action_id)

    def list_actions(
        self,
        incident_id: str,
        status: str | None = None,
        category: str | None = None,
    ) -> list[dict[str, Any]]:
        incident = self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found")

        query = "SELECT * FROM incident_actions WHERE incident_id = ?"
        params = [incident_id]
        if isinstance(status, str) and status:
            query += " AND status = ?"
            params.append(status)
        if isinstance(category, str) and category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY created_at ASC"

        with get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def get_action(self, incident_id: str, action_id: str) -> dict[str, Any]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM incident_actions WHERE incident_id = ? AND id = ?",
                (incident_id, action_id),
            ).fetchone()
            if not row:
                raise ValueError(f"Action '{action_id}' not found for incident '{incident_id}'")
            return dict(row)

    def update_action(self, incident_id: str, action_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        existing = self.get_action(incident_id, action_id)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        new_status = payload.get("status")
        if new_status and new_status not in ("pending", "in_progress", "completed", "blocked"):
            raise ValueError(f"Invalid action status '{new_status}'. Allowed: pending, in_progress, completed, blocked")

        assigned_engineer = payload.get("assigned_engineer") if "assigned_engineer" in payload else existing["assigned_engineer"]
        priority = payload.get("priority") if "priority" in payload else existing["priority"]
        if priority and priority not in ("critical", "high", "medium", "low"):
            priority = existing["priority"]

        completion_notes = (
            sanitize_logs(payload.get("completion_notes") or "")
            if "completion_notes" in payload and payload.get("completion_notes")
            else existing["completion_notes"]
        )
        blocked_reason = (
            sanitize_logs(payload.get("blocked_reason") or "")
            if "blocked_reason" in payload and payload.get("blocked_reason")
            else existing["blocked_reason"]
        )
        actor = payload.get("actor") or assigned_engineer or existing["assigned_engineer"] or "On-call Engineer"

        target_status = new_status or existing["status"]

        with get_connection() as conn:
            conn.execute(
                """
                UPDATE incident_actions
                SET status = ?, assigned_engineer = ?, priority = ?, completion_notes = ?, blocked_reason = ?, updated_at = ?
                WHERE incident_id = ? AND id = ?
                """,
                (
                    target_status,
                    assigned_engineer,
                    priority,
                    completion_notes,
                    blocked_reason,
                    now_iso,
                    incident_id,
                    action_id,
                ),
            )

        # Emit targeted timeline events
        if new_status and new_status != existing["status"]:
            if new_status == "in_progress":
                self.record_timeline_event(
                    incident_id=incident_id,
                    event_type="action_started",
                    description=f"Investigation started on action '{existing['title']}'.",
                    actor=actor,
                    actor_type="engineer",
                    related_action_id=action_id,
                    created_at=now_iso,
                )
            elif new_status == "completed":
                finding_snippet = f" Findings: {completion_notes}" if completion_notes else ""
                self.record_timeline_event(
                    incident_id=incident_id,
                    event_type="action_completed",
                    description=f"Action '{existing['title']}' completed successfully.{finding_snippet}",
                    actor=actor,
                    actor_type="engineer",
                    related_action_id=action_id,
                    created_at=now_iso,
                )
            elif new_status == "blocked":
                reason_snippet = f" Reason: {blocked_reason}" if blocked_reason else ""
                self.record_timeline_event(
                    incident_id=incident_id,
                    event_type="action_blocked",
                    description=f"Action '{existing['title']}' marked as blocked.{reason_snippet}",
                    actor=actor,
                    actor_type="engineer",
                    related_action_id=action_id,
                    created_at=now_iso,
                )
            elif new_status == "pending":
                self.record_timeline_event(
                    incident_id=incident_id,
                    event_type="action_reset",
                    description=f"Action '{existing['title']}' reset back to pending queue.",
                    actor=actor,
                    actor_type="engineer",
                    related_action_id=action_id,
                    created_at=now_iso,
                )

        if "assigned_engineer" in payload and payload["assigned_engineer"] != existing["assigned_engineer"]:
            new_assignee = payload["assigned_engineer"] or "unassigned"
            self.record_timeline_event(
                incident_id=incident_id,
                event_type="engineer_assigned",
                description=f"Assigned action '{existing['title']}' to {new_assignee}.",
                actor=actor,
                actor_type="engineer",
                related_action_id=action_id,
                created_at=now_iso,
            )

        return self.get_action(incident_id, action_id)

    def import_recommendations_to_actions(
        self,
        incident_id: str,
        actor: str = "On-call Engineer",
    ) -> list[dict[str, Any]]:
        incident = self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found")

        analysis = incident.get("analysis") or {}
        structured_checks = analysis.get("structured_checks", [])
        recommended_checks = analysis.get("recommended_checks", [])

        existing_actions = self.list_actions(incident_id)
        existing_titles = {a["title"].strip().lower() for a in existing_actions}

        created = []
        if structured_checks:
            for chk in structured_checks:
                if isinstance(chk, dict):
                    title = chk.get("check", "").strip()
                    if title and title.lower() not in existing_titles:
                        ctype = chk.get("check_type", "read_only")
                        cmd = chk.get("command_hint")
                        priority = "high" if ctype == "mitigation" else "medium"
                        action = self.create_action(
                            incident_id,
                            {
                                "title": title,
                                "description": f"Imported from explainable AI diagnostic check ({ctype.replace('_', ' ')}).",
                                "category": ctype,
                                "priority": priority,
                                "command_hint": cmd,
                                "actor": actor,
                            },
                        )
                        created.append(action)
                        existing_titles.add(title.lower())
        elif recommended_checks:
            for text in recommended_checks:
                if isinstance(text, str):
                    title = text.strip()
                    if title and title.lower() not in existing_titles:
                        t_lower = title.lower()
                        if any(w in t_lower for w in ["mitigat", "restart", "rollback", "scale", "kill", "flush", "evict"]):
                            ctype = "mitigation"
                            priority = "high"
                        elif any(w in t_lower for w in ["curl", "ping", "test", "probe", "query", "load", "active", "benchmark"]):
                            ctype = "active_validation"
                            priority = "medium"
                        else:
                            ctype = "read_only"
                            priority = "medium"

                        action = self.create_action(
                            incident_id,
                            {
                                "title": title,
                                "description": "Imported from recommended diagnostic checks.",
                                "category": ctype,
                                "priority": priority,
                                "command_hint": None,
                                "actor": actor,
                            },
                        )
                        created.append(action)
                        existing_titles.add(title.lower())

        if created:
            self.record_timeline_event(
                incident_id=incident_id,
                event_type="actions_imported",
                description=f"Imported {len(created)} diagnostic checks from AI investigation into active response plan.",
                actor=actor,
                actor_type="engineer",
            )

        return created

    def get_timeline(self, incident_id: str, limit: int = 150) -> list[dict[str, Any]]:
        incident = self.get_incident(incident_id)
        if not incident:
            raise ValueError(f"Incident '{incident_id}' not found")

        limit_val = limit if isinstance(limit, int) else 150

        with get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM incident_timeline
                WHERE incident_id = ?
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                """,
                (incident_id, limit_val),
            ).fetchall()
            events = [dict(r) for r in rows]

        if not events:
            now_iso = incident["created_at"]
            e1 = self.record_timeline_event(
                incident_id=incident_id,
                event_type="incident_created",
                description=f"Incident registered for service '{incident['service']}' in {incident['environment']}. Severity: {incident.get('severity', 'medium').upper()}.",
                actor="OpsRecall AI",
                actor_type="ai",
                created_at=now_iso,
            )
            events.append(e1)
            if incident.get("analysis"):
                summary_snippet = incident["analysis"].get("summary") or "Diagnostic analysis generated."
                if len(summary_snippet) > 140:
                    summary_snippet = summary_snippet[:137] + "..."
                e2 = self.record_timeline_event(
                    incident_id=incident_id,
                    event_type="analysis_completed",
                    description=f"AI diagnostic investigation completed. Summary: {summary_snippet}",
                    actor="OpsRecall AI",
                    actor_type="ai",
                    created_at=now_iso,
                )
                events.append(e2)
            if incident.get("resolution"):
                res = incident["resolution"]
                e3 = self.record_timeline_event(
                    incident_id=incident_id,
                    event_type="resolution_submitted",
                    description=f"Resolution submitted by '{res.get('engineer', 'Engineer')}'. Outcome: {res.get('outcome', 'resolved').upper()}.",
                    actor=res.get("engineer") or "On-call Engineer",
                    actor_type="engineer",
                    created_at=res.get("resolved_at") or incident["updated_at"],
                )
                events.append(e3)

        return events

    def get_action_plan_summary(self, incident_id: str) -> dict[str, Any]:
        actions = self.list_actions(incident_id)
        total = len(actions)
        completed = sum(1 for a in actions if a["status"] == "completed")
        in_progress = sum(1 for a in actions if a["status"] == "in_progress")
        pending = sum(1 for a in actions if a["status"] == "pending")
        blocked = sum(1 for a in actions if a["status"] == "blocked")
        pct = round((completed / total * 100)) if total > 0 else 0

        return {
            "incident_id": incident_id,
            "total_actions": total,
            "completed_actions": completed,
            "in_progress_actions": in_progress,
            "pending_actions": pending,
            "blocked_actions": blocked,
            "progress_pct": pct,
            "actions": actions,
        }


incident_service = IncidentService()
