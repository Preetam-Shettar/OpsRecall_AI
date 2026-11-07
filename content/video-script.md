# OpsRecall AI: 3-Minute Product Demonstration Video Script

**Target Video Length**: ~3 minutes (180 seconds)  
**Tone**: Confident, technical, concise, production-ready  
**Actors / Speakers**: Presenter (Screen share + voiceover or camera in corner)

---

### [0:00 - 0:35] Scene 1: The Problem & Introduction
**Visual**: Presenter on screen, transitioning to the OpsRecall AI Dashboard (`http://localhost:5173`). Clean modern UI visible with telemetry counters and theme switcher.

**Voiceover / Speaker**:
> "Hi everyone, welcome to OpsRecall AI.
> 
> In production environments, when critical services fail, on-call engineers often waste precious minutes diagnosing symptoms from scratch—even when an identical issue was solved weeks earlier. AI diagnostic assistants usually make this worse by treating every incident as a blank slate.
>
> We built OpsRecall AI to solve operational amnesia. It pairs rapid Groq LLM log diagnostics with a **persistent, engineer-verified learning loop** powered by Hindsight. Let's see it in action across two realistic production incidents."

---

### [0:35 - 1:25] Scene 2: Scenario A – Ingestion, Diagnosis & Retain
**Visual**: Click **Investigate New Incident**. Fill in:
- Title: `Orders API returns HTTP 500 after deployment`
- Service: `orders-api`
- Environment: `Staging`
- Logs: Paste `data/sample_incidents/database_pool_exhaustion.log` (shows pool exhaustion `max_connections=50` error).
- Click **Analyze Incident with OpsRecall AI**.

**Voiceover / Speaker**:
> "Here in Scenario A, our `orders-api` service starts throwing HTTP 500 errors.
>
> When we submit the raw logs, OpsRecall AI first sanitizes sensitive tokens and connection strings. Then, it calls our FastAPI backend to perform deep diagnostics.
>
> Notice the analysis panel: it immediately highlights connection pool exhaustion, identifies the exact file `db.py:42`, and outlines recommended checks.
>
> Now, as the on-call engineer, I apply the fix: increasing the pool size to 100 and fixing connection leak handling. I record the root cause: *'Connection pool exhausted under peak load'*, outline the steps, and check the box: **'Verified by on-call engineer'**.
>
> When I click **Save Resolution**, OpsRecall triggers the Hindsight **Retain** operation. Because this fix is verified by a human, it is permanently committed to our Hindsight memory bank: `opsrecall-incidents`."

---

### [1:25 - 2:20] Scene 3: Scenario B – Symptom Drift & Instant Recall
**Visual**: Return to Dashboard. The incident now shows a green **Resolved** badge with a purple `✓ Memory Saved` indicator. Click **Investigate New Incident**.
- Title: `Checkout API timing out after scaling workers`
- Service: `checkout-api`
- Environment: `Production`
- Logs: Paste `data/sample_incidents/api_timeout.log` (shows HTTP 504 Gateway Timeout while calling orders-api).
- Click **Analyze Incident with OpsRecall AI**.

**Voiceover / Speaker**:
> "Now, Scenario B: 48 hours later, a completely different service—`checkout-api`—is reporting HTTP 504 Gateway Timeouts.
>
> A standard stateless AI would suggest inspecting checkout gateway timeouts. But watch what happens with OpsRecall AI:
>
> Look at the **Recalled Past Incidents** card right above the diagnosis! OpsRecall queried Hindsight using the semantic signatures of the logs and instantly recalled our previous `orders-api` database pool exhaustion incident with a 92% confidence match.
>
> The diagnosis directly tells the engineer: *'Previous incident INC-20261107 showed that database pool exhaustion in orders-api caused upstream timeouts. Check orders-api database connection metrics before restarting checkout workers.'*
>
> Instead of spending an hour chasing downstream checkout symptoms, the engineer fixes the upstream issue in seconds."

---

### [2:20 - 2:45] Scene 4: The Hindsight Memory Explorer & Reflect
**Visual**: Navigate to **Hindsight Memory** in the left sidebar navigation. Display the memory table and the **Reflect & Synthesize** card. Click **Generate Reflection Analysis**.

**Voiceover / Speaker**:
> "Here in the **Hindsight Memory Explorer**, engineering leads have full visibility into the organizational knowledge graph. You can inspect all retained verified memories, search across services, and invoke Hindsight's **Reflect** capability.
>
> Reflect synthesizes cross-incident failure modes—identifying recurring systemic bottlenecks like database connection limits across our microservices before they cause cascading outages."

---

### [2:45 - 3:00] Scene 5: Architecture & Wrap-Up
**Visual**: Quick screen showing the architecture diagram from `README.md` and the 4-color theme switcher in the UI (Obsidian, Emerald, Synthwave, Slate).

**Voiceover / Speaker**:
> "OpsRecall AI is built with React 19, FastAPI, Groq, and Hindsight with automatic local SQLite fallback, fully containerized with Docker.
>
> OpsRecall AI turns single-engineer resolutions into shared organizational resilience. Thank you!"
