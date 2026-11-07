#  --- Overall Implementation Plan

> **Project status:** Proposed implementation blueprint. This document
> describes what we intend to build; it does not claim that any
> component is already implemented or tested.
>
> **Project category:** AI agent for engineering operations / incident
> response\
> **Core requirement:** Hindsight must provide persistent memory that
> changes how the agent handles later incidents.

------------------------------------------------------------------------

## 1. Project Overview

### 1.1 Project name

**OpsRecall AI**

### 1.2 One-line description

OpsRecall AI is an AI-powered incident response assistant that analyzes
software error logs, suggests likely causes and investigation steps, and
uses Hindsight memory to recall previous incidents and their verified
resolutions.

### 1.3 Problem statement

When an application fails, engineers often need to: - inspect logs and
error traces; - identify when and where the failure began; - search old
tickets, chat messages, notes, or post-mortems; - remember which fixes
worked for similar incidents; and - document the final resolution for
future use.

A generic chatbot may analyze the current log, but it may not remember
how the same engineering team handled a similar failure last week. This
makes engineers repeat investigation work.

### 1.4 Proposed solution

OpsRecall AI provides one workflow for submitting an incident, analyzing
its evidence, recalling related historical incidents, and recording the
confirmed outcome.

The key differentiator is **persistent incident memory powered by
Hindsight**. The agent should become more context-aware as useful
incident history accumulates.

### 1.5 Target users

-   Software developers
-   Site reliability engineers (SREs)
-   DevOps engineers
-   Small engineering teams
-   Technical support and operations teams

### 1.6 Scope for the first version

Build one polished workflow exceptionally well:

1.  Submit an incident title, description, and logs.
2.  Analyze the current evidence.
3.  Recall relevant previous incidents from Hindsight.
4.  Generate a diagnosis with evidence, confidence, and next steps.
5.  Let the engineer record whether the suggestion helped.
6.  Record the verified root cause and resolution in Hindsight.
7.  Show how a later similar incident benefits from the accumulated
    memory.

**Out of scope for the first version:** connecting to production
infrastructure, automatically restarting services, executing shell
commands, monitoring live systems, integrating every observability
platform, and claiming definitive root causes from incomplete logs.

------------------------------------------------------------------------

## 2. Hackathon Alignment

The supplied problem statement requires projects to use Hindsight and
demonstrate persistent memory and learning from past interactions. It
also asks teams to use Band AI desktop and submit a documented GitHub
repository, demo video, live project demo, and an explanation of
Hindsight usage.

OpsRecall AI addresses the theme through: - **Retain:** store incident
context and verified outcomes. - **Recall:** retrieve relevant
historical incidents for a new incident. - **Reflect:** synthesize
lessons from stored incident history where useful. - **Visible
learning:** demonstrate a first incident and a later similar incident,
showing how memory changes the investigation.

### Judging criteria from the supplied problem statement

  ------------------------------------------------------------------------
  Criterion                                   Weight What our demo should
                                                     make visible
  --------------------- ---------------------------- ---------------------
  Innovation                                     30% A focused
                                                     incident-response
                                                     workflow, not just a
                                                     generic chatbot

  Hindsight memory                               25% Real retain/recall
                                                     usage and a visible
                                                     improvement across
                                                     incidents

  Technical                                      20% Working frontend,
  implementation                                     backend,
                                                     integrations, error
                                                     handling, and clear
                                                     structure

  User experience                                15% Simple incident
                                                     submission and
                                                     understandable
                                                     recommendations

  Real-world impact                              10% Less repeated
                                                     investigation and
                                                     better reuse of
                                                     engineering knowledge
  ------------------------------------------------------------------------

------------------------------------------------------------------------

## 3. Technology Stack

Use a stack that is quick to develop, easy to explain, and realistic for
a working prototype.

  -----------------------------------------------------------------------
  Layer                   Technology              Responsibility
  ----------------------- ----------------------- -----------------------
  Frontend                React + Vite            Web application and
                                                  dashboard

  Styling                 Tailwind CSS            Responsive interface
                                                  and reusable UI styling

  Charts                  Recharts (optional)     Incident trends and
                                                  status summaries

  Backend                 Python + FastAPI        REST API and
                                                  orchestration

  Validation              Pydantic                Validate requests and
                                                  responses

  LLM                     Groq API with a         Analyze logs and draft
                          supported model         explanations

  Persistent agent memory Hindsight               Retain, recall, and
                                                  reflect on incident
                                                  knowledge

  Application database    SQLite for prototype    Incident records,
                                                  feedback, and basic
                                                  metadata

  HTTP client             httpx or requests       Backend integrations
                                                  where required

  Configuration           python-dotenv           Load environment
                                                  variables locally

  Version control         Git + GitHub            Source control and
                                                  submission repository

  Development assistant   Band AI desktop         Required development
                                                  tool from the problem
                                                  statement

  Optional packaging      Docker                  Reproducible local
                                                  setup if time permits
  -----------------------------------------------------------------------

### Important architecture decision

Hindsight is the agent's memory system. SQLite is only for application
records such as incident IDs, timestamps, status, and feedback. Do not
describe SQLite rows as the Hindsight memory integration.

Do not add PostgreSQL, Redis, Kubernetes, or a vector database unless
the working prototype genuinely needs them. Avoid adding infrastructure
that does not improve the demo.

### LLM selection

The supplied problem statement recommends Groq and names
`openai/gpt-oss-120b` and `qwen/qwen3-32b` as possible models. Confirm
current model availability and tool/function-calling support in the Groq
account before choosing one. Keep the model name configurable through an
environment variable.

The application should still work if the chosen model is unavailable:
return a clear error and preserve the submitted incident rather than
silently inventing an analysis.

------------------------------------------------------------------------

## 4. High-Level Architecture

``` text
┌──────────────────────────────────────────────────────────┐
│                    React Frontend                         │
│                                                          │
│ Dashboard | New Incident | Incident Details | History   │
└──────────────────────────┬───────────────────────────────┘
                           │ HTTPS / JSON
                           ▼
┌──────────────────────────────────────────────────────────┐
│                    FastAPI Backend                        │
│                                                          │
│ API Routes → Validation → Incident Service → Agent       │
│                                  │                       │
│                 ┌────────────────┼────────────────┐      │
│                 ▼                ▼                ▼      │
│           Log Parser       Hindsight Service   LLM Client │
│                                  │                │      │
└──────────────────────────────────┼────────────────┼──────┘
                                   │                │
                                   ▼                ▼
                           Hindsight API         Groq API
                           Retain / Recall       Log analysis
                           / Reflect
                                   │
                                   ▼
                           Persistent Memory

                    FastAPI Backend
                           │
                           ▼
                    SQLite Database
             Incident metadata and feedback
```

### Component responsibilities

**React frontend** - Collect incident information. - Display analysis
and recommended investigation steps. - Show related historical
incidents. - Allow the engineer to mark a resolution as verified. -
Display incident history and status.

**FastAPI backend** - Validate all incoming data. - Coordinate log
analysis, Hindsight calls, and LLM calls. - Keep API keys on the
server. - Store incident metadata. - Return structured responses to the
frontend.

**Hindsight service** - Retain incident context and verified outcomes. -
Recall relevant incidents for a new problem. - Reflect over accumulated
memory when a summary or cross-incident lesson is needed.

**LLM service** - Interpret the current logs. - Compare current evidence
with retrieved memories. - Produce a structured, cautious diagnosis and
next steps.

**SQLite** - Store application-level incident records and feedback. - It
is not a replacement for Hindsight's memory operations.

------------------------------------------------------------------------

## 5. Proposed Repository Structure

``` text
opsrecall-ai/
│
├── README.md
├── IMPLEMENTATION.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml                 # Optional
│
├── frontend/
│   ├── package.json
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       │
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── Sidebar.jsx
│       │   ├── StatCard.jsx
│       │   ├── IncidentForm.jsx
│       │   ├── IncidentCard.jsx
│       │   ├── AnalysisPanel.jsx
│       │   ├── MemoryMatchCard.jsx
│       │   ├── ResolutionForm.jsx
│       │   └── LoadingState.jsx
│       │
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── NewIncident.jsx
│       │   ├── IncidentDetails.jsx
│       │   └── IncidentHistory.jsx
│       │
│       ├── services/
│       │   └── api.js
│       │
│       └── utils/
│           └── formatters.js
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── incident.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── incident.py
│   │   │   └── analysis.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── incidents.py
│   │   │   └── memory.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── incident_service.py
│   │   │   ├── log_parser.py
│   │   │   ├── hindsight_service.py
│   │   │   ├── llm_service.py
│   │   │   └── analysis_service.py
│   │   │
│   │   └── prompts/
│   │       └── incident_analysis.txt
│   │
│   └── tests/
│       ├── test_health.py
│       ├── test_incidents.py
│       ├── test_log_parser.py
│       └── test_hindsight_service.py
│
├── data/
│   └── sample_incidents/
│       ├── database_pool_exhaustion.log
│       ├── api_timeout.log
│       └── memory_demo_scenarios.md
│
├── docs/
│   ├── architecture.md
│   ├── api.md
│   ├── hindsight-memory.md
│   └── demo-script.md
│
└── screenshots/
    ├── dashboard.png
    ├── incident-analysis.png
    ├── hindsight-memory.png
    └── memory-comparison.png
```

This is the target structure. It is acceptable to start with fewer files
and create modules as they become necessary. Do not create empty folders
just to match the tree.

------------------------------------------------------------------------

## 6. Core Application Workflow

### 6.1 New incident submission

The engineer opens **New Incident** and provides: - Incident title -
Service or component name - Environment (for example, development or
production) - Description of the problem - Error logs or stack trace -
Optional deployment/change context - Optional incident timestamp

The backend validates the input, assigns an incident ID, redacts obvious
secrets, and stores the initial incident record.

### 6.2 Current incident analysis

The backend sends the sanitized incident evidence to the LLM.

The LLM should return structured information: - Short incident summary -
Observed symptoms - Possible root causes - Evidence supporting each
possibility - Suggested investigation steps - Missing information -
Confidence label (for example, low, medium, or high)

The agent must distinguish observed facts from hypotheses. It must not
claim a root cause is confirmed merely because the LLM suggested it.

### 6.3 Hindsight memory recall

Before producing the final recommendation, the backend queries Hindsight
using a natural-language description of the current incident.

The query should include useful details such as: - Service or
component - Error messages - Exception names - Relevant log patterns -
Deployment context - Symptoms and timing

Hindsight returns relevant memories. The backend passes those memories
to the LLM as historical context.

The UI should show a **Related Past Incidents** section. Each result
should include the incident reference or date when available, the
similarity/relevance explanation if available, and the previously
recorded outcome.

### 6.4 Context-aware recommendation

The LLM receives: 1. Current incident evidence 2. Relevant recalled
memories 3. Instructions to separate evidence from assumptions 4.
Instructions to recommend safe investigation steps

It generates a response that explains: - What appears similar to a
previous incident - What was done previously - Whether that earlier fix
is relevant to the current evidence - What the engineer should check
next - What is still uncertain

The agent should never blindly repeat a previous fix. Similar symptoms
do not guarantee identical causes.

### 6.5 Resolution feedback

After investigating, the engineer records: - Whether the recommendation
was useful - Confirmed root cause - Actual resolution steps - Whether
the incident is resolved - Optional notes

Only engineer-confirmed outcomes should be labelled as verified
resolutions.

### 6.6 Retain the learning

The backend sends a useful incident summary to Hindsight using
**retain**. The retained content should include: - Incident identifier -
Service/component - Symptoms and relevant sanitized evidence - Confirmed
root cause, if known - Resolution steps, if confirmed - Outcome and
timestamp - Whether the information is verified or still a hypothesis

Do not store API keys, passwords, tokens, personal information, or
unnecessary raw secrets in memory.

### 6.7 Later incident

When another similar incident arrives, the backend recalls the earlier
incident. The agent can then make a more contextual recommendation.

This is the central demo: the agent's later response should be
demonstrably informed by a real memory retained during an earlier
interaction.

------------------------------------------------------------------------

## 7. Hindsight Memory Design

### 7.1 Hindsight setup

The official problem statement links: - Documentation:
https://hindsight.vectorize.io/ - GitHub:
https://github.com/vectorize-io/hindsight - Hindsight Cloud UI:
https://ui.hindsight.vectorize.io

For the quickest prototype, use Hindsight Cloud or a supported local
deployment. Keep the base URL and credentials in environment variables.

Install the Python client:

``` bash
pip install hindsight-client
```

### 7.2 Memory bank

Create a dedicated bank for the OpsRecall AI incident assistant. Use a
stable bank ID such as:

``` text
opsrecall-incidents
```

Create the bank once during setup or initialization. Do not attempt to
create a new bank for every chat message or incident.

A bank background/mission can describe the domain:

``` text
This memory bank stores software incidents, diagnostic observations,
verified root causes, resolution steps, and outcomes for an engineering
incident response assistant. Distinguish confirmed outcomes from
unverified hypotheses.
```

### 7.3 Three core operations

  -----------------------------------------------------------------------
  Hindsight operation                 How OpsRecall AI uses it
  ----------------------------------- -----------------------------------
  Retain                              Store incident summaries and
                                      verified resolutions

  Recall                              Retrieve relevant past incidents
                                      for a new incident

  Reflect                             Synthesize patterns or lessons
                                      across stored incident memories
  -----------------------------------------------------------------------

### 7.4 Example Python integration

The following is an integration example based on the Hindsight Python
client documentation. Confirm the exact configuration and SDK behavior
against the deployment you use.

``` python
import os
from hindsight_client import Hindsight

client = Hindsight(
    base_url=os.environ["HINDSIGHT_BASE_URL"],
    api_key=os.getenv("HINDSIGHT_API_KEY")
)

BANK_ID = "opsrecall-incidents"

def retain_incident(memory_text: str, incident_id: str):
    return client.retain(
        bank_id=BANK_ID,
        content=memory_text,
        context=f"OpsRecall incident {incident_id}"
    )

def recall_incidents(query: str):
    result = client.recall(
        bank_id=BANK_ID,
        query=query,
        budget="mid"
    )
    return result.results

def reflect_on_incidents(query: str):
    result = client.reflect(
        bank_id=BANK_ID,
        query=query,
        budget="mid"
    )
    return result.text
```

The official Python client documents `Hindsight`, `create_bank`,
`retain`, `recall`, and `reflect`. The exact options available can vary
by deployment and client version. See: -
https://hindsight.vectorize.io/sdks/python -
https://hindsight.vectorize.io/cookbook/recipes/quickstart

### 7.5 Example retained memory

``` text
Incident ID: INC-001
Service: Orders API
Environment: Staging
Symptoms: Requests returned HTTP 500 after a deployment.
Observed evidence: Logs showed database connection acquisition timeouts.
Confirmed root cause: Connection pool limit was too low for the new worker count.
Verified resolution: Pool configuration was adjusted and the service was redeployed.
Outcome: Resolved.
Verification: Confirmed by the engineer.
Timestamp: 2026-11-07T10:30:00Z
```

Use synthetic data for the demo unless you have permission to use real
incident data.

### 7.6 Memory quality rules

-   Store concise, useful incident summaries rather than every token of
    a long conversation.
-   Include timestamps and incident identifiers for traceability.
-   Label hypotheses separately from confirmed findings.
-   Store the outcome only after it has been verified.
-   Avoid retaining secrets and sensitive production data.
-   Show retrieved memory in the UI so judges can see the memory
    connection.
-   Do not simulate memory by reading a hard-coded incident list and
    claiming it came from Hindsight.

### 7.7 What should be visible to judges

During the demo, show: 1. The first incident being analyzed. 2. The
resolution being confirmed. 3. The incident being retained in Hindsight.
4. The memory visible in the Hindsight UI or through a real recall
result. 5. A second related incident being submitted. 6. The previous
incident appearing in the recall results. 7. The agent using that memory
in its recommendation.

------------------------------------------------------------------------

## 8. LLM and Agent Design

### 8.1 Responsibilities of the LLM

The LLM is responsible for interpreting log evidence and writing
explanations. It is not the source of persistent memory; Hindsight is.

### 8.2 Suggested analysis prompt

``` text
You are OpsRecall AI, an assistant for software incident investigation.

Analyze only the incident evidence and historical context supplied to you.

Rules:
1. Separate observed facts from possible explanations.
2. Never claim a root cause is confirmed unless the supplied evidence
   explicitly confirms it.
3. Use historical incidents as context, not as proof that the current
   incident has the same cause.
4. Explain why a historical incident is relevant.
5. Recommend safe, read-only investigation steps first.
6. Do not execute commands or make infrastructure changes.
7. If evidence is insufficient, state what additional information is needed.
8. Do not invent logs, metrics, incidents, or resolutions.

Return structured JSON with:
summary, symptoms, possible_causes, supporting_evidence,
related_memory_insights, recommended_checks, missing_information,
confidence, and safety_notes.
```

### 8.3 Recommended response format

``` json
{
  "summary": "The Orders API is experiencing database acquisition timeouts.",
  "symptoms": ["HTTP 500 responses", "Connection acquisition timeout"],
  "possible_causes": [
    {
      "cause": "Database connection pool exhaustion",
      "evidence": ["Connection acquisition timeout in supplied logs"],
      "confidence": "medium"
    }
  ],
  "related_memory_insights": [
    {
      "incident_id": "INC-001",
      "lesson": "A previous connection pool issue was resolved by reviewing pool limits."
    }
  ],
  "recommended_checks": [
    "Inspect active and idle database connections.",
    "Review connection pool limits and worker count."
  ],
  "missing_information": ["Database connection metrics"],
  "confidence": "medium",
  "safety_notes": ["No infrastructure changes have been performed."]
}
```

Validate the model output with Pydantic. If JSON parsing fails, handle
the error and request a corrected structured response or show a
controlled failure state.

------------------------------------------------------------------------

## 9. Backend API Design

All routes below are proposed application endpoints. They are not
Hindsight endpoints.

  -------------------------------------------------------------------------------------------
  Method                  Endpoint                                    Purpose
  ----------------------- ------------------------------------------- -----------------------
  GET                     `/api/health`                               Check backend health

  POST                    `/api/incidents`                            Create an incident and
                                                                      start analysis

  GET                     `/api/incidents`                            List incidents

  GET                     `/api/incidents/{incident_id}`              Fetch one incident

  POST                    `/api/incidents/{incident_id}/feedback`     Save engineer feedback

  POST                    `/api/incidents/{incident_id}/resolution`   Save verified
                                                                      resolution and retain
                                                                      learning

  POST                    `/api/memory/recall`                        Test Hindsight recall

  POST                    `/api/memory/reflect`                       Request a memory-based
                                                                      summary

  GET                     `/api/dashboard/summary`                    Return incident counts
                                                                      and summary metrics
  -------------------------------------------------------------------------------------------

### Example: create incident request

``` json
{
  "title": "Orders API returning 500 errors",
  "service": "orders-api",
  "environment": "staging",
  "description": "Requests began failing after the latest deployment.",
  "logs": "Database connection acquisition timed out...",
  "deployment_context": "Release 1.4.2"
}
```

### Example: create incident response

``` json
{
  "incident_id": "INC-002",
  "status": "analyzed",
  "analysis": {
    "summary": "Possible database connection pool exhaustion.",
    "confidence": "medium"
  },
  "related_memories": [],
  "recommendations": [
    "Inspect connection pool metrics."
  ]
}
```

Do not expose secrets, raw provider errors, or stack traces to the
browser. Log useful diagnostics on the server without logging
credentials.

------------------------------------------------------------------------

## 10. Data Model

### Incident

  Field            Type       Description
  ---------------- ---------- -------------------------------------
  id               String     Unique incident ID
  title            String     Incident title
  service          String     Affected service
  environment      String     Development, staging, or production
  description      Text       User-provided explanation
  sanitized_logs   Text       Redacted log content
  status           String     New, analyzing, analyzed, resolved
  created_at       DateTime   Creation timestamp
  updated_at       DateTime   Last update timestamp

### IncidentAnalysis

  Field             Type       Description
  ----------------- ---------- -------------------------------
  id                String     Analysis ID
  incident_id       String     Related incident
  summary           Text       AI-generated summary
  possible_causes   JSON       Candidate causes and evidence
  recommendations   JSON       Suggested checks
  confidence        String     Low, medium, or high
  created_at        DateTime   Analysis timestamp

### IncidentResolution

  Field                  Type       Description
  ---------------------- ---------- ------------------------------------
  id                     String     Resolution ID
  incident_id            String     Related incident
  confirmed_root_cause   Text       Engineer-confirmed cause
  resolution_steps       Text       Steps that resolved the issue
  outcome                String     Resolved, unresolved, or mitigated
  verified_by_user       Boolean    Whether an engineer confirmed it
  created_at             DateTime   Confirmation timestamp

Hindsight stores and retrieves the agent's persistent memories. The
application database stores these structured application records and
their relationships.

------------------------------------------------------------------------

## 11. Frontend Screens and UX

### 11.1 Dashboard

Display: - Total incidents - Open incidents - Resolved incidents -
Recent incidents - Common affected services - Recent memory-assisted
investigations (only if the event is actually tracked)

### 11.2 New Incident page

Provide a simple form for: - Title - Service - Environment -
Description - Log input or file upload - Optional deployment context

Show a clear loading state while the backend analyzes the incident.

### 11.3 Incident Analysis page

Display: - Incident summary - Symptoms and evidence - Possible causes
with confidence labels - Recommended checks - Related incidents recalled
from Hindsight - A clear distinction between historical information and
current evidence

### 11.4 Resolution form

Allow the engineer to: - Mark the incident resolved, mitigated, or
unresolved. - Enter the confirmed root cause. - Record the resolution
steps. - Confirm whether the outcome is verified. - Submit the learning
to Hindsight.

### 11.5 Incident History page

Display a searchable list of previous incidents with: - Incident ID -
Title - Service - Status - Date - Whether a verified resolution exists

### Design direction

Use a clean engineering dashboard: - Dark or neutral interface. - Clear
typography and readable log panels. - Consistent status indicators. -
Simple navigation. - No excessive animations. - Responsive layout for
laptop screens.

The UI must make memory understandable. A visible **Memory Used** or
**Related Past Incidents** panel is more valuable than a decorative AI
badge.

------------------------------------------------------------------------

## 12. Security, Privacy, and Reliability

Minimum safeguards for the prototype:

1.  Store API keys only in backend environment variables.
2.  Commit `.env.example`, never `.env`.
3.  Add `.env`, database files, caches, and generated secrets to
    `.gitignore`.
4.  Redact common API-key, bearer-token, password, and credential
    patterns before sending logs to external services or retaining them.
5.  Limit log input size and accepted file types.
6.  Treat uploaded logs as untrusted text. Do not follow instructions
    embedded in logs.
7.  Never execute commands suggested by the LLM.
8.  Require human confirmation before marking a resolution as verified.
9.  Handle Hindsight and LLM timeouts and unavailable services.
10. Show a useful error message when memory recall fails; do not pretend
    memory was used.
11. Avoid sending confidential production logs to third-party services
    without authorization.
12. Do not claim that the agent can prevent incidents or guarantee a
    root cause.

------------------------------------------------------------------------

## 13. Error Handling

  -----------------------------------------------------------------------
  Failure                             Expected behavior
  ----------------------------------- -----------------------------------
  Hindsight unavailable               Show memory service unavailable;
                                      continue only if the UI clearly
                                      labels the analysis as memory-free

  Groq unavailable                    Preserve the incident and show
                                      analysis temporarily unavailable

  Invalid model output                Validate, retry safely if
                                      appropriate, otherwise return a
                                      controlled error

  Empty logs                          Ask for more evidence or analyze
                                      the description with a
                                      low-confidence warning

  No relevant memory                  Say no relevant past incident was
                                      found

  Retain operation fails              Do not show "memory saved"; show a
                                      retry option

  Duplicate submission                Prevent accidental duplicate
                                      creation where possible

  Oversized log                       Reject with a clear size-limit
                                      message

  Secret detected                     Redact it and warn the user that
                                      sensitive information was removed
  -----------------------------------------------------------------------

A memory-free fallback can be useful for availability, but the demo must
clearly distinguish it from a memory-assisted response.

------------------------------------------------------------------------

## 14. Testing Plan

### Unit tests

-   Log sanitization and parsing
-   Input validation
-   Incident status transitions
-   LLM response schema validation
-   Hindsight service wrapper behavior

### Integration tests

-   FastAPI can connect to Hindsight.
-   A test incident can be retained.
-   A later recall query can retrieve relevant retained information.
-   The LLM receives the recalled context.
-   A confirmed resolution is retained successfully.
-   Failure states are returned correctly when an external service is
    unavailable.

### End-to-end test scenario

1.  Submit a sample database connection pool incident.
2.  Analyze it.
3.  Record a verified resolution.
4.  Confirm that Hindsight retain succeeds.
5.  Submit another incident with related symptoms.
6.  Confirm that Hindsight recall returns the earlier incident.
7.  Confirm that the final response references the recalled information.
8.  Verify that the UI displays the memory result and its source.

### Acceptance criteria

The prototype is ready for demonstration when: - A user can submit an
incident through the UI. - The backend returns a structured analysis. -
Hindsight retain works with the configured bank. - Hindsight recall
retrieves a relevant retained incident. - The later recommendation
visibly uses the recalled information. - A user can record a
resolution. - The UI handles loading and error states. - The README
explains setup and Hindsight integration. - No credentials are committed
to GitHub.

------------------------------------------------------------------------

## 15. Sample Demo Data

Use realistic but synthetic data so that the demo is repeatable and does
not expose real production information.

### Scenario A: first incident

**Title:** Orders API returns HTTP 500 after deployment

**Logs:**

``` text
2026-11-07 10:12:01 ERROR orders-api
Database connection acquisition timed out.

2026-11-07 10:12:02 ERROR orders-api
Request failed: GET /orders

2026-11-07 10:12:03 WARN database-pool
Active connections reached configured maximum.
```

The agent should identify database connection pool exhaustion as a
possibility, not a confirmed root cause until the engineer verifies it.

For the demo, the engineer confirms that the pool limit was too low for
the worker count, adjusts the configuration, and verifies recovery. The
confirmed outcome is then retained in Hindsight.

### Scenario B: later related incident

**Title:** Checkout API timing out after scaling workers

**Logs:**

``` text
2026-11-08 09:30:10 ERROR checkout-api
Timeout waiting for database connection.

2026-11-08 09:30:11 WARN database-pool
Connection pool utilization: 100%.
```

The agent should recall the earlier incident and suggest checking the
connection pool configuration and worker count. It must still analyze
the current evidence rather than assuming the root cause is identical.

------------------------------------------------------------------------

## 16. Demo Storyboard

Aim for a short, clear demo of approximately 2--4 minutes.

  -----------------------------------------------------------------------
  Step                    What to show            What the audience
                                                  should understand
  ----------------------- ----------------------- -----------------------
  1                       Dashboard and problem   Engineers repeat
                          statement               investigations when
                                                  incident knowledge is
                                                  scattered

  2                       Submit first incident   OpsRecall analyzes
                                                  current logs

  3                       Show analysis           The agent identifies
                                                  possible causes and
                                                  evidence

  4                       Confirm resolution      The engineer verifies
                                                  what actually fixed the
                                                  issue

  5                       Show Hindsight retain   The incident outcome is
                                                  stored in persistent
                                                  memory

  6                       Submit a related second The agent is given a
                          incident                new problem

  7                       Show Hindsight recall   The earlier incident is
                                                  retrieved

  8                       Show improved           The response uses the
                          recommendation          prior verified
                                                  resolution as context

  9                       Show architecture       React, FastAPI, Groq,
                          briefly                 and Hindsight have
                                                  distinct
                                                  responsibilities
  -----------------------------------------------------------------------

Do not fake the before/after. Capture the real retain and recall
operations, and show actual results from the configured Hindsight
instance.

------------------------------------------------------------------------

## 17. Development Plan and Priorities

### Phase 1 --- Project foundation

-   Create the GitHub repository.
-   Create frontend and backend folders.
-   Set up React + Vite.
-   Set up FastAPI and a health endpoint.
-   Add `.env.example` and `.gitignore`.
-   Confirm both frontend and backend run locally.

### Phase 2 --- Basic incident workflow

-   Build the dashboard layout.
-   Build the new incident form.
-   Add incident creation API.
-   Store incident metadata.
-   Display incident history.

### Phase 3 --- LLM analysis

-   Configure Groq API.
-   Create the incident analysis prompt.
-   Parse and validate structured output.
-   Display summary, evidence, possible causes, and recommended checks.

### Phase 4 --- Hindsight integration

-   Set up Hindsight Cloud or local deployment.
-   Create the incident memory bank.
-   Implement the Hindsight service wrapper.
-   Implement retain and recall.
-   Test with a small incident pair.
-   Add visible memory results to the UI.
-   Add reflect only where it improves a real cross-incident summary.

### Phase 5 --- Resolution learning

-   Add resolution form.
-   Require engineer confirmation.
-   Retain the verified outcome.
-   Test a later similar incident.
-   Capture evidence that recall changes the later response.

### Phase 6 --- Polish and validation

-   Improve loading and error states.
-   Add sample data.
-   Test the complete demo flow.
-   Check secret handling.
-   Update README and architecture documentation.
-   Capture genuine screenshots.

### Phase 7 --- Submission

-   Verify the GitHub repository is accessible.
-   Record and publish the team demo video.
-   Prepare the live demonstration.
-   Explain exactly how Hindsight is used.
-   Complete the separate content-guide deliverables for each team
    member.

**Priority rule:** If time is short, finish one end-to-end incident →
retain → recall → improved response flow before adding charts, file
uploads, authentication, or extra integrations.

------------------------------------------------------------------------

## 18. Environment Configuration

Create `backend/.env.example`:

``` env
APP_NAME=OpsRecall AI
APP_ENV=development
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000

GROQ_API_KEY=replace_with_your_key
GROQ_MODEL=replace_with_available_model

HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
HINDSIGHT_API_KEY=replace_with_your_key
HINDSIGHT_BANK_ID=opsrecall-incidents

DATABASE_URL=sqlite:///./opsrecall.db

FRONTEND_ORIGIN=http://localhost:5173
```

Copy it to `.env` and fill in real credentials locally. Never commit
`.env`.

For a local Hindsight deployment, replace `HINDSIGHT_BASE_URL` with the
local API URL shown by that deployment. Follow the official setup guide
for the selected deployment mode.

------------------------------------------------------------------------

## 19. Local Development Commands

### Backend

``` bash
cd backend

python -m venv .venv
```

Activate the virtual environment:

**Windows PowerShell**

``` powershell
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

``` bash
source .venv/bin/activate
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

Run FastAPI:

``` bash
uvicorn app.main:app --reload
```

The API should be available at `http://127.0.0.1:8000`. FastAPI's
interactive API documentation is normally available at `/docs`.

### Frontend

``` bash
cd frontend
npm install
npm run dev
```

Vite normally serves the frontend at `http://localhost:5173`.

### Suggested backend dependencies

``` text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-dotenv
hindsight-client
httpx
groq
sqlalchemy
pytest
```

Pin tested dependency versions in the final `requirements.txt` before
submission. Add only packages the implementation actually uses.

------------------------------------------------------------------------

## 20. GitHub README Requirements

The repository README should include:

1.  Project name and short description.
2.  Problem statement.
3.  Solution overview.
4.  Key features.
5.  Architecture diagram.
6.  Technology stack.
7.  How Hindsight is integrated.
8.  How retain, recall, and reflect are used.
9.  Setup instructions.
10. Environment variables.
11. How to run frontend and backend.
12. Screenshots.
13. Demo video link.
14. Limitations and future improvements.
15. Credits and links to Hindsight documentation.

The README must describe the actual implementation. Remove features from
the feature list if they have not been built.

------------------------------------------------------------------------

## 21. Hackathon Content and Submission Checklist

Based on the supplied problem statement and content guide, track the
following separately from software development.

### Project deliverables

-   [ ] GitHub repository with clean, documented code
-   [ ] Working prototype
-   [ ] Demo video showing the agent in action
-   [ ] Live project demo prepared for judges
-   [ ] Clear explanation of Hindsight memory usage
-   [ ] Evidence of real retain and recall operations

### Content-guide deliverables

-   [ ] Each team member completes their own required technical article.
-   [ ] Each team member publishes their own required social media post.
-   [ ] The team publishes its demo video according to the guide.
-   [ ] Each article is publicly accessible on the chosen publishing
    platform.
-   [ ] Each article is submitted to one of the subreddits specified in
    the guide.
-   [ ] Follow the content guide's word count, formatting, screenshot,
    and wording restrictions.
-   [ ] Check the guide carefully before publishing; the content
    deliverables are separate from the GitHub project submission.

The content guide includes restrictions on mentioning the hackathon in
the individual article and social post. Follow the supplied guide
exactly when preparing those materials.

------------------------------------------------------------------------

## 22. Known Limitations and Future Improvements

### Initial prototype limitations

-   The agent analyzes only the logs and context supplied by the user.
-   It does not monitor production infrastructure.
-   It does not execute fixes or shell commands.
-   Analysis quality depends on the quality of logs and the selected
    LLM.
-   Memory recall may return no relevant result or an imperfect match.
-   Synthetic demo data does not establish production reliability.

### Future improvements

-   Integrate observability tools such as monitoring and log platforms.
-   Import incident records from issue trackers.
-   Add team-level access control and audit logs.
-   Add incident timelines and deployment correlation.
-   Add configurable memory retention policies.
-   Add evaluation datasets to measure diagnosis quality and memory
    usefulness.
-   Add human-approved runbook suggestions.
-   Add deployment-specific integrations after security review.

------------------------------------------------------------------------

## 23. Definition of Done

OpsRecall AI's core prototype is complete when a judge can watch the
following happen without relying on a scripted claim:

1.  An engineer submits a realistic incident.
2.  The agent analyzes the supplied evidence.
3.  Hindsight receives a real retain operation after a verified outcome.
4.  The team can inspect the stored memory or confirm it through recall.
5.  A second related incident is submitted.
6.  Hindsight returns the earlier incident as relevant context.
7.  The agent uses that context to produce a more informed
    recommendation.
8.  The engineer can understand which details came from current logs and
    which came from historical memory.

**The most important proof is not that the interface says "Memory
Enabled." It is that a real memory retained from one incident is
recalled and meaningfully used in a later incident.**

------------------------------------------------------------------------

## 24. Official References

-   Hackathon problem statement supplied by the organizers.
-   Hindsight documentation: https://hindsight.vectorize.io/
-   Hindsight GitHub: https://github.com/vectorize-io/hindsight
-   Hindsight Cloud UI: https://ui.hindsight.vectorize.io
-   Hindsight Python SDK: https://hindsight.vectorize.io/sdks/python
-   Hindsight quickstart:
    https://hindsight.vectorize.io/cookbook/recipes/quickstart
-   Groq: https://groq.com/
-   Band AI desktop: https://www.band.ai

------------------------------------------------------------------------

**Implementation principle:** Build a small, reliable incident-response
agent with a genuine Hindsight memory loop. A clear and verifiable
retain → recall → improved response demonstration is more valuable than
a large collection of unfinished features.
