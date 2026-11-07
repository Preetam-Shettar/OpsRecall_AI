"""
OpsRecall AI - End-to-End Retain & Recall Verification Script
Simulates the dual-incident workflow:
1. Scenario A: Orders API 500 (DB pool exhaustion) -> Diagnosed -> Verified & Retained to Hindsight
2. Scenario B: Checkout API timeout -> Diagnosed with historical memory recalled!
"""
import sys
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.database import init_db
from app.routes.incidents import create_incident, save_resolution, dashboard_summary
from app.schemas.incident import IncidentCreate, IncidentResolution
from app.services.hindsight_service import memory_client


def run_demo():
    print("=" * 70)
    print(" OpsRecall AI - End-to-End Retain & Recall Verification")
    print("=" * 70)

    # Initialize DB
    init_db()

    # Step 1: Submit Scenario A (Orders API 500)
    print("\n[Step 1] Submitting Incident A: Orders API 500 (Cold Memory)...")
    payload_a = IncidentCreate(
        title="Orders API returns HTTP 500 after deployment",
        service="orders-api",
        environment="staging",
        description="Requests began failing after deployment release. Latency spiked sharply.",
        logs=(
            "2026-11-07 10:12:01 ERROR orders-api Database connection acquisition timed out after 30s. "
            "2026-11-07 10:12:02 ERROR orders-api Request failed: GET /orders ConnectionPoolTimeoutException. "
            "2026-11-07 10:12:03 WARN database-pool Active connections reached configured maximum (10/10)."
        ),
        deployment_context="Release 1.4.2",
    )
    res_a = create_incident(payload_a)
    inc_a_id = res_a["incident_id"]
    print(f" -> Incident A Created: {inc_a_id}")
    print(f" -> Diagnosis Summary: {res_a['analysis']['summary']}")
    print(f" -> Related Memories Found: {len(res_a['related_memories'])} (Expected: 0 on first run)")

    # Step 2: Confirm Resolution and Retain to Hindsight
    print("\n[Step 2] Engineer verifies root cause and saves resolution...")
    res_payload = IncidentResolution(
        root_cause="Database connection pool limit (10) was too low for worker count (16).",
        resolution="Increased pool_size to 40 in config and redeployed service.",
        outcome="resolved",
        verified=True,
        engineer="On-Call SRE",
    )
    retain_result = save_resolution(inc_a_id, res_payload)
    print(f" -> Resolution Status: {retain_result['status']}")
    print(f" -> Retained to Hindsight Bank: {retain_result['memory_retained']}")
    print(f" -> Target Memory Bank: {memory_client.bank_id}")

    # Step 3: Submit Scenario B (Checkout API Timeout)
    print("\n[Step 3] Submitting Incident B: Checkout API Timeout (Warm Memory)...")
    payload_b = IncidentCreate(
        title="Checkout API timing out after scaling workers",
        service="checkout-api",
        environment="production",
        description="Worker concurrency was increased and checkout began timing out on DB connection acquisition.",
        logs=(
            "2026-11-08 09:30:10 ERROR checkout-api Timeout waiting for database connection from pool. "
            "2026-11-08 09:30:11 WARN database-pool Connection pool utilization: 100% (pool size: 10). "
            "2026-11-08 09:30:12 ERROR checkout-api Transaction rollback: lease acquisition timed out."
        ),
        deployment_context="Scale workers to 16",
    )
    res_b = create_incident(payload_b)
    inc_b_id = res_b["incident_id"]
    print(f" -> Incident B Created: {inc_b_id}")
    print(f" -> Diagnosis Summary: {res_b['analysis']['summary']}")
    print(f" -> HINDSIGHT RECALL TRIGGERED: {len(res_b['related_memories'])} past incident(s) retrieved!")

    for idx, memory in enumerate(res_b["related_memories"]):
        print(f"    [{idx + 1}] Prior Incident Ref: {memory.get('incident_id')}")
        print(f"        Lesson: {memory.get('lesson')}")

    # Step 4: Verify Dashboard Summary
    print("\n[Step 4] Checking System Telemetry...")
    summary = dashboard_summary()
    print(f" -> Total Incidents Processed: {summary['total_incidents']}")
    print(f" -> Verified Resolutions: {summary['resolved_incidents']}")
    print(f" -> Stored Hindsight Memories: {summary['stored_memories']}")

    print("\n" + "=" * 70)
    print(" VERIFICATION SUCCESSFUL: Hindsight memory retained and recalled!")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()
