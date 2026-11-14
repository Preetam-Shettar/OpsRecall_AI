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


def test_explainable_local_analysis_structure(monkeypatch):
    monkeypatch.setattr(analysis_service, "GROQ_API_KEY", None)

    incident = {
        "title": "Orders API database connection pool exhausted",
        "service": "orders-api",
        "environment": "production",
        "description": "500 errors spike following traffic increase.",
        "sanitized_logs": (
            "2026-11-14 10:15:22 ERROR [orders-api] Failed to acquire database connection\n"
            "2026-11-14 10:15:23 ERROR [orders-api] Connection pool exhausted\n"
            "2026-11-14 10:15:24 WARN  [orders-api] Request timeout after 30000ms\n"
            "2026-11-14 10:15:25 ERROR [orders-api] POST /orders returned HTTP 500\n"
        ),
    }
    result = AnalysisService().analyze_incident(incident, prior_memories=[])

    # 1. Primary cause hypothesis
    assert result["primary_cause"] is not None
    assert "pool" in result["primary_cause"]["cause"].lower()
    assert result["primary_cause"]["confidence"] in ("low", "medium", "high")

    # 2. Reasoning chain
    assert len(result["reasoning_chain"]) >= 3
    assert any("Mechanism" in step or "Detection" in step for step in result["reasoning_chain"])

    # 3. Alternative hypotheses with ruling out rationale
    assert len(result["alternative_hypotheses"]) >= 1
    for alt in result["alternative_hypotheses"]:
        assert alt["cause"]
        assert alt["status"] in ("alternative", "less_likely", "ruled_out")
        assert len(alt["ruling_out_rationale"]) > 0

    # 4. Verbatim supporting log excerpts with line numbers
    assert len(result["supporting_log_excerpts"]) >= 2
    for excerpt in result["supporting_log_excerpts"]:
        assert excerpt["line_number"] is not None
        assert excerpt["log_text"]
        assert excerpt["signal_matched"]

    # 5. Qualitative confidence justification (no fake percentage probability)
    assert result["confidence"] in ("low", "medium", "high")
    assert result["confidence_justification"] is not None
    assert "confidence" in result["confidence_justification"].lower()
    assert "%" not in result["confidence_justification"]

    # 6. Structured checks with safety classifications
    assert len(result["structured_checks"]) >= 2
    types = {c["check_type"] for c in result["structured_checks"]}
    assert "read_only" in types
    # Confirm command hints are populated where appropriate
    read_only_checks = [c for c in result["structured_checks"] if c["check_type"] == "read_only"]
    assert any(c.get("command_hint") for c in read_only_checks)


def test_backward_compatibility_with_legacy_analysis_records():
    from app.schemas.analysis import IncidentAnalysis

    legacy_payload = {
        "summary": "Legacy incident summary from SQLite",
        "symptoms": ["High latency"],
        "possible_causes": [{
            "cause": "Network latency",
            "evidence": ["Ping times were 200ms"],
            "confidence": "medium",
        }],
        "supporting_evidence": ["Ping records"],
        "related_memory_insights": [],
        "recommended_checks": ["Check router metrics"],
        "missing_information": [],
        "confidence": "medium",
        "safety_notes": ["No actions taken"],
        "analysis_source": "local",
    }
    # Must validate cleanly without errors
    validated = IncidentAnalysis.model_validate(legacy_payload)
    dumped = validated.model_dump()

    assert dumped["summary"] == legacy_payload["summary"]
    assert dumped["primary_cause"] is None
    assert dumped["reasoning_chain"] == []
    assert dumped["alternative_hypotheses"] == []
    assert dumped["supporting_log_excerpts"] == []
    assert dumped["confidence_justification"] is None
    assert dumped["structured_checks"] == []

