from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field


class PossibleCause(BaseModel):
    cause: str
    evidence: list[str] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"] = "medium"


class EvidenceLogExcerpt(BaseModel):
    log_text: str
    signal_matched: Optional[str] = None
    line_number: Optional[int] = None


class AlternativeHypothesis(BaseModel):
    cause: str
    status: Literal["alternative", "less_likely", "ruled_out"] = "alternative"
    ruling_out_rationale: str = ""
    evidence: list[str] = Field(default_factory=list)


class DiagnosticCheck(BaseModel):
    check: str
    check_type: Literal["read_only", "active_validation", "mitigation"] = "read_only"
    command_hint: Optional[str] = None


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

    # Part 3: Explainable AI Investigation Extensions (with backward-compatible defaults)
    primary_cause: Optional[PossibleCause] = None
    reasoning_chain: list[str] = Field(default_factory=list)
    alternative_hypotheses: list[AlternativeHypothesis] = Field(default_factory=list)
    supporting_log_excerpts: list[EvidenceLogExcerpt] = Field(default_factory=list)
    confidence_justification: Optional[str] = None
    structured_checks: list[DiagnosticCheck] = Field(default_factory=list)
