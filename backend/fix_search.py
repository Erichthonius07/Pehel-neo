with open('app/api/v1/endpoints/feed.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add Query import and UUID
old_imports = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.db.base import get_db
from app.api.deps import get_current_citizen'''

new_imports = '''from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.db.base import get_db
from app.api.deps import get_current_citizen
from app.schemas.issues import IssueListResponse'''

content = content.replace(old_imports, new_imports)

# Add search endpoint before the last line
search_endpoint = '''

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
    issues = (
        query.order_by(
            func.case(
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
'''

# Insert before the end of file (after last function)
content = content.rstrip() + search_endpoint + '\n'

with open('app/api/v1/endpoints/feed.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Added search endpoint to feed.py')