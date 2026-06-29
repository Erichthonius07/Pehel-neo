from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.db.base import get_db
from app.api.deps import get_current_citizen
from app.schemas.issues import IssueListResponse

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

@router.get("/search", response_model=List[IssueListResponse])
def search_issues(
    q: str = Query(..., min_length=2, max_length=100),
    city_id: Optional[UUID] = None,
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Search issues by title, description, location text, or AI summary. Public."""
    from sqlalchemy import or_, func
    from app.models import Issue
    
    search_term = f"%{q}%"
    
    query = db.query(Issue).filter(
        or_(
            Issue.title.ilike(search_term),
            Issue.description.ilike(search_term),
            Issue.location_text.ilike(search_term),
            Issue.ai_summary.ilike(search_term),
        )
    )
    
    if city_id:
        query = query.filter(Issue.city_id == city_id)
    if category:
        query = query.filter(Issue.category == category)
    
    # Sort: exact title match first, then priority
    from sqlalchemy import case
    issues = (
        query.order_by(
            case(
                (Issue.title.ilike(f"{q}%"), 2),
                (Issue.title.ilike(f"%{q}%"), 1),
                else_=0
            ).desc(),
            Issue.priority_score.desc(),
            Issue.created_at.desc(),
        )
        .limit(limit)
        .all()
    )
    
    return issues

@router.get("/nearby", response_model=List[IssueListResponse])
def get_nearby_issues(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_meters: int = Query(1000, ge=100, le=10000),
    category: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Get issues within a radius of given lat/lng. Public."""
    from sqlalchemy import func
    from app.models import Issue
    from math import radians, cos, sin, asin, sqrt
    
    # Rough bounding box filter first (1 degree ~ 111km)
    deg_radius = radius_meters / 111000.0
    min_lat = lat - deg_radius
    max_lat = lat + deg_radius
    min_lng = lng - deg_radius
    max_lng = lng + deg_radius
    
    query = db.query(Issue).filter(
        Issue.geo_lat >= min_lat,
        Issue.geo_lat <= max_lat,
        Issue.geo_lng >= min_lng,
        Issue.geo_lng <= max_lng,
    )
    
    if category:
        query = query.filter(Issue.category == category)
    
    # Exclude closed/resolved
    query = query.filter(Issue.state.notin_(["closed", "resolved_confirmed"]))
    
    issues = query.order_by(Issue.priority_score.desc(), Issue.created_at.desc()).all()
    
    # Haversine distance filter
    def haversine(lat1, lng1, lat2, lng2):
        R = 6371000  # meters
        phi1 = radians(lat1)
        phi2 = radians(lat2)
        dphi = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlng/2)**2
        return 2 * R * asin(sqrt(a))
    
    result = []
    for issue in issues:
        dist = haversine(lat, lng, float(issue.geo_lat), float(issue.geo_lng))
        if dist <= radius_meters:
            result.append(issue)
            if len(result) >= limit:
                break
    
    return result

@router.get("/for-you", response_model=List[IssueListResponse])
def get_personalized_feed(
    limit: int = 20,
    offset: int = 0,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Personalized feed for the current citizen. Auth required."""
    from sqlalchemy import or_, distinct, func
    from app.models import Issue, IssueSupport, IssueComment
    
    # Get user's most recent issue's ward as their "home ward"
    latest_issue = (
        db.query(Issue)
        .filter(Issue.user_id == citizen["id"])
        .order_by(Issue.created_at.desc())
        .first()
    )
    user_ward_id = latest_issue.ward_id if latest_issue else None
    
    # Get categories user has engaged with (supported or commented)
    supported_categories = (
        db.query(distinct(Issue.category))
        .join(IssueSupport, Issue.id == IssueSupport.issue_id)
        .filter(IssueSupport.user_id == citizen["id"])
        .all()
    )
    supported_categories = [c[0] for c in supported_categories if c[0]]
    
    commented_categories = (
        db.query(distinct(Issue.category))
        .join(IssueComment, Issue.id == IssueComment.issue_id)
        .filter(IssueComment.user_id == citizen["id"])
        .all()
    )
    commented_categories = [c[0] for c in commented_categories if c[0]]
    
    engaged_categories = list(set(supported_categories + commented_categories))
    
    # Build query
    conditions = []
    if user_ward_id:
        conditions.append(Issue.ward_id == user_ward_id)
    if engaged_categories:
        conditions.append(Issue.category.in_(engaged_categories))
    
    if not conditions:
        # Fallback: just return trending open issues
        return (
            db.query(Issue)
            .filter(Issue.state.notin_(["closed", "resolved_confirmed"]))
            .order_by(Issue.priority_score.desc(), Issue.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    query = db.query(Issue).filter(or_(*conditions))
    
    # Exclude issues user already reported
    query = query.filter(Issue.user_id != citizen["id"])
    
    # Exclude resolved/closed issues older than 30 days
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    query = query.filter(
        or_(
            Issue.state.notin_(["resolved_confirmed", "closed"]),
            Issue.updated_at > cutoff,
        )
    )
    
    issues = (
        query.order_by(Issue.priority_score.desc(), Issue.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return issues

