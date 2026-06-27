from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.base import get_db
from app.api.deps import get_current_citizen

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("/")
def get_feed(
    ward_id: Optional[UUID] = None,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Public feed of issues. No auth required."""
    from app.services.issue_service import list_issues
    
    return list_issues(db, ward_id=ward_id, category=category, limit=limit, offset=offset)


@router.get("/trending")
def get_trending(
    ward_id: Optional[UUID] = None,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Trending issues by support count. No auth required."""
    from app.models import Issue
    
    query = db.query(Issue).filter(Issue.state.notin_(["closed", "resolved_confirmed"]))
    if ward_id:
        query = query.filter(Issue.ward_id == ward_id)
    
    issues = query.order_by(Issue.support_count.desc()).limit(limit).offset(0).all()
    
    return [
        {
            "id": str(i.id),
            "title": i.title,
            "category": i.category,
            "severity": i.severity,
            "state": i.state,
            "support_count": i.support_count,
            "priority_score": i.priority_score,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in issues
    ]