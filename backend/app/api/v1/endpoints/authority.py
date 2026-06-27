from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.base import get_db
from app.api.deps import get_current_authority

router = APIRouter(prefix="/authority", tags=["authority"])


@router.get("/me")
def get_current_authority_user(
    authority: dict = Depends(get_current_authority),
):
    """Get current authority user profile."""
    return {
        "id": authority["id"],
        "email": authority["email"],
        "name": authority["name"],
        "role": authority["role"],
        "authority_id": authority.get("authority_id"),
    }


@router.get("/dashboard")
def get_authority_dashboard(
    authority: dict = Depends(get_current_authority),
    db: Session = Depends(get_db),
):
    """Get authority dashboard stats."""
    from app.models import Issue
    
    authority_id = authority.get("authority_id")
    
    # Issues assigned to this authority's wards
    total_issues = db.query(Issue).filter(
        Issue.ward_id.in_(
            db.query(Ward.id).filter(Ward.authority_id == authority_id)
        )
    ).count() if authority_id else 0
    
    open_issues = db.query(Issue).filter(
        Issue.state.notin_(["closed", "resolved_confirmed"]),
    ).count()
    
    overdue_issues = db.query(Issue).filter(
        Issue.state.notin_(["closed", "resolved_confirmed"]),
        Issue.sla_resolution_deadline < datetime.utcnow(),
    ).count()
    
    return {
        "total_issues": total_issues,
        "open_issues": open_issues,
        "overdue_issues": overdue_issues,
    }