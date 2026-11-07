# OpsRecall AI — System Architecture

## High-Level Architecture Overview

OpsRecall AI is an AI agent for engineering operations and incident response that pairs structured LLM diagnostics with persistent memory powered by **Hindsight**.

```
┌────────────────────────────────────────────────────────┐
│                   React 19 Frontend                    │
│                                                        │
│ Dashboard | New Incident | Details | History | Memory  │
└───────────────────────────┬────────────────────────────┘
                            │ REST / JSON
                            ▼
┌────────────────────────────────────────────────────────┐
│                   FastAPI Backend                      │
│                                                        │
│ Routes → Sanitizer → Incident Orchestrator → Agent     │
│                             │                          │
│            ┌────────────────┼────────────────┐         │
│            ▼                ▼                ▼         │
│      Log Parser     Hindsight Service   LLM Client     │
│                             │                │         │
└─────────────────────────────┼────────────────┼─────────┘
                              │                │
                              ▼                ▼
                     Hindsight Memory Bank  Groq API
                        Retain / Recall /   Log Analysis
                            Reflect
                              │
                              ▼
                     Persistent Memory Engine
                              │
                    SQLite Application DB
                   Incident Records & Audits
```

## Core Components

1. **Frontend (React + Vite)**:
   - Modern dark-mode engineering operations console.
   - Provides 1-click demo scenario loading, real-time log sanitization feedback, and side-by-side memory correlation.
   - Highlights engineer-verified resolutions distinctly from AI hypotheses.

2. **Backend (Python + FastAPI)**:
   - Orchestrates incident ingestion, validation, and diagnostic pipelines.
   - Enforces secret redaction on all incoming logs before LLM or memory calls.
   - Synchronizes application metadata in SQLite while delegating persistent knowledge retention and semantic recall to Hindsight.

3. **Hindsight Memory Integration**:
   - Bank: `opsrecall-incidents`.
   - **Retain**: Invoked only when an engineer confirms a verified root cause and resolution.
   - **Recall**: Invoked upon submitting a new incident using natural language descriptions, error terms, and service metadata.
   - **Reflect**: Synthesizes cross-incident recurring failure patterns across historical outages.

4. **Groq LLM Service**:
   - Formulates structured JSON diagnostics (summary, observed symptoms, candidate causes, safe read-only checks).
   - Treats log text strictly as untrusted evidence, avoiding prompt injection or unsafe automation.
