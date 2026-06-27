from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime

class IssueCreateRequest(BaseModel):
    category: str = Field(..., pattern=r"^(roads|water|garbage)$")
    ward_id: UUID
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    geo_lat: float = Field(..., ge=-90, le=90)
    geo_lng: float = Field(..., ge=-180, le=180)
    location_text: Optional[str] = None
    severity: Optional[str] = Field(default="medium", pattern=r"^(low|medium|high|critical)$")
    is_safety_risk: bool = False

class IssueResponse(BaseModel):
    id: UUID
    category: str
    state: str
    title: str
    description: str
    geo_lat: float
    geo_lng: float
    location_text: Optional[str] = None
    severity: str
    ward_id: UUID
    city_id: UUID
    user_id: UUID
    sla_ack_deadline: Optional[datetime] = None
    sla_visit_deadline: Optional[datetime] = None
    sla_resolution_deadline: Optional[datetime] = None
    time_decay_window_ends_at: Optional[datetime] = None
    priority_score: int = 0
    support_count: int = 0
    is_safety_risk: bool = False
    confidence_ai: float = 0.0
    confidence_community: float = 100.0
    confidence_time: float = 0.0
    net_confidence: float = 0.0
    created_at: datetime

    class Config:
        from_attributes = True

class IssueListResponse(BaseModel):
    id: UUID
    category: str
    state: str
    title: str
    geo_lat: float
    geo_lng: float
    severity: str
    ward_id: UUID
    support_count: int = 0
    created_at: datetime

    class Config:
        from_attributes = True

class TimelineEventResponse(BaseModel):
    id: UUID
    issue_id: UUID
    event_type: str
    new_state: Optional[str] = None
    old_state: Optional[str] = None
    actor_type: str
    actor_id: Optional[UUID] = None
    description: Optional[str] = None
    sequence_number: int
    created_at: datetime

    class Config:
        from_attributes = True

class TimelineListResponse(BaseModel):
    issue_id: UUID
    events: List[TimelineEventResponse]
    total: int
