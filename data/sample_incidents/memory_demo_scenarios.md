# OpsRecall AI Demo Scenarios: Retain → Recall Verification

This document walks through the dual-incident demonstration illustrating how persistent Hindsight memory changes the agent's diagnosis across separate interactions.

---

## Scenario A: Initial Incident (Cold Memory)

- **Service:** `orders-api`
- **Environment:** `staging`
- **Title:** `Orders API returns HTTP 500 after deployment`
- **Context:** `Release 1.4.2 (scaled worker threads)`
- **Logs:** See `database_pool_exhaustion.log`

### Initial Agent Diagnosis (No memory matched yet)
- **Summary:** Database connection acquisition timeouts observed.
- **Hypotheses:** Connection pool exhaustion or slow database queries.
- **Related Memory:** None (`No relevant past incidents found in the memory bank yet`).

### Engineer Verification & Resolution (Retained to Hindsight)
- **Confirmed Root Cause:** Connection pool ceiling was set to 10, which was too low for the 16 new worker threads.
- **Verified Resolution:** Raised `pool_size` from 10 to 40 in configuration and redeployed.
- **Retained Content in Hindsight:**
  ```text
  Incident ID: INC-001
  Service: orders-api
  Environment: staging
  Symptoms: Requests returned HTTP 500 after a deployment.
  Observed evidence: Logs showed database connection acquisition timeouts.
  Confirmed root cause: Connection pool limit was too low for the new worker count.
  Verified resolution: Raised pool_size to 40 in config and restarted service.
  Outcome: resolved
  Verification: confirmed by engineer
  ```

---

## Scenario B: Later Related Incident (Warm Memory)

- **Service:** `checkout-api`
- **Environment:** `production`
- **Title:** `Checkout API timing out after scaling workers`
- **Context:** `Scaled worker pool from 4 to 16 workers`
- **Logs:** See `api_timeout.log`

### Agent Diagnosis (Hindsight Memory Active!)
- **Related Past Incident Recalled:**
  - `[INC-001]` Confirmed Fix: *Connection pool limit was too low for the new worker count. Raised pool_size to 40 in config.*
- **Context-Aware Diagnosis:**
  - The AI agent correlates the current worker scale event with the historical incident from `orders-api`.
  - Recommends inspecting the database connection pool limit vs worker concurrency before restarting or investigating external network issues.
- **Visible Difference:**
  The engineer immediately sees the historical lesson in the "Related Past Incidents" card, avoiding repeated root-cause triage.
