from pathlib import Path
import os
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

DATABASE_PATH = Path(os.getenv("DATABASE_PATH", str(REPO_ROOT / "backend" / "data" / "opsrecall.db")))
if not DATABASE_PATH.is_absolute():
    DATABASE_PATH = REPO_ROOT / DATABASE_PATH
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
HINDSIGHT_BASE_URL = os.getenv("HINDSIGHT_BASE_URL")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "opsrecall-incidents")
BACKEND_CORS_ORIGINS = [item.strip() for item in os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:5173").split(",") if item.strip()]
