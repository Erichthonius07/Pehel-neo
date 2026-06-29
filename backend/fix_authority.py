with open('app/api/v1/endpoints/authority.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.base import get_db
from app.api.deps import get_current_authority'''

new = '''from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from uuid import UUID

from app.db.base import get_db
from app.api.deps import get_current_authority
from app.models import Issue, Ward, Authority'''

content = content.replace(old, new)

# Fix the dashboard query
old_query = '''    # Issues assigned to this authority's wards
    total_issues = db.query(Issue).filter(
        Issue.ward_id.in_(
            db.query(Ward.id).filter(Ward.authority_id == authority_id)
        )
    ).count() if authority_id else 0'''

new_query = '''    # Issues assigned to this authority's city wards
    total_issues = 0
    if authority_id:
        authority = db.query(Authority).filter(Authority.id == authority_id).first()
        if authority and authority.city_id:
            total_issues = db.query(Issue).filter(
                Issue.ward_id.in_(
                    db.query(Ward.id).filter(Ward.city_id == authority.city_id)
                )
            ).count()'''

content = content.replace(old_query, new_query)

with open('app/api/v1/endpoints/authority.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed authority.py')