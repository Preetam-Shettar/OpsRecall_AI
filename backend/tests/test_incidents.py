from app.routes.incidents import create_incident, list_incidents, get_incident, save_resolution, dashboard_summary
from app.schemas.incident import IncidentCreate, IncidentResolution


def test_incident_lifecycle(tmp_path, monkeypatch):
    test_db = tmp_path / "test_lifecycle.db"
    monkeypatch.setattr("app.database.DATABASE_PATH", test_db)
    from app.database import init_db
    init_db()

    # 1. Create Incident A (Scenario A: Database pool exhaustion)
    create_payload = IncidentCreate(
        title="Orders API returning 500 errors",
        service="orders-api",
        environment="staging",
        description="Requests began failing after the latest deployment.",
        logs="Database connection acquisition timed out after 30 seconds. Active connections reached maximum pool limit.",
        deployment_context="Release 1.4.2",
    )
    result = create_incident(create_payload)
    incident_id = result["incident_id"]

    assert incident_id.startswith("INC-")
    assert result["status"] == "analyzed"
    assert result["analysis"]["summary"]
    assert len(result["recommendations"]) > 0

    # 2. Get incident by ID
    fetched = get_incident(incident_id)
    assert fetched["id"] == incident_id
    assert fetched["service"] == "orders-api"

    # 3. Save Verified Resolution -> Retains into Hindsight memory
    res_payload = IncidentResolution(
        root_cause="Database connection pool limit too low for worker count",
        resolution="Increased pool_size from 10 to 40 in config and redeployed",
        outcome="resolved",
        verified=True,
        engineer="Punit",
    )
    res_result = save_resolution(incident_id, res_payload)
    assert res_result["status"] == "resolved"
    assert res_result["memory_retained"] is True

    # 4. Check dashboard summary
    summary = dashboard_summary()
    assert summary["total_incidents"] >= 1
    assert summary["resolved_incidents"] >= 1
    assert summary["stored_memories"] >= 1

    # 5. Create Incident B (Scenario B: Checkout API connection timeout)
    # Memory should be recalled and included in analysis!
    create_payload_b = IncidentCreate(
        title="Checkout API timeout after scaling workers",
        service="checkout-api",
        environment="production",
        description="Worker concurrency increased and checkout began timing out on database queries.",
        logs="2026-11-08 09:30:10 ERROR checkout-api Timeout waiting for database connection pool.",
        deployment_context="Scale workers to 20",
    )
    result_b = create_incident(create_payload_b)
    assert result_b["incident_id"]
    # Check that related memories were recalled!
    assert len(result_b["related_memories"]) > 0
    assert any("INC-" in mem["incident_id"] for mem in result_b["related_memories"])

    # 6. Verify that an unverified resolution does NOT retain memory
    unverified_res = IncidentResolution(
        root_cause="Speculative unconfirmed hypothesis",
        resolution="Restarted service without verification",
        outcome="mitigated",
        verified=False,
    )
    unverified_result = save_resolution(result_b["incident_id"], unverified_res)
    assert unverified_result["memory_retained"] is False
    assert unverified_result["memory_details"] is None
