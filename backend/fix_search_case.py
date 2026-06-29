with open('app/api/v1/endpoints/feed.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix func.case to case()
old = '''    issues = (
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
    )'''

new = '''    from sqlalchemy import case
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
    )'''

content = content.replace(old, new)

with open('app/api/v1/endpoints/feed.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed search case syntax')