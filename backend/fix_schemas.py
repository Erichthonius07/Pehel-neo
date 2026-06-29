with open('app/schemas/issues.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add computed_field import
content = content.replace(
    'from pydantic import BaseModel, Field',
    'from pydantic import BaseModel, Field, computed_field'
)

# 2. Add ai_summary to IssueResponse
content = content.replace(
    '    net_confidence: float = 0.0\n    created_at: datetime',
    '    net_confidence: float = 0.0\n    ai_summary: Optional[str] = None\n    created_at: datetime'
)

# 3. Add sla_status computed field to IssueResponse (before Config)
content = content.replace(
    '    created_at: datetime\n\n    class Config:\n        from_attributes = True\n\nclass IssueListResponse',
    '''    created_at: datetime

    @computed_field
    @property
    def sla_status(self) -> str:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.state in ["closed", "resolved_confirmed"]:
            return "Completed"
        if self.sla_resolution_deadline and self.sla_resolution_deadline < now:
            return "Overdue"
        if self.sla_ack_deadline and self.sla_ack_deadline < now:
            return "Acknowledgement overdue"
        return "On track"

    class Config:
        from_attributes = True

class IssueListResponse'''
)

# 4. Add ai_summary and priority_score to IssueListResponse
content = content.replace(
    '    support_count: int = 0\n    created_at: datetime',
    '    support_count: int = 0\n    priority_score: int = 0\n    ai_summary: Optional[str] = None\n    created_at: datetime'
)

# 5. Add sla_status computed field to IssueListResponse (before Config)
content = content.replace(
    '    created_at: datetime\n\n    class Config:\n        from_attributes = True\n\nclass TimelineEventResponse',
    '''    created_at: datetime

    @computed_field
    @property
    def sla_status(self) -> str:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if self.state in ["closed", "resolved_confirmed"]:
            return "Completed"
        if self.sla_resolution_deadline and self.sla_resolution_deadline < now:
            return "Overdue"
        if self.sla_ack_deadline and self.sla_ack_deadline < now:
            return "Acknowledgement overdue"
        return "On track"

    class Config:
        from_attributes = True

class TimelineEventResponse'''
)

with open('app/schemas/issues.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed schemas/issues.py')