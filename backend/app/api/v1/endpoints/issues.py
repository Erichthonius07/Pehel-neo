# Issue endpoints for Pehel Neo
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.db.base import get_db
from app.api.deps import get_current_citizen, get_current_authority
from app.services.issue_service import (
    create_issue, get_issue_by_id, list_issues, get_issue_timeline,
    transition_issue_state, can_citizen_act_on_resolution,
    add_issue_support,
)
from app.schemas.issues import IssueCreateRequest, IssueResponse, IssueListResponse, TimelineListResponse
from app.agents.intake_agent import run_intake_agent

router = APIRouter(prefix="/issues", tags=["issues"])


@router.post("", response_model=IssueResponse, status_code=status.HTTP_201_CREATED)
def submit_issue(
    request: IssueCreateRequest,
    background_tasks: BackgroundTasks,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Submit a new civic issue. Citizen auth required."""
    try:
        issue = create_issue(
            db=db,
            user_id=citizen["id"],
            category=request.category,
            ward_id=request.ward_id,
            title=request.title,
            description=request.description,
            geo_lat=request.geo_lat,
            geo_lng=request.geo_lng,
            location_text=request.location_text,
            severity=request.severity,
            is_safety_risk=request.is_safety_risk,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Trigger Intake Agent in background
    background_tasks.add_task(run_intake_agent, issue.id)

    return issue


@router.get("", response_model=List[IssueListResponse])
def list_public_issues(
    ward_id: Optional[UUID] = None,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List public issues (no auth required)."""
    return list_issues(db, ward_id=ward_id, category=category, limit=limit, offset=offset)


@router.get("/{issue_id}", response_model=IssueResponse)
def get_issue(
    issue_id: UUID,
    db: Session = Depends(get_db),
):
    """Get single issue by ID (public)."""
    issue = get_issue_by_id(db, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )
    return issue


@router.get("/{issue_id}/timeline", response_model=TimelineListResponse)
def get_timeline(
    issue_id: UUID,
    db: Session = Depends(get_db),
):
    """Get audit timeline for an issue (public)."""
    issue = get_issue_by_id(db, issue_id)
    if not issue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Issue not found",
        )
    events = get_issue_timeline(db, issue_id)
    return TimelineListResponse(
        issue_id=issue_id,
        events=events,
        total=len(events),
    )


# Authority state transitions
@router.post("/{issue_id}/acknowledge", response_model=IssueResponse)
def acknowledge_issue(
    issue_id: UUID,
    authority: dict = Depends(get_current_authority),
    db: Session = Depends(get_db),
):
    """Authority acknowledges a reported issue."""
    try:
        issue = transition_issue_state(
            db, issue_id, authority["id"], "acknowledged",
            actor_type="authority",
            description="Issue acknowledged by authority",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return issue


@router.post("/{issue_id}/visit", response_model=IssueResponse)
def visit_issue(
    issue_id: UUID,
    authority: dict = Depends(get_current_authority),
    db: Session = Depends(get_db),
):
    """Authority marks issue as visited."""
    try:
        issue = transition_issue_state(
            db, issue_id, authority["id"], "visited",
            actor_type="authority",
            description="Site visit completed by authority",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return issue


@router.post("/{issue_id}/start-work", response_model=IssueResponse)
def start_work(
    issue_id: UUID,
    authority: dict = Depends(get_current_authority),
    db: Session = Depends(get_db),
):
    """Authority starts work on issue."""
    try:
        issue = transition_issue_state(
            db, issue_id, authority["id"], "in_progress",
            actor_type="authority",
            description="Work started by authority",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return issue


@router.post("/{issue_id}/resolve", response_model=IssueResponse)
def resolve_issue(
    issue_id: UUID,
    authority: dict = Depends(get_current_authority),
    db: Session = Depends(get_db),
):
    """Authority claims resolution."""
    try:
        issue = transition_issue_state(
            db, issue_id, authority["id"], "resolved_claimed",
            actor_type="authority",
            description="Resolution claimed by authority",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return issue


# Citizen resolution response endpoints
@router.post("/{issue_id}/confirm", response_model=IssueResponse)
def confirm_resolution(
    issue_id: UUID,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Citizen confirms resolution was done properly."""
    if not can_citizen_act_on_resolution(db, issue_id, citizen["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the reporter or supporters can confirm resolution",
        )
    try:
        issue = transition_issue_state(
            db, issue_id, citizen["id"], "resolved_confirmed",
            actor_type="citizen",
            description="Resolution confirmed by citizen",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return issue


@router.post("/{issue_id}/dispute", response_model=IssueResponse)
def dispute_resolution(
    issue_id: UUID,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Citizen disputes resolution."""
    if not can_citizen_act_on_resolution(db, issue_id, citizen["id"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the reporter or supporters can dispute resolution",
        )
    try:
        issue = transition_issue_state(
            db, issue_id, citizen["id"], "disputed",
            actor_type="citizen",
            description="Resolution disputed by citizen",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return issue

@router.post("/{issue_id}/support", response_model=IssueResponse)
def support_issue(
    issue_id: UUID,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Add support/upvote to an issue. Citizen auth required."""
    try:
        issue = add_issue_support(db, issue_id, citizen["id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return issue