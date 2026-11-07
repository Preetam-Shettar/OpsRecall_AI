import json

import httpx

from app.services import analysis_service
from app.services.analysis_service import AnalysisService


INCIDENT = {
    "title": "Orders API timeouts",
    "service": "orders-api",
    "environment": "staging",
    "description": "Requests started failing after deployment.",
    "sanitized_logs": "Database connection acquisition timed out.",
}


def groq_content():
    return {
        "summary": "Database connection acquisition is timing out.",
        "symptoms": ["Request timeouts"],
        "possible_causes": [{
            "cause": "Connection pool pressure",
            "evidence": ["The sanitized logs report an acquisition timeout."],
            "confidence": "medium",
        }],
        "supporting_evidence": ["The incident logs report a database acquisition timeout."],
        "related_memory_insights": [],
        "recommended_checks": ["Review database connection pool metrics."],
        "missing_information": ["Connection pool utilization during the incident."],
        "confidence": "medium",
        "safety_notes": ["No production changes were made."],
    }


def test_uses_local_analysis_without_groq_credentials(monkeypatch):
    monkeypatch.setattr(analysis_service, "GROQ_API_KEY", None)

    result = AnalysisService().analyze_incident(INCIDENT, prior_memories=[])

    assert result["analysis_source"] == "local"
    assert result["analysis_notice"]
    assert result["summary"]


def test_uses_and_validates_groq_json_response(monkeypatch):
    monkeypatch.setattr(analysis_service, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(analysis_service, "GROQ_MODEL", "test-model")
    request_data = {}

    def fake_post(url, **kwargs):
        request_data.update({"url": url, **kwargs})
        return httpx.Response(
            200,
            json={
                "choices": [{
                    "message": {"content": json.dumps(groq_content())},
                    "finish_reason": "stop",
                }],
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(analysis_service.httpx, "post", fake_post)
    memories = [{"incident_id": "INC-010", "content": "Pool size was increased after a verified outage."}]

    incident_with_secret = {
        **INCIDENT,
        "sanitized_logs": "api_key: abcdefgh12345678",
    }
    result = AnalysisService().analyze_incident(incident_with_secret, prior_memories=memories)

    assert result["analysis_source"] == "groq"
    assert result["analysis_notice"] is None
    assert result["related_memory_insights"] == [{
        "incident_id": "INC-010",
        "lesson": "Pool size was increased after a verified outage.",
    }]
    assert request_data["headers"]["Authorization"].split() == ["Bearer", "test-key"]
    assert request_data["json"]["response_format"] == {"type": "json_object"}
    assert request_data["timeout"] == 20
    assert "abcdefgh12345678" not in request_data["json"]["messages"][1]["content"]


def test_groq_failure_returns_visible_local_fallback(monkeypatch):
    monkeypatch.setattr(analysis_service, "GROQ_API_KEY", "test-key")

    def fail_request(*args, **kwargs):
        raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(analysis_service.httpx, "post", fail_request)

    result = AnalysisService().analyze_incident(INCIDENT, prior_memories=[])

    assert result["analysis_source"] == "local_fallback"
    assert "Groq analysis was unavailable" in result["analysis_notice"]
    assert result["summary"]


def test_invalid_groq_schema_returns_visible_local_fallback(monkeypatch):
    monkeypatch.setattr(analysis_service, "GROQ_API_KEY", "test-key")

    def invalid_response(url, **kwargs):
        return httpx.Response(
            200,
            json={
                "choices": [{
                    "message": {"content": '{"summary":"incomplete"}'},
                    "finish_reason": "stop",
                }],
            },
            request=httpx.Request("POST", url),
        )

    monkeypatch.setattr(analysis_service.httpx, "post", invalid_response)

    result = AnalysisService().analyze_incident(INCIDENT, prior_memories=[])

    assert result["analysis_source"] == "local_fallback"
    assert result["analysis_notice"]
