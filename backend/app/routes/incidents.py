from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.schemas.action_plan import (
    ActionBatchImportRequest,
    ActionCreate,
    ActionResponse,
    ActionUpdate,
    IncidentActionPlanSummary,
    TimelineEventResponse,
)
from app.schemas.incident import IncidentCreate, IncidentFeedback, IncidentResolution
from app.services.incident_service import incident_service

router = APIRouter()


@router.post("/api/incidents")
def create_incident(payload: IncidentCreate):
    incident = incident_service.create_incident(payload.model_dump())
    return {
        "incident_id": incident["id"],
        "status": incident["status"],
        "analysis": incident["analysis"],
        "related_memories": incident["related_memories"],
        "recommendations": incident["recommendations"],
    }


@router.get("/api/incidents")
def list_incidents(
    search: Optional[str] = Query(None, description="Search term in title, description, or service"),
    service: Optional[str] = Query(None, description="Filter by service"),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    return incident_service.list_incidents(search=search, service=service, status=status)


@router.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    incident = incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/api/incidents/{incident_id}/feedback")
def save_feedback(incident_id: str, payload: IncidentFeedback):
    try:
        return incident_service.save_feedback(incident_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/incidents/{incident_id}/resolution")
def save_resolution(incident_id: str, payload: IncidentResolution):
    try:
        return incident_service.save_resolution(incident_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/dashboard/summary")
@router.get("/api/dashboard/analytics")
def dashboard_summary():
    return incident_service.dashboard_summary()


# =============================================================================
# Part 4: Guided Incident Response, Action Plan & Timeline Endpoints
# =============================================================================

@router.get("/api/incidents/{incident_id}/actions")
def list_incident_actions(
    incident_id: str,
    status: Optional[str] = Query(None, description="Filter actions by status: pending, in_progress, completed, blocked"),
    category: Optional[str] = Query(None, description="Filter actions by category: read_only, active_validation, mitigation"),
):
    status_val = status if isinstance(status, str) else None
    category_val = category if isinstance(category, str) else None
    try:
        return incident_service.list_actions(incident_id, status=status_val, category=category_val)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/incidents/{incident_id}/actions")
def create_incident_action(incident_id: str, payload: ActionCreate):
    try:
        return incident_service.create_action(incident_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400 if "cannot be empty" in str(exc) else 404, detail=str(exc))


@router.post("/api/incidents/{incident_id}/actions/import-recommendations")
def import_recommended_actions(incident_id: str, payload: Optional[ActionBatchImportRequest] = None):
    actor = payload.actor if payload and payload.actor else "On-call Engineer"
    try:
        return incident_service.import_recommendations_to_actions(incident_id, actor=actor)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/incidents/{incident_id}/actions/summary")
def get_action_plan_summary(incident_id: str):
    try:
        return incident_service.get_action_plan_summary(incident_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/api/incidents/{incident_id}/actions/{action_id}")
def get_incident_action(incident_id: str, action_id: str):
    try:
        return incident_service.get_action(incident_id, action_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/api/incidents/{incident_id}/actions/{action_id}")
def update_incident_action(incident_id: str, action_id: str, payload: ActionUpdate):
    try:
        return incident_service.update_action(incident_id, action_id, payload.model_dump(exclude_unset=True))
    except ValueError as exc:
        msg = str(exc)
        status_code = 400 if "Invalid action status" in msg else 404
        raise HTTPException(status_code=status_code, detail=msg)


@router.get("/api/incidents/{incident_id}/timeline")
def get_incident_timeline(
    incident_id: str,
    limit: int = Query(150, ge=1, le=500, description="Maximum number of chronological events to retrieve"),
):
    limit_val = limit if isinstance(limit, int) else 150
    try:
        return incident_service.get_timeline(incident_id, limit=limit_val)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

