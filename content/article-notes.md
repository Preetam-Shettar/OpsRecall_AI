# OpsRecall AI: Article & Technical Deep Dive Notes

## 1. Problem Statement & Motivation
In modern cloud operations and SRE on-call rotations, the biggest source of downtime and engineering burnout is **session amnesia**. When a critical production incident occurs—such as database pool exhaustion, cascading API gateway timeouts, or cache eviction storms—engineers often scramble to diagnose symptoms from scratch. Even if an identical or related incident was solved two weeks ago by a peer engineer, that context is buried inside stale Slack channels, fragmented post-mortems, or Jira tickets.

Current LLM-powered incident response tools typically suffer from two major flaws:
1. **Stateless Analysis**: Each triage session starts with a blank slate, offering generic advice like *"check your database logs and restart services"* without knowing historical infrastructure topology or previous proven fixes.
2. **Hallucinated Memory**: Without strict verification gates, AI assistants ingest unverified guesses or noisy intermediate hypotheses into vector stores, poisoning future triage runs with bad recommendations.

**OpsRecall AI** was built to solve this by pairing Groq-accelerated LLM log diagnostics with a **persistent, engineer-verified learning loop** powered by Hindsight memory banks.

---

## 2. Technical Architecture & Design Decisions

### System Architecture
OpsRecall AI operates as a decoupled micro-architecture:
- **Frontend**: React 19 + Vite + Tailwind CSS SPA providing real-time telemetry, interactive triage flows, memory correlation indicators, and theme controls.
- **Backend**: FastAPI (Python 3.12/3.14) providing structured log ingestion, regex sanitization, LLM coordination, and memory orchestration.
- **Memory Engine (Hindsight)**: Dual-layer persistence engine communicating with Hindsight Cloud (`opsrecall-incidents` bank) via REST, with an automatic, resilient SQLite fallback for offline or zero-network operations.
- **Inference Engine**: Groq Cloud running `llama-3.3-70b-versatile` for sub-second log parsing and structured JSON incident diagnosis.

```
┌─────────────────────────────────────────────────────────────┐
│                 React 19 + Vite Frontend                    │
│   (Dashboard, Triage Wizard, Memory Explorer, Theme Engine) │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON REST API
┌──────────────────────────────▼──────────────────────────────┐
│                     FastAPI Backend                         │
│  ┌───────────────────────┐      ┌────────────────────────┐  │
│  │ Log Sanitizer Engine  │ ───► │ Incident Orchestrator  │  │
│  │ (Redacts keys/tokens) │      └───────────┬────────────┘  │
│  └───────────────────────┘                  │               │
│                                             ▼               │
│                        ┌──────────────────────────────────┐ │
│                        │ Hindsight Dual-Persistence Engine│ │
│                        │ - retain (verified gate)         │ │
│                        │ - recall (vector context)        │ │
│                        │ - reflect (pattern synthesis)    │ │
│                        └────────────┬──────────────┬──────┘ │
└─────────────────────────────────────┼──────────────┼────────┘
                                      │              │
                    (HTTP REST)       ▼              ▼ (Local Resilient)
                       ┌───────────────────┐    ┌───────────────────┐
                       │  Hindsight Cloud  │    │  Local SQLite DB  │
                       │ opsrecall-incidents│   │   (memories table)│
                       └───────────────────┘    └───────────────────┘
```

### Key Technical Decisions
1. **Gate Memory Retain to Verified Resolutions**: Memory is only retained when `resolution["verified"] is True`. Experimental or unverified engineer comments are never promoted to the memory bank.
2. **Log Sanitization First**: Raw logs pass through a regex sanitization pipeline before reaching Groq or Hindsight, stripping bearer tokens, AWS/API keys, database URLs, and passwords.
3. **Graceful Fallback Mode**: The backend automatically detects Hindsight Cloud reachability. If offline or unconfigured, it persists memories to SQLite with transparent UI indicators (`[Local Memory Fallback]`), never falsely reporting cloud sync.

---

## 3. Actual Hindsight Integration

The integration resides in `backend/app/services/hindsight_service.py` under the bank ID `opsrecall-incidents`:

- **`retain(service, outcome, incident_id, verified)`**:
  - Compiles the engineer-confirmed resolution, root cause, and signal terms into a structured memory document.
  - Sends an authenticated POST request to `/v1/banks/{bank_id}/memories`.
  - Fallback writes to the local `memories` table with a generated UUID.
- **`recall(query, service=None, limit=3)`**:
  - Searches past incidents by symptom similarity or service scope.
  - Returns matching historical records with confidence scores, past root causes, and verified fixes.
  - Injects these memories directly into the prompt context for the LLM analysis.
- **`reflect(topic, service=None)`**:
  - Synthesizes recurring failure patterns and architectural vulnerabilities across all retained incidents.
  - Cloud endpoint: `/v1/banks/{bank_id}/reflect`.
  - Fallback endpoint: Aggregates local memories and formats systemic recommendations with an explicit `[Local Memory Fallback]` prefix.

---

## 4. Real Challenges Encountered & Solutions

1. **Python 3.14 Starlette `TestClient` Deadlock**:
   - *Problem*: In Python 3.14 on Windows, Starlette's `TestClient` running via `anyio` deadlocked during test execution when managing background portal threads.
   - *Solution*: Re-architected backend unit and integration tests to invoke FastAPI router handlers and service layers directly as asynchronous coroutines, reducing test execution time to under 0.6 seconds without external network dependencies.
2. **SQLite Column Schema Evolution**:
   - *Problem*: Standard `CREATE TABLE IF NOT EXISTS` did not add new memory metadata columns (`bank_id`, `incident_id`, `service`, `outcome`, `verified`) to pre-existing SQLite database files on disk.
   - *Solution*: Implemented an automatic PRAGMA table inspection and migration routine in `database.py` that executes `ALTER TABLE memories ADD COLUMN` on startup.
3. **Accidental False-Positive Log Redaction**:
   - *Problem*: Naive regexes stripped valid service port numbers or status codes.
   - *Solution*: Crafted targeted regex patterns targeting known secret prefixes (`sk-`, `ey...`, `postgres://`, `Authorization: Bearer`).

---

## 5. Real Verification & Test Results

- **Backend Pytest Suite**: 11 passed in 0.58s
  - `test_health.py`: Health check and system status.
  - `test_log_parser.py`: Secret redaction, log signal extraction.
  - `test_incidents.py`: Log parsing, incident creation, incident retrieval, analysis generation, resolution verification gate (confirms unverified resolutions are NOT retained).
  - `test_hindsight.py`: Retain execution, recall search, reflect aggregation.
- **Frontend Build**: Vite v6.4.1 Production Build
  - 33 modules transformed in 248ms.
  - Zero syntax errors, zero TypeScript/JSX compilation warnings.
  - Production bundles: `dist/index.html` (0.50 kB), `dist/assets/index-*.js` (230 kB), `dist/assets/index-*.css` (20 kB).
- **End-to-End Demo Script (`scripts/verify_demo.py`)**:
  - Scenario A (Database Pool Exhaustion) $\rightarrow$ Analyzed $\rightarrow$ Verified Resolution Saved $\rightarrow$ Retained to Memory.
  - Scenario B (API Timeout Incident) $\rightarrow$ Recalled Scenario A memory with matching signal terms (`database`, `pool`, `timeout`) $\rightarrow$ Generated accelerated diagnosis citing the prior fix.

---

## 6. Limitations & Lessons Learned

- **Current Limitations**:
  - Live Hindsight Cloud requires valid account credentials; offline developers default to local SQLite fallback.
  - Real-time log streaming from Kubernetes pods or CloudWatch is not yet wired to a live webhook receiver (currently relies on structured JSON paste/upload).
- **Key Lessons**:
  - Strictly gating AI persistent memory behind human verification is mandatory for mission-critical DevOps domains.
  - Having a dual-mode persistence architecture (cloud with zero-config local fallback) makes local development and hackathon evaluations 100% reliable.

---

## 7. Media & Snippets Checklist for Final Submission
- [x] Dashboard high-resolution screenshot (`screenshots/dashboard.png`)
- [ ] End-to-end 3-minute product demo video recording
- [ ] Code snippet highlighting the verification gate in `backend/app/services/incident_service.py`
- [ ] Code snippet demonstrating Hindsight `recall` injection in `backend/app/services/analysis_service.py`
