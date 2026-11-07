from fastapi import APIRouter

from app.schemas.incident import IncidentMemoryRequest
from app.services.hindsight_service import memory_client

router = APIRouter()


@router.post("/api/memory/recall")
def recall_memories(payload: IncidentMemoryRequest):
    return {"results": memory_client.recall(payload.query)}


@router.post("/api/memory/reflect")
def reflect_memories(payload: IncidentMemoryRequest):
    return {"summary": memory_client.reflect(payload.query)}
