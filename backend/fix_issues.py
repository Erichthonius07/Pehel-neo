with open('app/api/v1/endpoints/issues.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "Narrative generation started" return
narrative_return_idx = None
for i, line in enumerate(lines):
    if 'Narrative generation started' in line:
        narrative_return_idx = i
        break

# Find the line with confirm_media_upload
confirm_idx = None
for i, line in enumerate(lines):
    if '@router.post("/{issue_id}/media/confirm")' in line:
        confirm_idx = i
        break

if narrative_return_idx is None or confirm_idx is None:
    print(f"ERROR: narrative={narrative_return_idx}, confirm={confirm_idx}")
    exit(1)

# Build new content: keep lines up to and including narrative return, 
# then one blank line, then the new upload endpoint, then confirm
new_lines = lines[:narrative_return_idx+1]
new_lines.append('\n')

# Add the missing get_media_upload_url endpoint
upload_endpoint = '''@router.post("/{issue_id}/media/upload-url")
def get_media_upload_url(
    issue_id: UUID,
    media_type: str = "complaint_photo",
    content_type: str = "image/jpeg",
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Get presigned URL for media upload."""
    from app.services.storage_service import generate_upload_url
    return generate_upload_url(issue_id, media_type, content_type)

'''
new_lines.append(upload_endpoint)

# Add the rest starting from confirm
new_lines.extend(lines[confirm_idx:])

with open('app/api/v1/endpoints/issues.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Fixed issues.py")