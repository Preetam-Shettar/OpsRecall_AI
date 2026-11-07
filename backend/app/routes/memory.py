from fastapi import APIRouter

from app.schemas.incident import IncidentMemoryRequest
from app.services.hindsight_service import memory_client

router = APIRouter()


@router.post("/api/memory/recall")
def recall_memories(payload: IncidentMemoryRequest):
    results = memory_client.recall(payload.query, budget=payload.budget)
    return {
        "query": payload.query,
        "bank_id": memory_client.bank_id,
        "results_count": len(results),
        "results": results,
    }


@router.post("/api/memory/reflect")
def reflect_memories(payload: IncidentMemoryRequest):
    summary = memory_client.reflect(payload.query, budget=payload.budget)
    return {
        "query": payload.query,
        "bank_id": memory_client.bank_id,
        "summary": summary,
    }
