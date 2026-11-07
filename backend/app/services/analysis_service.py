import re
from typing import Any

from app.services.hindsight_service import memory_client
from app.services.log_parser import extract_signal_terms


class AnalysisService:
    def analyze_incident(self, incident: dict[str, Any], prior_memories: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        logs_text = (incident.get("sanitized_logs") or incident.get("description") or "").lower()
        query = " ".join(
            [
                incident.get("title", ""),
                incident.get("service", ""),
                incident.get("environment", ""),
                incident.get("description", ""),
                logs_text,
            ]
        )
        memories = prior_memories if prior_memories is not None else memory_client.recall(query)

        signal_terms = extract_signal_terms(incident.get("sanitized_logs") or incident.get("description") or "")
        if "timeout" in logs_text or "timed out" in logs_text or "database" in logs_text:
            summary = "The incident appears to involve a backend dependency bottleneck or connection exhaustion."
            symptoms = ["Request timeouts", "Back-end dependency latency", "Intermittent 5xx responses"]
            causes = [{
                "cause": "Database connection pool exhaustion or slow dependency response",
                "evidence": ["Timeouts were observed in the supplied logs", "The service is affected during a deployment or scale event"],
                "confidence": "medium",
            }]
            checks = [
                "Inspect active and idle database connections.",
                "Review connection pool limits and worker thread counts.",
                "Compare the deployment or traffic change against the incident window.",
            ]
        elif "error" in logs_text or "500" in logs_text:
            summary = "The service is showing repeated application or upstream failures that need isolation first."
            symptoms = ["HTTP 500 responses", "Application error logs", "User-facing failures"]
            causes = [{
                "cause": "An upstream dependency or application-level error path is failing under load",
                "evidence": ["The logs mention repeated exceptions or API failures", "The issue is localized to a specific service or environment"],
                "confidence": "medium",
            }]
            checks = [
                "Review the relevant stack trace and recent deployments.",
                "Check dependency health metrics and queue depth.",
                "Validate whether a config change introduced the regression.",
            ]
        else:
            summary = "The evidence suggests a degraded service path, but additional signals are needed to narrow the root cause."
            symptoms = ["Service instability", "Operational anomalies", "User impact noted"]
            causes = [{
                "cause": "A service dependency, configuration, or resource issue is likely",
                "evidence": ["The provided logs indicate a service problem", "Evidence is currently insufficient to confirm a single root cause"],
                "confidence": "low",
            }]
            checks = [
                "Gather a focused stack trace, dependency metrics, and deployment timeline.",
                "Review recent config changes and recent resource spikes.",
                "Confirm whether the issue is limited to one environment or service.",
            ]

        related = []
        for item in memories[:3]:
            label = item.get("context", "Prior incident")
            content = item.get("content", "")
            if content:
                related.append({
                    "incident_id": item.get("incident_id", label),
                    "lesson": content[:220],
                })

        recommendation = {
            "summary": summary,
            "symptoms": symptoms,
            "possible_causes": causes,
            "supporting_evidence": [
                "The supplied incident text and logs were reviewed for operational patterns.",
                "Historical similar incidents were used as context when available.",
            ] + ([f"Matched signal: {term}" for term in signal_terms[:4]] if signal_terms else []),
            "related_memory_insights": related,
            "recommended_checks": checks,
            "missing_information": [
                "Recent deployment or change log.",
                "Dependency and infrastructure metrics during the incident window.",
            ],
            "confidence": "medium" if causes[0]["confidence"] != "low" else "low",
            "safety_notes": [
                "No production changes or commands were executed.",
                "The diagnosis remains evidence-based and should be validated by an engineer.",
            ],
        }
        return recommendation
