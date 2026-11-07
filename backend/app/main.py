import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import BACKEND_CORS_ORIGINS
from app.database import init_db
from app.routes.health import router as health_router
from app.routes.incidents import router as incidents_router
from app.routes.memory import router as memory_router


class DoubleSlashNormalizerMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http" and "//" in scope.get("path", ""):
            scope["path"] = re.sub(r"/+", "/", scope["path"])
        await self.app(scope, receive, send)


app = FastAPI(
    title="OpsRecall AI API",
    description="AI-powered incident response assistant with persistent Hindsight memory",
    version="0.1.0",
)

app.add_middleware(DoubleSlashNormalizerMiddleware)

# Enable CORS for all requesting origins (local, preview, or deployed frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=BACKEND_CORS_ORIGINS if (BACKEND_CORS_ORIGINS and "*" not in BACKEND_CORS_ORIGINS) else [],
    allow_origin_regex=r"^https?://.*$" if ("*" in BACKEND_CORS_ORIGINS or not BACKEND_CORS_ORIGINS) else None,
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
