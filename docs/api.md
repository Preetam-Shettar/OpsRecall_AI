# OpsRecall AI — REST API Documentation

All application endpoints run under the `/api` prefix on the backend server (default: `http://127.0.0.1:8000`).

---

### 1. Health Endpoint
- **Method:** `GET`
- **Path:** `/api/health`
- **Response:**
  ```json
  {
    "status": "ok",
    "service": "opsrecall-ai"
  }
  ```

---

### 2. Create Incident & Diagnose
- **Method:** `POST`
- **Path:** `/api/incidents`
- **Request Body:**
  ```json
  {
    "title": "Orders API returning 500 errors",
    "service": "orders-api",
    "environment": "staging",
    "description": "Requests began failing after latest release",
    "logs": "Database connection acquisition timed out...",
    "deployment_context": "Release 1.4.2"
  }
  ```
- **Response:**
  ```json
  {
    "incident_id": "INC-20261107-101201-A1B2",
    "status": "analyzed",
    "analysis": {
      "summary": "Database connection pool exhaustion...",
      "symptoms": ["Request timeouts"],
      "possible_causes": [{ "cause": "Pool exhausted", "confidence": "high" }],
      "related_memory_insights": [],
      "recommended_checks": ["Inspect connection pool limits"],
      "confidence": "medium"
    },
    "related_memories": [],
    "recommendations": ["Inspect connection pool limits"]
  }
  ```

---

### 3. List Incidents
- **Method:** `GET`
- **Path:** `/api/incidents?search=orders&status=resolved`
- **Response:** Array of incident records.

---

### 4. Fetch Single Incident
- **Method:** `GET`
- **Path:** `/api/incidents/{incident_id}`

---

### 5. Save Feedback
- **Method:** `POST`
- **Path:** `/api/incidents/{incident_id}/feedback`
- **Request Body:**
  ```json
  {
    "helpful": true,
    "notes": "Recommendation correctly identified pool limit issue."
  }
  ```

---

### 6. Save Verified Resolution (Retains to Hindsight)
- **Method:** `POST`
- **Path:** `/api/incidents/{incident_id}/resolution`
- **Request Body:**
  ```json
  {
    "root_cause": "Connection pool limit was too low for worker count",
    "resolution": "Increased pool_size to 40 in config and restarted service",
    "outcome": "resolved",
    "verified": true,
    "engineer": "On-call Engineer"
  }
  ```

---

### 7. Hindsight Recall
- **Method:** `POST`
- **Path:** `/api/memory/recall`
- **Request Body:**
  ```json
  {
    "query": "database connection pool timeout",
    "budget": "mid"
  }
  ```

---

### 8. Hindsight Reflect
- **Method:** `POST`
- **Path:** `/api/memory/reflect`
- **Request Body:**
  ```json
  {
    "query": "database connection pool timeout",
    "budget": "mid"
  }
  ```

---

### 9. Dashboard Telemetry Summary
- **Method:** `GET`
- **Path:** `/api/dashboard/summary`
