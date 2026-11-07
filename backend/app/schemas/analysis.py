from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class PossibleCause(BaseModel):
    cause: str
    evidence: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"


class RelatedMemoryInsight(BaseModel):
    incident_id: str
    lesson: str


class IncidentAnalysis(BaseModel):
    summary: str
    symptoms: list[str] = Field(default_factory=list)
    possible_causes: list[PossibleCause]
    supporting_evidence: list[str] = Field(default_factory=list)
    related_memory_insights: list[RelatedMemoryInsight] = Field(default_factory=list)
    recommended_checks: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"
    safety_notes: list[str] = Field(default_factory=list)
    analysis_source: Literal["groq", "local", "local_fallback"] = "local"
    analysis_notice: str | None = None
