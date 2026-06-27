from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.api.deps import get_current_authority

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(authority: dict = Depends(get_current_authority)):
    """Require admin role."""
    if authority.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return authority


@router.get("/stats")
def get_admin_stats(
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get platform-wide stats. Admin only."""
    from app.models import Issue, User, Authority
    
    total_issues = db.query(Issue).count()
    total_users = db.query(User).count()
    total_authorities = db.query(Authority).count()
    
    open_issues = db.query(Issue).filter(
        Issue.state.notin_(["closed", "resolved_confirmed"]),
    ).count()
    
    return {
        "total_issues": total_issues,
        "open_issues": open_issues,
        "total_users": total_users,
        "total_authorities": total_authorities,
    }


@router.post("/disputes/{issue_id}/dismiss")
def dismiss_dispute(
    issue_id: str,
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin dismisses a dispute. Moves issue to resolved_confirmed."""
    from app.services.issue_service import transition_issue_state
    from uuid import UUID
    
    try:
        issue = transition_issue_state(
            db,
            UUID(issue_id),
            admin["id"],
            "resolved_confirmed",
            actor_type="admin",
            description="Dispute dismissed by admin",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return issue
@router.post("/agents/pattern")
def trigger_pattern_agent(
    admin: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Manually trigger Pattern Intelligence Agent. Admin only."""
    from app.agents.pattern_agent import run_pattern_agent
    
    result = run_pattern_agent()
    
    return {
        "clusters_generated": result.get("clusters_generated", 0),
        "wards_analyzed": result.get("wards_analyzed", 0),
        "combinations_checked": result.get("combinations_checked", 0),
        "errors": result.get("errors", []),
    }
