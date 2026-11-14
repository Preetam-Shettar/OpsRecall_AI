from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

ActionCategory = Literal["read_only", "active_validation", "mitigation"]
ActionStatus = Literal["pending", "in_progress", "completed", "blocked"]
ActionPriority = Literal["low", "medium", "high", "critical"]
ActorType = Literal["ai", "engineer", "system"]


class ActionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(default="", max_length=2000)
    category: ActionCategory = "read_only"
    priority: ActionPriority = "medium"
    assigned_engineer: Optional[str] = Field(default=None, max_length=100)
    command_hint: Optional[str] = Field(default=None, max_length=500)
    actor: Optional[str] = Field(default="On-call Engineer", max_length=100)


class ActionUpdate(BaseModel):
    status: Optional[ActionStatus] = None
    assigned_engineer: Optional[str] = Field(default=None, max_length=100)
    priority: Optional[ActionPriority] = None
    completion_notes: Optional[str] = Field(default=None, max_length=3000)
    blocked_reason: Optional[str] = Field(default=None, max_length=1000)
    actor: Optional[str] = Field(default=None, max_length=100)


class ActionResponse(BaseModel):
    id: str
    incident_id: str
    title: str
    description: str
    category: ActionCategory
    priority: ActionPriority
    status: ActionStatus
    assigned_engineer: Optional[str] = None
    command_hint: Optional[str] = None
    completion_notes: Optional[str] = None
    blocked_reason: Optional[str] = None
    created_at: str
    updated_at: str


class TimelineEventResponse(BaseModel):
    id: int
    incident_id: str
    event_type: str
    description: str
    actor: str
    actor_type: ActorType
    related_action_id: Optional[str] = None
    created_at: str


class ActionBatchImportRequest(BaseModel):
    actor: Optional[str] = Field(default="On-call Engineer", max_length=100)


class IncidentActionPlanSummary(BaseModel):
    incident_id: str
    total_actions: int = 0
    completed_actions: int = 0
    in_progress_actions: int = 0
    pending_actions: int = 0
    blocked_actions: int = 0
    progress_pct: int = 0
    actions: list[ActionResponse] = Field(default_factory=list)
