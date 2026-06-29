with open('app/api/v1/endpoints/feed.py', 'r', encoding='utf-8') as f:
    content = f.read()

for_you_endpoint = '''

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
'''

content = content.rstrip() + for_you_endpoint + '\n'

with open('app/api/v1/endpoints/feed.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Added for-you endpoint to feed.py')