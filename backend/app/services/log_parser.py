import re

SECRET_PATTERNS = [
    r"(?i)(?:api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key|client[_-]?secret)[:=\s]+['\"]?[A-Za-z0-9_\-]{8,}['\"]?",
    r"(?i)sk-[A-Za-z0-9_\-]{10,}",
    r"(?i)Bearer\s+[A-Za-z0-9._\-]+",
    r"(?i)(?:aws|access|secret)_key_id[:=\s]+['\"]?[A-Za-z0-9/+=]{8,}['\"]?",
    r"(?i)password[:=\s]+['\"]?[^\s'\"<>&]{4,}['\"]?",
    r"(?i)(?:postgres|mysql|mongodb|redis):\/\/[^\s]+:[^\s]+@[^\s]+",
]


def sanitize_logs(raw_logs: str, max_chars: int = 40000) -> str:
    """
    Sanitize log text by redacting credentials, tokens, connection strings,
    and secrets while preserving operational diagnostic evidence.
    """
    if not raw_logs:
        return ""

    sanitized = raw_logs[:max_chars]

    for pattern in SECRET_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED_SECRET]", sanitized)

    return sanitized.strip()


def extract_signal_terms(raw_text: str) -> list[str]:
    """
    Extract high-signal diagnostic indicators from incident text or logs.
    """
    text = (raw_text or "").lower()
    tokens = set(re.findall(r"[a-z0-9_\-]+", text))

    prioritized = [
        "timeout",
        "timed out",
        "database",
        "redis",
        "pool",
        "memory",
        "connection",
        "latency",
        "deadlock",
        "error",
        "500",
        "502",
        "503",
        "504",
        "cpu",
        "oom",
        "out of memory",
        "deployment",
        "cache",
        "queue",
        "kafka",
        "api",
        "worker",
        "health",
        "acquisition",
        "exhaustion",
        "leak",
        "rollback",
    ]

    matched = []
    for candidate in prioritized:
        if " " in candidate:
            if candidate in text:
                matched.append(candidate.replace(" ", "_"))
        else:
            if candidate in tokens or ("timeout" in candidate and ("timeout" in tokens or "timed" in tokens)):
                matched.append(candidate)
    return matched
