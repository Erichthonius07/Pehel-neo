with open('app/schemas/issues.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add IssueWithCommentMeta after IssueListResponse
old_block = '''class TimelineEventResponse(BaseModel):'''

new_block = '''class IssueWithCommentMeta(IssueListResponse):
    last_commented_at: datetime
    my_comment_count: int

    class Config:
        from_attributes = True


class TimelineEventResponse(BaseModel):'''

content = content.replace(old_block, new_block)

with open('app/schemas/issues.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Added IssueWithCommentMeta schema')