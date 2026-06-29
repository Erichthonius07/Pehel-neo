from pydantic import BaseModel, Field, computed_field
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
    ai_summary: Optional[str] = None
    created_at: datetime

    @computed_field
    @property
    def sla_status(self) -> str:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.state in ["closed", "resolved_confirmed"]:
            return "Completed"
        if self.sla_resolution_deadline and self.sla_resolution_deadline < now:
            return "Overdue"
        if self.sla_ack_deadline and self.sla_ack_deadline < now:
            return "Acknowledgement overdue"
        return "On track"

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
    priority_score: int = 0
    ai_summary: Optional[str] = None
    sla_ack_deadline: Optional[datetime] = None
    sla_resolution_deadline: Optional[datetime] = None
    created_at: datetime

    @computed_field
    @property
    def sla_status(self) -> str:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.state in ["closed", "resolved_confirmed"]:
            return "Completed"
        if self.sla_resolution_deadline and self.sla_resolution_deadline < now:
            return "Overdue"
        if self.sla_ack_deadline and self.sla_ack_deadline < now:
            return "Acknowledgement overdue"
        return "On track"

    class Config:
        from_attributes = True

class IssueWithCommentMeta(IssueListResponse):
    last_commented_at: datetime
    my_comment_count: int

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
