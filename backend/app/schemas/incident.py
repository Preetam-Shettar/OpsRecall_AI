from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PossibleCause(BaseModel):
    cause: str
    evidence: list[str]
    confidence: Literal["low", "medium", "high"]


class RelatedMemoryInsight(BaseModel):
    incident_id: str
    lesson: str


class IncidentAnalysis(BaseModel):
    summary: str
    symptoms: list[str]
    possible_causes: list[PossibleCause]
    supporting_evidence: list[str]
    related_memory_insights: list[RelatedMemoryInsight]
    recommended_checks: list[str]
    missing_information: list[str]
    confidence: Literal["low", "medium", "high"]
    safety_notes: list[str]
    analysis_source: Literal["groq", "local", "local_fallback"] = "local"
    analysis_notice: str | None = None


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    service: str = Field(..., min_length=2, max_length=100)
    environment: str = Field(default="staging", min_length=2, max_length=50)
    description: str = Field(..., min_length=10, max_length=2000)
    logs: str = Field(default="", max_length=20000)
    deployment_context: str | None = Field(default=None, max_length=500)
    incident_timestamp: str | None = Field(default=None, max_length=50)


class IncidentFeedback(BaseModel):
    helpful: bool
    notes: str | None = Field(default=None, max_length=2000)


class IncidentResolution(BaseModel):
    root_cause: str = Field(..., min_length=2, max_length=2000)
    resolution: str = Field(..., min_length=2, max_length=2000)
    verified: bool = True
    engineer: str | None = Field(default=None, max_length=100)


class IncidentMemoryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=2000)
