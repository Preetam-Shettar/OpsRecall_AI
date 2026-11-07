from dataclasses import dataclass
from typing import Any


@dataclass
class Incident:
    id: str
    title: str
    service: str
    environment: str
    description: str
    logs: str
    sanitized_logs: str
    status: str
    created_at: str
    updated_at: str
    analysis: dict[str, Any] | None = None
    feedback: dict[str, Any] | None = None
    resolution: dict[str, Any] | None = None
    metadata: dict[str, Any] | None = None


@dataclass
class IncidentAnalysisModel:
    id: str
    incident_id: str
    summary: str
    possible_causes: list[dict[str, Any]]
    recommendations: list[str]
    confidence: str
    created_at: str


@dataclass
class IncidentResolutionModel:
    id: str
    incident_id: str
    confirmed_root_cause: str
    resolution_steps: str
    outcome: str
    verified_by_user: bool
    created_at: str
    engineer: str | None = None
