from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field

from app.schemas.analysis import (
    IncidentAnalysis,
    PossibleCause,
    RelatedMemoryInsight,
)


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    service: str = Field(..., min_length=2, max_length=100)
    environment: str = Field(default="staging", min_length=2, max_length=50)
    severity: str | None = Field(default=None, max_length=50)
    description: str = Field(..., min_length=5, max_length=2000)
    logs: str = Field(default="", max_length=50000)
    deployment_context: str | None = Field(default=None, max_length=500)
    incident_timestamp: str | None = Field(default=None, max_length=50)


class IncidentFeedback(BaseModel):
    helpful: bool
    notes: str | None = Field(default=None, max_length=2000)


class IncidentResolution(BaseModel):
    root_cause: str = Field(..., min_length=2, max_length=2000)
    resolution: str = Field(..., min_length=2, max_length=2000)
    outcome: Literal["resolved", "mitigated", "unresolved"] = "resolved"
    verified: bool = True
    engineer: str | None = Field(default=None, max_length=100)


class IncidentMemoryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)
    budget: str = Field(default="mid", max_length=20)


class MemoryItem(BaseModel):
    id: int
    incident_id: str
    title: str
    service: str
    environment: str
    severity: str
    root_cause: str
    resolution: str
    outcome: str
    verified: bool
    engineer: str | None = None
    created_at: str
    storage_provider: str
    bank_id: str
    recall_count: int = 0
    has_parent_incident: bool = True


class MemoryDetail(MemoryItem):
    content: str
    context: str | None = None
    evidence_logs: str | None = None
    symptoms: str | None = None
    related_incident_ids: list[str] = Field(default_factory=list)
    recalled_in_incidents: list[dict[str, Any]] = Field(default_factory=list)


class MemoryListResponse(BaseModel):
    items: list[MemoryItem]
    total: int
    page: int
    page_size: int
    total_pages: int
    verified_only: bool


class IncidentResponse(BaseModel):
    incident_id: str
    status: str
    analysis: IncidentAnalysis | dict[str, Any]
    related_memories: list[dict[str, Any]] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
