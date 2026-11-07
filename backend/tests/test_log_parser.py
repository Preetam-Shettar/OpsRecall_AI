from app.services.log_parser import extract_signal_terms, sanitize_logs


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
