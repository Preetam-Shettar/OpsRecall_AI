# OpsRecall AI — 3-Minute Hackathon Demo Script

Follow this step-by-step storyboard for recording the project demo video or presenting live to judges.

---

### Step 1: Problem Statement (0:00 - 0:30)
- **Show:** The OpsRecall AI Dashboard (`http://localhost:5173`).
- **Narrate:**
  > *"When services fail, engineering teams repeat the exact same investigations because past solutions stay locked in post-mortems or forgotten chat channels. Standard chatbots analyze logs, but they forget how our team solved similar issues last week. OpsRecall AI fixes this with persistent memory powered by Hindsight."*

---

### Step 2: Scenario A — The First Incident (0:30 - 1:15)
- **Action:**
  1. Click **New Incident** in the sidebar.
  2. Click **Scenario A (Orders API 500)** to pre-populate logs showing connection acquisition timeouts.
  3. Click **Investigate Incident with AI**.
- **Show:**
  - Fast analysis results showing symptoms, candidate causes, and safe recommended checks.
  - Point out that **Related Past Incidents** is currently empty: *"No relevant past incidents found yet because the memory bank has not learned this failure."*
- **Action:**
  4. Scroll down to the **Resolution Feedback** card.
  5. Click **Fill Demo Resolution** (sets confirmed root cause to pool limit mismatch).
  6. Click **Save Verified Resolution & Retain in Hindsight**.
- **Show:** The green success alert confirming that the verified fix has been retained in the persistent memory bank.

---

### Step 3: Scenario B — The Persistent Memory Test (1:15 - 2:15)
- **Narrate:**
  > *"Now imagine a different microservice—the Checkout API—starts timing out after engineers scaled worker concurrency."*
- **Action:**
  1. Click **New Incident**.
  2. Click **Scenario B (Checkout Timeout)**.
  3. Click **Investigate Incident with AI**.
- **Show (The 'Aha!' moment):**
  - Point directly to the **Hindsight Recall Active** card at the top of the diagnosis!
  - Show that **Scenario A (Orders API pool exhaustion)** was automatically recalled as context.
  - The diagnosis immediately warns the engineer: *"A previous connection pool issue was resolved by reviewing pool limits vs worker concurrency."*
- **Narrate:**
  > *"Notice the difference: The agent didn't blindly guess. It recalled the exact verified resolution our team discovered earlier, saving valuable triage time."*

---

### Step 4: Memory Explorer & Reflect (2:15 - 2:45)
- **Action:**
  1. Click **Hindsight Memory** in the sidebar.
  2. Type `database connection pool timeout` and click **Test Hindsight Recall**.
  3. Click **Synthesize Reflection** to demonstrate cross-incident pattern recognition.
- **Narrate:**
  > *"Through Hindsight's retain, recall, and reflect operations, OpsRecall AI turns every resolved incident into persistent institutional knowledge."*

---

### Step 5: Wrap-up & Architecture (2:45 - 3:00)
- **Show:** Dashboard summary showing updated resolved count and stored memories count.
- **Conclude:**
  > *"OpsRecall AI combines React, FastAPI, Groq LLM diagnostics, and Hindsight persistent memory into a safe, production-grade incident assistant."*
