import json
import pytest
from fastapi import HTTPException

from app.database import init_db, get_connection
from app.routes.memory import list_memories, get_memory


@pytest.fixture
def seeded_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_memory_explorer.db"
    monkeypatch.setattr("app.database.DATABASE_PATH", test_db)
    init_db()

    with get_connection() as conn:
        # Incident 1 (Parent of Memory 1)
        conn.execute(
            """
            INSERT INTO incidents (
                id, title, service, environment, severity, description, logs, sanitized_logs,
                status, created_at, updated_at, analysis_json, resolution_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "INC-TEST-001",
                "Orders API Database Exhaustion",
                "orders-api",
                "production",
                "critical",
                "Database pool exhausted during traffic spike",
                "ERROR connection pool exhausted db_password=my_unmasked_secret_key_999",
                "ERROR connection pool exhausted db_password=[REDACTED]",
                "resolved",
                "2026-11-14T08:00:00Z",
                "2026-11-14T08:15:00Z",
                json.dumps({"related_memory_insights": []}),
                json.dumps({
                    "root_cause": "Pool limit too low for traffic",
                    "resolution": "Increased pool ceiling to 40",
                    "outcome": "resolved",
                    "verified": True,
                    "engineer": "SRE Alex",
                    "resolved_at": "2026-11-14T08:15:00Z",
                }),
                json.dumps({}),
            ),
        )

        # Incident 2 (Parent of Memory 2)
        conn.execute(
            """
            INSERT INTO incidents (
                id, title, service, environment, severity, description, logs, sanitized_logs,
                status, created_at, updated_at, analysis_json, resolution_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "INC-TEST-002",
                "Checkout Service Latency Spike",
                "checkout-service",
                "staging",
                "medium",
                "High latency on payment checkout gateway",
                "WARN gateway timeout after 5000ms",
                "WARN gateway timeout after 5000ms",
                "resolved",
                "2026-11-14T09:00:00Z",
                "2026-11-14T09:20:00Z",
                # Note: Cites INC-TEST-001 TWICE to test de-duplication!
                json.dumps({
                    "related_memory_insights": [
                        {"incident_id": "INC-TEST-001", "lesson": "Pool ceiling check"},
                        {"incident_id": "INC-TEST-001", "lesson": "Duplicate citation check"},
                    ]
                }),
                json.dumps({
                    "root_cause": "Upstream partner rate limiting",
                    "resolution": "Enabled circuit breaker and backoff",
                    "outcome": "resolved",
                    "verified": True,
                    "engineer": "SRE Jordan",
                    "resolved_at": "2026-11-14T09:20:00Z",
                }),
                json.dumps({}),
            ),
        )

        # Memory 1 (Verified, Parent exists)
        conn.execute(
            """
            INSERT INTO memories (bank_id, incident_id, service, content, context, outcome, verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                "opsrecall-incidents",
                "INC-TEST-001",
                "orders-api",
                (
                    "Incident ID: INC-TEST-001\n"
                    "Service: orders-api\n"
                    "Environment: production\n"
                    "Symptoms: Database pool exhausted during traffic spike\n"
                    "Confirmed root cause: Pool limit too low for traffic\n"
                    "Verified resolution: Increased pool ceiling to 40\n"
                    "Outcome: resolved\n"
                    "Verification: confirmed by engineer SRE Alex\n"
                    "Timestamp: 2026-11-14T08:15:00Z"
                ),
                "OpsRecall resolution INC-TEST-001",
                "resolved",
                "2026-11-14 08:15:00",
            ),
        )

        # Memory 2 (Verified, Parent exists)
        conn.execute(
            """
            INSERT INTO memories (bank_id, incident_id, service, content, context, outcome, verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                "opsrecall-incidents",
                "INC-TEST-002",
                "checkout-service",
                (
                    "Incident ID: INC-TEST-002\n"
                    "Service: checkout-service\n"
                    "Environment: staging\n"
                    "Symptoms: High latency on payment checkout gateway\n"
                    "Confirmed root cause: Upstream partner rate limiting\n"
                    "Verified resolution: Enabled circuit breaker and backoff\n"
                    "Outcome: resolved\n"
                    "Verification: confirmed by engineer SRE Jordan\n"
                    "Timestamp: 2026-11-14T09:20:00Z"
                ),
                "OpsRecall resolution INC-TEST-002",
                "resolved",
                "2026-11-14 09:20:00",
            ),
        )

        # Memory 3 (Unverified memory to test verification separation)
        conn.execute(
            """
            INSERT INTO memories (bank_id, incident_id, service, content, context, outcome, verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                "opsrecall-incidents",
                "INC-UNVERIFIED-999",
                "auth-service",
                (
                    "Incident ID: INC-UNVERIFIED-999\n"
                    "Service: auth-service\n"
                    "Environment: staging\n"
                    "Symptoms: Intermittent token failure\n"
                    "Confirmed root cause: Speculative hypothesis\n"
                    "Verified resolution: Restarted pod\n"
                    "Outcome: mitigated\n"
                    "Verification: unverified\n"
                    "Timestamp: 2026-11-14T10:00:00Z"
                ),
                "OpsRecall resolution INC-UNVERIFIED-999",
                "mitigated",
                "2026-11-14 10:00:00",
            ),
        )

        # Memory 4 (Orphaned / Missing Parent Incident)
        conn.execute(
            """
            INSERT INTO memories (bank_id, incident_id, service, content, context, outcome, verified, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (
                "opsrecall-incidents",
                "INC-ORPHAN-404",
                "inventory-service",
                (
                    "Incident ID: INC-ORPHAN-404\n"
                    "Service: inventory-service\n"
                    "Environment: staging\n"
                    "Symptoms: Redis cache miss cascade\n"
                    "Confirmed root cause: Cache TTL expired simultaneously\n"
                    "Verified resolution: Added jitter to cache TTLs\n"
                    "Outcome: resolved\n"
                    "Verification: confirmed by engineer SRE Morgan\n"
                    "Timestamp: 2026-11-14T11:00:00Z"
                ),
                "OpsRecall resolution INC-ORPHAN-404",
                "resolved",
                "2026-11-14 11:00:00",
            ),
        )


def test_list_memories_default_verified_only(seeded_db):
    # Default verified=True should exclude unverified memory #3
    data = list_memories(verified=True)
    assert data["verified_only"] is True
    assert data["total"] == 3  # Memory 1, 2, and 4 (orphan is verified)
    ids = [item["incident_id"] for item in data["items"]]
    assert "INC-UNVERIFIED-999" not in ids
    assert "INC-TEST-001" in ids
    assert "INC-TEST-002" in ids
    assert "INC-ORPHAN-404" in ids


def test_list_memories_unverified_separation(seeded_db):
    # verified=False should return ONLY unverified memory
    data_unv = list_memories(verified=False)
    assert data_unv["total"] == 1
    assert data_unv["items"][0]["incident_id"] == "INC-UNVERIFIED-999"
    assert data_unv["items"][0]["verified"] is False


def test_memory_pagination(seeded_db):
    # Page 1 with page_size=2
    d1 = list_memories(page=1, page_size=2)
    assert len(d1["items"]) == 2
    assert d1["page"] == 1
    assert d1["page_size"] == 2
    assert d1["total_pages"] == 2

    # Page 2 with page_size=2
    d2 = list_memories(page=2, page_size=2)
    assert len(d2["items"]) == 1
    assert d2["page"] == 2

    # Items on page 1 and page 2 must be distinct
    p1_ids = {item["id"] for item in d1["items"]}
    p2_ids = {item["id"] for item in d2["items"]}
    assert p1_ids.isdisjoint(p2_ids)


def test_memory_searching(seeded_db):
    # Search by root cause keyword
    data = list_memories(search="circuit breaker")
    assert data["total"] == 1
    assert data["items"][0]["incident_id"] == "INC-TEST-002"

    # Search by service
    data_svc = list_memories(search="orders-api")
    assert data_svc["total"] == 1
    assert data_svc["items"][0]["service"] == "orders-api"


def test_memory_filtering_by_service_and_severity(seeded_db):
    # Filter by service
    data_svc = list_memories(service="orders-api")
    assert all(item["service"] == "orders-api" for item in data_svc["items"])

    # Filter by severity
    data_sev = list_memories(severity="critical")
    assert data_sev["total"] == 1
    assert data_sev["items"][0]["severity"] == "critical"


def test_memory_detail_and_secret_sanitization(seeded_db):
    # Detail retrieval by integer ID
    detail = get_memory("1")
    assert detail["id"] == 1
    assert detail["incident_id"] == "INC-TEST-001"
    assert detail["root_cause"] == "Pool limit too low for traffic"
    assert detail["storage_provider"] == "Local SQLite Fallback"
    assert detail["bank_id"] == "opsrecall-incidents"
    assert detail["verified"] is True
    assert detail["engineer"] == "SRE Alex"

    # Secret check: evidence logs must NOT contain secret
    assert "my_unmasked_secret_key_999" not in detail["evidence_logs"]
    assert "[REDACTED_SECRET]" in detail["evidence_logs"]


def test_missing_parent_incident_handling(seeded_db):
    # Memory 4 (INC-ORPHAN-404) has no row in incidents table
    data = list_memories(search="inventory-service")
    assert data["total"] == 1
    orphan = data["items"][0]
    assert orphan["has_parent_incident"] is False
    assert orphan["service"] == "inventory-service"
    assert orphan["root_cause"] == "Cache TTL expired simultaneously"
    assert orphan["resolution"] == "Added jitter to cache TTLs"

    # Detail check for orphan
    det = get_memory(str(orphan["id"]))
    assert det["has_parent_incident"] is False
    assert det["symptoms"] == "Redis cache miss cascade"
    assert det["engineer"] == "SRE Morgan"


def test_recall_citation_deduplication(seeded_db):
    # Incident 2 cited INC-TEST-001 twice in related_memory_insights.
    # The recall_count must be exactly 1 (not 2).
    detail = get_memory("1")
    assert detail["recall_count"] == 1
    assert len(detail["recalled_in_incidents"]) == 1
    assert detail["recalled_in_incidents"][0]["id"] == "INC-TEST-002"


def test_get_memory_not_found(seeded_db):
    with pytest.raises(HTTPException) as exc:
        get_memory("99999")
    assert exc.value.status_code == 404
