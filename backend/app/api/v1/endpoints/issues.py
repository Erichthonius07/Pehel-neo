# Issue endpoints for Pehel Neo
from fastapi import BackgroundTasks
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
from app.agents.resolution_validator import run_resolution_validator

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
    background_tasks: BackgroundTasks,
    authority: dict = Depends(get_current_authority),
    db: Session = Depends(get_db),
):
    """Authority claims resolution. Triggers Resolution Validator in background."""
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

    # Trigger Resolution Validator in background
    background_tasks.add_task(run_resolution_validator, issue.id)

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

@router.post("/{issue_id}/narrative")
def get_narrative(
    issue_id: UUID,
    db: Session = Depends(get_db),
):
    """Generate narrative summary for an issue. Public — no auth required."""
    from app.agents.narrative_agent import run_narrative_agent
    result = run_narrative_agent(issue_id)
    return result

@router.post("/{issue_id}/media/upload-url")
def get_media_upload_url(
    issue_id: UUID,
    media_type: str = "complaint_photo",
    content_type: str = "image/jpeg",
    citizen: dict = Depends(get_current_citizen),
):
    """Get presigned URL for media upload.
    
    media_type: complaint_photo | resolution_photo | visit_photo | audio
    content_type: image/jpeg | image/png | audio/mpeg
    """
    from app.services.storage_service import generate_upload_url
    return generate_upload_url(issue_id, media_type, content_type)


@router.post("/{issue_id}/media/confirm")
def confirm_media_upload(
    issue_id: UUID,
    s3_key: str,
    media_type: str = "complaint_photo",
    geo_lat: Optional[float] = None,
    geo_lng: Optional[float] = None,
    background_tasks: BackgroundTasks = None,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Confirm media upload and create IssueMedia record.
    
    If media_type == resolution_photo, re-triggers Resolution Validator.
    """
    from app.models import IssueMedia
    from app.services.storage_service import _get_bucket_name
    from app.core.config import get_settings
    from app.agents.resolution_validator import run_resolution_validator
    
    settings = get_settings()
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")
    
    # Verify citizen is reporter or supporter
    from app.services.issue_service import can_citizen_act_on_resolution
    if not can_citizen_act_on_resolution(db, issue_id, citizen["id"]):
        raise HTTPException(status_code=403, detail="Not authorized for this issue")
    
    # Create IssueMedia record
    media = IssueMedia(
        issue_id=issue_id,
        media_type=media_type,
        s3_key=s3_key,
        s3_bucket=_get_bucket_name(),
        geo_lat=geo_lat,
        geo_lng=geo_lng,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    
    # If resolution photo, re-trigger Resolution Validator in background
    if media_type == "resolution_photo" and background_tasks:
        # Mark existing validation as stale
        db.query(AgentLog).filter(
            AgentLog.issue_id == issue_id,
            AgentLog.action == "resolution_validated"
        ).delete()
        db.commit()
        # Re-run validator
        background_tasks.add_task(run_resolution_validator, issue_id)
    
    return {
        "id": str(media.id),
        "issue_id": str(media.issue_id),
        "media_type": media.media_type,
        "s3_key": media.s3_key,
        "public_url": f"{settings.MINIO_ENDPOINT or 'http://localhost:9000'}/{media.s3_bucket}/{media.s3_key}",
        "created_at": media.created_at.isoformat() if media.created_at else None,
    }

