from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import BACKEND_CORS_ORIGINS
from app.database import init_db
from app.routes.health import router as health_router
from app.routes.incidents import router as incidents_router
from app.routes.memory import router as memory_router

app = FastAPI(
    title="OpsRecall AI API",
    description="AI-powered incident response assistant with persistent Hindsight memory",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(incidents_router)
app.include_router(memory_router)


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {
        "service": "OpsRecall AI",
        "version": "0.1.0",
        "status": "operational",
        "endpoints": {
            "health": "/api/health",
            "incidents": "/api/incidents",
            "dashboard": "/api/dashboard/summary",
            "recall": "/api/memory/recall",
            "reflect": "/api/memory/reflect",
            "docs": "/docs",
        },
    }
