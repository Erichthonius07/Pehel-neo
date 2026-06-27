"""Issue service with state machine and SLA logic."""
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models import Issue, IssueTimeline, Ward, City, User
from app.core.constants import IssueState, IssueCategory
from app.models import Issue, IssueTimeline, Ward, City, User, IssueSupporter

# SLA config: (ack_hours, visit_hours, resolution_hours, time_decay_days)
SLA_CONFIG = {
    "roads": (4, 48, 240, 30),
    "water": (2, 24, 120, 14),
    "garbage": (4, 24, 48, 7),
}


def calculate_sla_deadlines(category: str, now: datetime) -> Tuple[datetime, datetime, datetime, datetime]:
    """Calculate SLA deadlines based on category."""
    ack_h, visit_h, res_h, decay_days = SLA_CONFIG[category]
    
    ack_deadline = now + timedelta(hours=ack_h)
    visit_deadline = now + timedelta(hours=visit_h)
    resolution_deadline = now + timedelta(hours=res_h)
    time_decay = now + timedelta(days=decay_days)
    
    return ack_deadline, visit_deadline, resolution_deadline, time_decay


def create_issue(
    db: Session,
    user_id: UUID,
    category: str,
    ward_id: UUID,
    title: str,
    description: str,
    geo_lat: float,
    geo_lng: float,
    location_text: Optional[str],
    severity: str,
    is_safety_risk: bool,
) -> Issue:
    """Create a new issue with SLA deadlines and initial timeline event."""
    now = datetime.utcnow()
    
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    if not ward:
        raise ValueError("Ward not found")
    
    ack_dl, visit_dl, res_dl, time_decay = calculate_sla_deadlines(category, now)
    
    issue = Issue(
        id=uuid4(),
        user_id=user_id,
        ward_id=ward_id,
        city_id=ward.city_id,
        category=category,
        state=IssueState.REPORTED.value,
        title=title,
        description=description,
        geo_lat=geo_lat,
        geo_lng=geo_lng,
        location_text=location_text,
        severity=severity,
        is_safety_risk=is_safety_risk,
        priority_score=0,
        support_count=0,
        confidence_ai=0.0,
        confidence_community=100.0,
        confidence_time=0.0,
        net_confidence=0.0,
        sla_ack_deadline=ack_dl,
        sla_visit_deadline=visit_dl,
        sla_resolution_deadline=res_dl,
        time_decay_window_ends_at=time_decay,
        is_repeat_failure=False,
        repeat_count=0,
    )
    db.add(issue)
    db.flush()
    
    timeline_event = IssueTimeline(
        issue_id=issue.id,
        event_type="state_change",
        new_state=IssueState.REPORTED.value,
        actor_type="citizen",
        description="Issue reported by citizen",
    )
    db.add(timeline_event)
    db.commit()
    
    db.execute(
        text("UPDATE issues SET location = ST_SetSRID(ST_MakePoint(:lng, :lat), 4326) WHERE id = :id"),
        {"lng": geo_lng, "lat": geo_lat, "id": str(issue.id)}
    )
    db.commit()
    db.refresh(issue)
    
    return issue


def get_issue_by_id(db: Session, issue_id: UUID) -> Optional[Issue]:
    return db.query(Issue).filter(Issue.id == issue_id).first()


def list_issues(db: Session, ward_id: Optional[UUID] = None, category: Optional[str] = None, limit: int = 20, offset: int = 0):
    query = db.query(Issue).order_by(Issue.created_at.desc())
    if ward_id:
        query = query.filter(Issue.ward_id == ward_id)
    if category:
        query = query.filter(Issue.category == category)
    return query.offset(offset).limit(limit).all()


def get_issue_timeline(db: Session, issue_id: UUID):
    return db.query(IssueTimeline).filter(
        IssueTimeline.issue_id == issue_id
    ).order_by(IssueTimeline.sequence_number.asc()).all()


def can_citizen_act_on_resolution(db: Session, issue_id: UUID, user_id: UUID) -> bool:
    """Check if citizen is the reporter or a supporter of the issue."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        return False

    # Reporter can always act
    if issue.user_id == user_id:
        return True

    # Supporters can act
    supporter = db.query(IssueSupporter).filter(
        IssueSupporter.issue_id == issue_id,
        IssueSupporter.user_id == user_id
    ).first()
    return supporter is not None


def add_issue_support(db: Session, issue_id: UUID, user_id: UUID) -> Issue:
    """Add citizen support to an issue. Raises ValueError on business rule violations."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise ValueError("Issue not found")

    # Reporter cannot support their own issue
    if issue.user_id == user_id:
        raise ValueError("Reporter cannot support their own issue")

    # Check if already supported
    existing = db.query(IssueSupporter).filter(
        IssueSupporter.issue_id == issue_id,
        IssueSupporter.user_id == user_id
    ).first()
    if existing:
        raise ValueError("Already supported this issue")

    # Add support record
    supporter = IssueSupporter(issue_id=issue_id, user_id=user_id)
    db.add(supporter)

    # Increment counter
    issue.support_count += 1

    # Timeline event
    timeline = IssueTimeline(
        issue_id=issue_id,
        event_type="support_added",
        actor_type="citizen",
        actor_id=user_id,
        description="Citizen added support to issue",
    )
    db.add(timeline)

    db.commit()
    db.refresh(issue)
    return issue


# Full state machine per Pehel Neo spec
VALID_TRANSITIONS = {
    "reported": ["acknowledged"],
    "acknowledged": ["visited"],
    "visited": ["in_progress"],
    "in_progress": ["resolved_claimed"],
    "resolved_claimed": ["resolved_confirmed", "disputed", "resolution_unverified"],
    "disputed": ["reopened", "resolved_confirmed"],
    "reopened": ["acknowledged"],
    "resolved_confirmed": ["closed"],
    "resolution_unverified": ["closed"],
}


def transition_issue_state(
    db: Session,
    issue_id: UUID,
    actor_id: UUID,
    new_state: str,
    actor_type: str = "authority",
    description: str = None,
) -> Issue:
    """Transition issue state with full validation."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise ValueError("Issue not found")

    current = issue.state
    allowed_next = VALID_TRANSITIONS.get(current, [])
    
    if new_state not in allowed_next:
        raise ValueError(f"Invalid transition: {current} -> {new_state}. Allowed: {allowed_next}")

    if current == "resolved_claimed":
        if new_state in ("resolved_confirmed", "disputed") and actor_type != "citizen":
            raise ValueError("Only citizens can confirm or dispute resolution")
        if new_state == "resolution_unverified" and actor_type != "system":
            raise ValueError("Only system can mark resolution_unverified")
    
    if new_state == "closed" and actor_type != "admin":
        raise ValueError("Only admin can close issues")
    
    if current == "disputed" and new_state == "resolved_confirmed" and actor_type != "admin":
        raise ValueError("Only admin can dismiss a dispute")

    old_state = issue.state
    issue.state = new_state
    issue.updated_at = datetime.utcnow()

    timeline = IssueTimeline(
        issue_id=issue.id,
        event_type="state_change",
        old_state=old_state,
        new_state=new_state,
        actor_type=actor_type,
        actor_id=actor_id,
        description=description or f"State changed from {old_state} to {new_state}",
    )
    db.add(timeline)
    db.commit()
    db.refresh(issue)
    return issue