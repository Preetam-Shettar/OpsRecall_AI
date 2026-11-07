# OpsRecall AI

OpsRecall AI is a prototype incident-response assistant that analyzes engineering incidents, recalls similar prior incidents from Hindsight memory, and records verified resolutions for future reuse.

## Quick start

1. Create a Python environment and install backend dependencies:
   ```bash
   python -m pip install -r backend/requirements.txt
   ```
2. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
3. Copy environment variables:
   ```bash
   copy .env.example .env
   ```
4. Start the backend:
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
5. Start the frontend:
   ```bash
   cd frontend
   npm run dev -- --host 0.0.0.0 --port 5173
   ```

## Notes

- The app runs without Groq or Hindsight credentials by falling back to deterministic local analysis and memory storage. The analysis panel labels local analysis and any fallback from Groq.
- When `GROQ_API_KEY` is configured, incident analysis uses Groq's JSON response mode and validates the result before returning it.
- If a real Hindsight instance is configured, the backend will use it automatically for recall and retention.
- This is a working prototype designed for a demo flow rather than production deployment.
