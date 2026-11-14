from app.services.log_parser import (
    extract_log_evidence_snippets,
    extract_signal_terms,
    sanitize_logs,
)


def test_sanitize_logs_redacts_api_keys_and_tokens():
    raw_logs = (
        "2026-11-07 10:12:00 ERROR api_key: abcdefgh12345678 "
        "Authorization: Bearer my-secret-jwt-token-xyz123 "
        "Failed database connection sk-proj-1234567890abcdef "
        "password: SuperSecretPassword123!"
    )
    sanitized = sanitize_logs(raw_logs)

    assert "abcdefgh12345678" not in sanitized
    assert "my-secret-jwt-token-xyz123" not in sanitized
    assert "sk-proj-1234567890abcdef" not in sanitized
    assert "SuperSecretPassword123!" not in sanitized
    assert "[REDACTED_SECRET]" in sanitized


def test_sanitize_logs_handles_empty():
    assert sanitize_logs("") == ""
    assert sanitize_logs(None) == ""


def test_extract_signal_terms():
    sample_log = (
        "2026-11-07 10:12:01 ERROR orders-api Database connection acquisition timed out. "
        "Active connections reached configured maximum in pool. HTTP 500 returned."
    )
    signals = extract_signal_terms(sample_log)
    assert "timeout" in signals
    assert "database" in signals
    assert "pool" in signals
    assert "500" in signals


def test_extract_log_evidence_snippets_exact_and_line_numbers():
    raw_logs = (
        "2026-11-14 10:15:20 INFO  [orders-api] Starting service on port 8080\n"
        "2026-11-14 10:15:22 ERROR [orders-api] Failed to acquire database connection\n"
        "2026-11-14 10:15:23 ERROR [orders-api] Connection pool exhausted\n"
        "2026-11-14 10:15:24 WARN  [orders-api] Request timeout after 30000ms\n"
        "2026-11-14 10:15:25 ERROR [orders-api] POST /orders returned HTTP 500\n"
        "2026-11-14 10:15:27 ERROR [database] Maximum connection limit reached\n"
    )
    snippets = extract_log_evidence_snippets(raw_logs, max_snippets=4)

    assert len(snippets) == 4
    # Line 2 is the first error line
    assert snippets[0]["line_number"] == 2
    assert "Failed to acquire database connection" in snippets[0]["log_text"]
    assert snippets[0]["signal_matched"] in ("acquisition", "connection", "database", "error")

    # Line 3 is pool exhausted
    assert snippets[1]["line_number"] == 3
    assert "Connection pool exhausted" in snippets[1]["log_text"]

    # Line 4 is timeout
    assert snippets[2]["line_number"] == 4
    assert "Request timeout after 30000ms" in snippets[2]["log_text"]

    # Line 5 is HTTP 500
    assert snippets[3]["line_number"] == 5
    assert "HTTP 500" in snippets[3]["log_text"]


def test_extract_log_evidence_snippets_secret_redaction():
    raw_logs = (
        "2026-11-14 10:15:22 ERROR [orders-api] Connection pool exhausted api_key: sk-1234567890abcdef\n"
        "2026-11-14 10:15:23 ERROR [orders-api] Authorization failed: Bearer secret-token-abcdef123456\n"
    )
    snippets = extract_log_evidence_snippets(raw_logs)

    for snippet in snippets:
        assert "sk-1234567890abcdef" not in snippet["log_text"]
        assert "secret-token-abcdef123456" not in snippet["log_text"]
        assert "[REDACTED_SECRET]" in snippet["log_text"]


def test_extract_log_evidence_snippets_empty_and_malformed():
    assert extract_log_evidence_snippets("") == []
    assert extract_log_evidence_snippets(None) == []
    assert extract_log_evidence_snippets("   \n\n   ") == []
    # Log with no diagnostic error signals
    assert extract_log_evidence_snippets("2026-11-14 10:15:20 INFO Service healthy and ready") == []


def test_extract_log_evidence_snippets_max_limit():
    many_errors = "\n".join([f"2026-11-14 10:15:{i:02d} ERROR [orders-api] timeout failure {i}" for i in range(20)])
    snippets = extract_log_evidence_snippets(many_errors, max_snippets=3)
    assert len(snippets) == 3
