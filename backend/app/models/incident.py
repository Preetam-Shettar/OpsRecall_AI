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


@dataclass
class IncidentActionModel:
    id: str
    incident_id: str
    title: str
    description: str
    category: str
    priority: str
    status: str
    created_at: str
    updated_at: str
    assigned_engineer: str | None = None
    command_hint: str | None = None
    completion_notes: str | None = None
    blocked_reason: str | None = None


@dataclass
class IncidentTimelineEventModel:
    id: int
    incident_id: str
    event_type: str
    description: str
    actor: str
    actor_type: str
    created_at: str
    related_action_id: str | None = None

