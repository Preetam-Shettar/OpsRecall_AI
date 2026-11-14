from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.incident import IncidentMemoryRequest, MemoryDetail, MemoryListResponse
from app.services.hindsight_service import memory_client
from app.services.incident_service import incident_service

router = APIRouter()


@router.get("/api/memory", response_model=MemoryListResponse)
def list_memories(
    search: Optional[str] = Query(None, description="Search term in incident ID, service, root cause or resolution"),
    service: Optional[str] = Query(None, description="Filter by service"),
    severity: Optional[str] = Query(None, description="Filter by severity (critical, high, medium, low)"),
    environment: Optional[str] = Query(None, description="Filter by environment (production, staging, development)"),
    verified: Optional[bool] = Query(True, description="Filter by verification status. Default: True (only verified memories in catalog)"),
    page: int = Query(1, ge=1, description="Page number, 1-indexed"),
    page_size: int = Query(10, ge=1, le=100, description="Page size, 1 to 100"),
):
    return incident_service.list_memories(
        search=search,
        service=service,
        severity=severity,
        environment=environment,
        verified=verified,
        page=page,
        page_size=page_size,
    )


@router.get("/api/memory/{memory_id}", response_model=MemoryDetail)
def get_memory(memory_id: str):
    memory = incident_service.get_memory_detail(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail=f"Memory record '{memory_id}' not found.")
    return memory


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
