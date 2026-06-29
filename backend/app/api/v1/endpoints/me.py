from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.base import get_db
from app.api.deps import get_current_citizen
from app.models import Issue, IssueComment, IssueSupport
from app.schemas.issues import IssueListResponse, IssueWithCommentMeta

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/issues", response_model=List[IssueListResponse])
def get_my_issues(
    limit: int = 50,
    offset: int = 0,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Get all issues reported by the current citizen."""
    issues = (
        db.query(Issue)
        .filter(Issue.user_id == citizen["id"])
        .order_by(Issue.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return issues


@router.get("/comments", response_model=List[IssueWithCommentMeta])
def get_my_commented_issues(
    limit: int = 50,
    offset: int = 0,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Get all issues the current citizen has commented on."""
    from sqlalchemy import func
    
    # Subquery: issues this user commented on, with latest comment date
    commented = (
        db.query(
            IssueComment.issue_id,
            func.max(IssueComment.created_at).label("last_commented_at"),
            func.count(IssueComment.id).label("my_comment_count")
        )
        .filter(IssueComment.user_id == citizen["id"])
        .group_by(IssueComment.issue_id)
        .subquery()
    )
    
    issues = (
        db.query(Issue, commented.c.last_commented_at, commented.c.my_comment_count)
        .join(commented, Issue.id == commented.c.issue_id)
        .order_by(commented.c.last_commented_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    result = []
    for issue, last_commented, comment_count in issues:
        # Build the response manually
        result.append({
            "id": issue.id,
            "category": issue.category,
            "state": issue.state,
            "title": issue.title,
            "geo_lat": float(issue.geo_lat) if issue.geo_lat else 0.0,
            "geo_lng": float(issue.geo_lng) if issue.geo_lng else 0.0,
            "severity": issue.severity,
            "ward_id": issue.ward_id,
            "support_count": issue.support_count,
            "priority_score": int(issue.priority_score) if issue.priority_score else 0,
            "ai_summary": issue.ai_summary,
            "sla_ack_deadline": issue.sla_ack_deadline,
            "sla_resolution_deadline": issue.sla_resolution_deadline,
            "created_at": issue.created_at,
            "last_commented_at": last_commented,
            "my_comment_count": comment_count,
        })
    return result


@router.get("/supports", response_model=List[IssueListResponse])
def get_my_supported_issues(
    limit: int = 50,
    offset: int = 0,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Get all issues the current citizen has supported."""
    issues = (
        db.query(Issue)
        .join(IssueSupport, Issue.id == IssueSupport.issue_id)
        .filter(IssueSupport.user_id == citizen["id"])
        .order_by(IssueSupport.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return issues


def _compute_sla_status(issue) -> str:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if issue.state in ["closed", "resolved_confirmed"]:
        return "Completed"
    if issue.sla_resolution_deadline and issue.sla_resolution_deadline < now:
        return "Overdue"
    if issue.sla_ack_deadline and issue.sla_ack_deadline < now:
        return "Acknowledgement overdue"
    return "On track"