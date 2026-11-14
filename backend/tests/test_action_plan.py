import json
import pytest
from fastapi import HTTPException

from app.database import get_connection, init_db
from app.routes.incidents import (
    create_incident_action,
    dashboard_summary,
    get_action_plan_summary,
    get_incident,
    get_incident_action,
    get_incident_timeline,
    import_recommended_actions,
    list_incident_actions,
    save_resolution,
    update_incident_action,
)
from app.schemas.action_plan import (
    ActionBatchImportRequest,
    ActionCreate,
    ActionUpdate,
)
from app.schemas.incident import IncidentResolution
from app.services.incident_service import incident_service


@pytest.fixture
def seeded_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_action_plan.db"
    monkeypatch.setattr("app.database.DATABASE_PATH", test_db)
    init_db()

    # Seed an incident with explainable AI analysis including structured checks
    inc_id = "INC-20261114-100000-TEST"
    analysis = {
        "summary": "Database connection pool exhausted due to spike in concurrent checkout requests.",
        "symptoms": ["504 Gateway Timeout", "pool exhausted"],
        "possible_causes": [
            {"cause": "Connection pool ceiling exceeded", "evidence": ["504 Gateway Timeout"], "confidence": "high"}
        ],
        "confidence": "high",
        "safety_notes": ["Verify connection limits before restarting."],
        "recommended_checks": [
            "Inspect downstream circuit breaker status",
            "Verify database lock contention",
            "Scale downstream connection pool",
        ],
        "structured_checks": [
            {
                "check": "Inspect downstream circuit breaker status",
                "check_type": "read_only",
                "command_hint": "curl -s http://payments-api:8080/internal/circuit-breaker",
            },
            {
                "check": "Verify database lock contention",
                "check_type": "active_validation",
                "command_hint": "SELECT * FROM pg_stat_activity WHERE wait_event IS NOT NULL",
            },
            {
                "check": "Scale downstream connection pool",
                "check_type": "mitigation",
                "command_hint": "kubectl scale deployment payments-api --replicas=4",
            },
        ],
    }

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO incidents (
                id, title, service, environment, severity, description, logs, sanitized_logs,
                status, created_at, updated_at, analysis_json, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inc_id,
                "Payment Gateway 504 Timeout Spike",
                "payments-api",
                "production",
                "critical",
                "High latency and 504 gateway timeouts observed during checkout traffic spike.",
                "2026-11-14T10:00:00Z ERROR payments-api: 504 Gateway Timeout downstream provider unreachable",
                "2026-11-14T10:00:00Z ERROR payments-api: 504 Gateway Timeout downstream provider unreachable",
                "analyzed",
                "2026-11-14T10:00:00Z",
                "2026-11-14T10:00:00Z",
                json.dumps(analysis),
                json.dumps({"severity": "critical"}),
            ),
        )

    # Initial timeline events
    incident_service.record_timeline_event(
        incident_id=inc_id,
        event_type="incident_created",
        description="Incident registered for service 'payments-api' in production. Severity: CRITICAL.",
        actor="OpsRecall AI",
        actor_type="ai",
        created_at="2026-11-14T10:00:00Z",
    )
    incident_service.record_timeline_event(
        incident_id=inc_id,
        event_type="analysis_completed",
        description=f"AI diagnostic investigation completed. Summary: {analysis['summary']}",
        actor="OpsRecall AI",
        actor_type="ai",
        created_at="2026-11-14T10:00:00Z",
    )

    return inc_id


def test_action_creation_and_retrieval(seeded_db):
    incident_id = seeded_db

    # Create manual action
    create_payload = ActionCreate(
        title="Inspect downstream circuit breaker status",
        description="Check if circuit breaker has tripped for payment provider.",
        category="read_only",
        priority="high",
        assigned_engineer="Alice",
        command_hint="curl -s http://payments-api:8080/internal/circuit-breaker",
    )
    action = create_incident_action(incident_id, create_payload)
    assert action["incident_id"] == incident_id
    assert action["title"] == create_payload.title
    assert action["status"] == "pending"
    assert action["category"] == "read_only"
    assert action["priority"] == "high"
    assert action["assigned_engineer"] == "Alice"
    action_id = action["id"]

    # Retrieve single action
    fetched = get_incident_action(incident_id, action_id)
    assert fetched["id"] == action_id
    assert fetched["title"] == create_payload.title

    # List actions
    actions = list_incident_actions(incident_id)
    assert len(actions) == 1
    assert actions[0]["id"] == action_id


def test_import_recommendations_to_action_plan(seeded_db):
    incident_id = seeded_db

    # Import AI recommendations into action plan
    imported = import_recommended_actions(incident_id, ActionBatchImportRequest(actor="Bob"))
    assert isinstance(imported, list)
    assert len(imported) == 3

    # Verify each imported action has valid category and status pending
    for action in imported:
        assert action["incident_id"] == incident_id
        assert action["status"] == "pending"
        assert action["category"] in ("read_only", "active_validation", "mitigation")

    # Importing again does not duplicate identical titles
    second_import = import_recommended_actions(incident_id, ActionBatchImportRequest(actor="Bob"))
    assert len(second_import) == 0


def test_action_lifecycle_status_transitions(seeded_db):
    incident_id = seeded_db

    action = create_incident_action(
        incident_id,
        ActionCreate(title="Scale downstream connection pool", category="mitigation", priority="critical"),
    )
    action_id = action["id"]
    assert action["status"] == "pending"

    # Start action (pending -> in_progress)
    patch1 = update_incident_action(
        incident_id,
        action_id,
        ActionUpdate(status="in_progress", actor="Charlie"),
    )
    assert patch1["status"] == "in_progress"

    # Block action (in_progress -> blocked)
    patch2 = update_incident_action(
        incident_id,
        action_id,
        ActionUpdate(status="blocked", blocked_reason="Waiting for DBA approval", actor="Charlie"),
    )
    assert patch2["status"] == "blocked"
    assert patch2["blocked_reason"] == "Waiting for DBA approval"

    # Complete action (blocked -> completed)
    patch3 = update_incident_action(
        incident_id,
        action_id,
        ActionUpdate(
            status="completed",
            completion_notes="DBA pool limit doubled from 50 to 100 connections.",
            actor="Charlie",
        ),
    )
    assert patch3["status"] == "completed"
    assert "doubled" in patch3["completion_notes"]


def test_invalid_status_transition_rejected(seeded_db):
    incident_id = seeded_db
    action = create_incident_action(
        incident_id,
        ActionCreate(title="Test invalid status"),
    )
    action_id = action["id"]

    # Pydantic or service-level rejection
    with pytest.raises(Exception):
        update_incident_action(
            incident_id,
            action_id,
            ActionUpdate.model_validate({"status": "exploded"}),
        )


def test_action_engineer_assignment(seeded_db):
    incident_id = seeded_db
    action = create_incident_action(
        incident_id,
        ActionCreate(title="Verify database lock contention"),
    )
    action_id = action["id"]

    updated = update_incident_action(
        incident_id,
        action_id,
        ActionUpdate(assigned_engineer="Devon"),
    )
    assert updated["assigned_engineer"] == "Devon"


def test_timeline_chronological_ordering_and_provenance(seeded_db):
    incident_id = seeded_db

    act1 = create_incident_action(
        incident_id,
        ActionCreate(title="Check Redis replica lag", assigned_engineer="Evelyn"),
    )

    update_incident_action(
        incident_id,
        act1["id"],
        ActionUpdate(status="in_progress", actor="Evelyn"),
    )

    update_incident_action(
        incident_id,
        act1["id"],
        ActionUpdate(status="completed", completion_notes="Replica lag 0ms.", actor="Evelyn"),
    )

    # Fetch timeline
    timeline = get_incident_timeline(incident_id)
    assert len(timeline) >= 4

    event_types = [e["event_type"] for e in timeline]
    assert "incident_created" in event_types
    assert "analysis_completed" in event_types
    assert "action_created" in event_types
    assert "action_started" in event_types
    assert "action_completed" in event_types

    # Provenance: AI vs Engineer
    ai_events = [e for e in timeline if e["actor_type"] == "ai"]
    eng_events = [e for e in timeline if e["actor_type"] == "engineer"]
    assert len(ai_events) >= 2
    assert len(eng_events) >= 2
    assert all(e["actor"] == "OpsRecall AI" for e in ai_events)
    assert any(e["actor"] == "Evelyn" for e in eng_events)


def test_no_automatic_incident_resolution_when_actions_completed(seeded_db):
    incident_id = seeded_db
    act = create_incident_action(
        incident_id,
        ActionCreate(title="Check pod restart count"),
    )

    # Complete the only action
    update_incident_action(
        incident_id,
        act["id"],
        ActionUpdate(status="completed", completion_notes="Zero restarts"),
    )

    # Verify incident is still NOT resolved
    inc = get_incident(incident_id)
    assert inc["status"] != "resolved"
    assert inc["resolution"] is None

    # Verify action plan summary shows 100% completion
    summary = get_action_plan_summary(incident_id)
    assert summary["total_actions"] == 1
    assert summary["completed_actions"] == 1
    assert summary["progress_pct"] == 100


def test_explicit_resolution_records_timeline_and_preserves_verification_boundary(seeded_db, monkeypatch):
    incident_id = seeded_db

    from app.services.hindsight_service import memory_client
    monkeypatch.setattr(memory_client, "retain", lambda *args, **kwargs: {"status": "stored_locally", "source": "local_memory_bank"})

    # Submit resolution with verification
    res_payload = IncidentResolution(
        root_cause="Misconfigured connection pool ceiling in payments service config map.",
        resolution="Increased pool max to 100 and rolled out v1.4.2.",
        outcome="resolved",
        verified=True,
        engineer="Lead SRE",
    )
    submit_res = save_resolution(incident_id, res_payload)
    assert submit_res["status"] == "resolved"
    assert submit_res["memory_retained"] is True

    # Timeline includes resolution events
    tl = get_incident_timeline(incident_id)
    types = [e["event_type"] for e in tl]
    assert "resolution_submitted" in types
    assert "resolution_verified" in types
    assert "incident_resolved" in types


def test_invalid_incident_and_action_id_handling(seeded_db):
    # 404 for missing incident
    with pytest.raises(HTTPException) as exc1:
        list_incident_actions("INC-NONEXISTENT-9999")
    assert exc1.value.status_code == 404

    with pytest.raises(HTTPException) as exc2:
        create_incident_action("INC-NONEXISTENT-9999", ActionCreate(title="Ghost action"))
    assert exc2.value.status_code == 404

    with pytest.raises(HTTPException) as exc3:
        get_incident_timeline("INC-NONEXISTENT-9999")
    assert exc3.value.status_code == 404

    # 404 for missing action inside existing incident
    with pytest.raises(HTTPException) as exc4:
        get_incident_action(seeded_db, "ACT-GHOST-000")
    assert exc4.value.status_code == 404


def test_dashboard_summary_includes_actions_telemetry(seeded_db):
    incident_id = seeded_db
    create_incident_action(
        incident_id,
        ActionCreate(title="Telemetry test action 1", category="read_only"),
    )

    data = dashboard_summary()
    assert "actions_summary" in data
    acts = data["actions_summary"]
    assert acts["total_actions"] >= 1
    assert "completed_actions" in acts
    assert "blocked_actions" in acts
    assert "pending_actions" in acts
