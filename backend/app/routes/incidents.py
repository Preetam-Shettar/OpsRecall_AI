from fastapi import APIRouter, HTTPException

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
def list_incidents():
    return incident_service.list_incidents()


@router.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    incident = incident_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    return incident


@router.post("/api/incidents/{incident_id}/feedback")
def save_feedback(incident_id: str, payload: IncidentFeedback):
    return incident_service.save_feedback(incident_id, payload.model_dump())


@router.post("/api/incidents/{incident_id}/resolution")
def save_resolution(incident_id: str, payload: IncidentResolution):
    return incident_service.save_resolution(incident_id, payload.model_dump())


@router.get("/api/dashboard/summary")
def dashboard_summary():
    return incident_service.dashboard_summary()
