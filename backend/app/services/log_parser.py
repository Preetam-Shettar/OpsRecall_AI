import re

SECRET_PATTERNS = [
    r"(?i)(api[_-]?key|token|secret|password)[:=\s]+[A-Za-z0-9_\-]{8,}",
    r"(?i)sk-[A-Za-z0-9]{10,}",
    r"(?i)Bearer\s+[A-Za-z0-9._\-]+",
    r"(?i)(?:aws|access|secret)_key_id[:=\s]+[A-Za-z0-9/+=]{8,}",
    r"(?i)password[:=\s]+['\"]?[A-Za-z0-9!@#$%^&*()_\-+=]{4,}['\"]?",
    r"(?i)token[:=\s]+['\"]?[A-Za-z0-9._\-]{8,}['\"]?",
]


def sanitize_logs(raw_logs: str) -> str:
    sanitized = raw_logs or ""
    for pattern in SECRET_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized)
    sanitized = re.sub(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2})\b", "[TIMESTAMP]", sanitized)
    return sanitized.strip()


def extract_signal_terms(raw_text: str) -> list[str]:
    text = (raw_text or "").lower()
    tokens = set(re.findall(r"[a-z0-9_\-]+", text))
    prioritized = [
        "timeout",
        "database",
        "redis",
        "pool",
        "memory",
        "connection",
        "latency",
        "error",
        "500",
        "cpu",
        "oom",
        "deployment",
        "cache",
        "queue",
        "kafka",
        "api",
        "worker",
        "health",
    ]
    return [token for token in prioritized if token in tokens]
