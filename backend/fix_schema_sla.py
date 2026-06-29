with open('app/schemas/issues.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add SLA fields to IssueListResponse
old = '''    support_count: int = 0
    priority_score: int = 0
    ai_summary: Optional[str] = None
    created_at: datetime'''

new = '''    support_count: int = 0
    priority_score: int = 0
    ai_summary: Optional[str] = None
    sla_ack_deadline: Optional[datetime] = None
    sla_resolution_deadline: Optional[datetime] = None
    created_at: datetime'''

content = content.replace(old, new)

with open('app/schemas/issues.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Added SLA fields to IssueListResponse')