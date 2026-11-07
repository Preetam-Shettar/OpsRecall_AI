# Persistent Memory Architecture with Hindsight

## Overview

A critical challenge in modern incident response is **scattered knowledge**. When an application outage happens, engineers spend hours diagnosing root causes that colleagues already resolved days or weeks earlier. Standard LLM chatbots cannot solve this because each session starts from zero without memory of team fixes.

OpsRecall AI integrates **Hindsight** (https://hindsight.vectorize.io/) as the core persistent memory bank (`opsrecall-incidents`).

---

## The Three Core Hindsight Operations

### 1. Retain
- **When it fires:** Triggered only when a human engineer confirms a root cause and resolution in the Resolution Form.
- **Why human verification matters:** Storing speculative chatbot hypotheses into persistent memory causes hallucination loops. Only verified engineering outcomes are retained.
- **Payload structure:**
  ```text
  Incident ID: INC-001
  Service: orders-api
  Environment: staging
  Symptoms: Requests returned HTTP 500 after a deployment.
  Observed evidence: Logs showed database connection acquisition timeouts.
  Confirmed root cause: Connection pool limit was too low for the new worker count.
  Verified resolution: Pool configuration was adjusted and the service was redeployed.
  Outcome: resolved
  Verification: confirmed by engineer
  Timestamp: 2026-11-07T10:30:00Z
  ```

### 2. Recall
- **When it fires:** Triggered automatically whenever a new incident is submitted.
- **Query generation:** Synthesizes the affected service name, error messages, exception classes, and log snippets into a natural-language search query.
- **Context Injection:** Recalled memories are supplied to the LLM prompt under `historical_memories`, directing the LLM to inspect relevant previous fixes without assuming the root cause is identical.

### 3. Reflect
- **When it fires:** Triggered on-demand via the **Hindsight Memory Explorer** or scheduled reviews.
- **Purpose:** Analyzes accumulated memory records to surface systemic infrastructure patterns (e.g. repeated connection pool bottlenecks across multiple services).
