"""Comment endpoints with threading."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

from app.db.base import get_db
from app.api.deps import get_current_citizen, get_current_authority
from app.models import IssueComment, Issue, IssueTimeline, User, AuthorityUser

router = APIRouter(prefix="/issues", tags=["comments"])


class CommentCreate(BaseModel):
    message_text: str
    parent_id: Optional[UUID] = None


@router.post("/{issue_id}/comments")
def add_comment(
    issue_id: UUID,
    body: CommentCreate,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Citizen adds a comment on an issue."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    message = body.message_text
    parent_id = body.parent_id

    # Validate parent_id
    if parent_id:
        parent = db.query(IssueComment).filter(
            IssueComment.id == parent_id,
            IssueComment.issue_id == issue_id,
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        # One level only: parent cannot itself have a parent
        if parent.parent_id is not None:
            raise HTTPException(status_code=400, detail="Cannot reply to a reply (one level only)")

    # Get citizen pseudonym for label
    user = db.query(User).filter(User.id == citizen["id"]).first()
    label = user.pseudonym if user and user.pseudonym else "Citizen"

    comment = IssueComment(
        issue_id=issue_id,
        user_id=citizen["id"],
        authority_user_id=None,
        is_agent=False,
        message_text=message,
        parent_id=parent_id,
        author_type="citizen",
        author_label=label,
    )
    db.add(comment)

    # Timeline event
    timeline = IssueTimeline(
        issue_id=issue_id,
        event_type="comment",
        actor_type="citizen",
        actor_id=citizen["id"],
        description=f"{label} commented: {message[:100]}",
    )
    db.add(timeline)

    db.commit()
    db.refresh(comment)

    return {
        "id": str(comment.id),
        "issue_id": str(comment.issue_id),
        "message_text": comment.message_text,
        "author_type": comment.author_type,
        "author_label": comment.author_label,
        "parent_id": str(comment.parent_id) if comment.parent_id else None,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


@router.post("/{issue_id}/comments/authority")
def add_authority_comment(
    issue_id: UUID,
    body: CommentCreate,
    authority: dict = Depends(get_current_authority),
    db: Session = Depends(get_db),
):
    """Authority adds a comment on an issue."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    message = body.message_text
    parent_id = body.parent_id

    # Validate parent_id
    if parent_id:
        parent = db.query(IssueComment).filter(
            IssueComment.id == parent_id,
            IssueComment.issue_id == issue_id,
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
        # One level only
        if parent.parent_id is not None:
            raise HTTPException(status_code=400, detail="Cannot reply to a reply (one level only)")

    # Get authority user name for label
    auth_user = db.query(AuthorityUser).filter(AuthorityUser.id == authority["id"]).first()
    label = f"{auth_user.name}" if auth_user else "Authority"

    comment = IssueComment(
        issue_id=issue_id,
        user_id=None,
        authority_user_id=authority["id"],
        is_agent=False,
        message_text=message,
        parent_id=parent_id,
        author_type="authority",
        author_label=label,
    )
    db.add(comment)

    # Timeline event
    timeline = IssueTimeline(
        issue_id=issue_id,
        event_type="comment",
        actor_type="authority",
        actor_id=authority["id"],
        description=f"{label} commented: {message[:100]}",
    )
    db.add(timeline)

    db.commit()
    db.refresh(comment)

    return {
        "id": str(comment.id),
        "issue_id": str(comment.issue_id),
        "message_text": comment.message_text,
        "author_type": comment.author_type,
        "author_label": comment.author_label,
        "parent_id": str(comment.parent_id) if comment.parent_id else None,
        "created_at": comment.created_at.isoformat() if comment.created_at else None,
    }


@router.get("/{issue_id}/comments")
def get_comments(
    issue_id: UUID,
    db: Session = Depends(get_db),
):
    """Get threaded comments for an issue. Public — no auth required."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    comments = (
        db.query(IssueComment)
        .filter(IssueComment.issue_id == issue_id)
        .order_by(IssueComment.created_at.asc())
        .all()
    )

    # Build threaded structure
    comment_map = {}
    root_comments = []

    for c in comments:
        node = {
            "id": str(c.id),
            "message_text": c.message_text,
            "author_type": c.author_type,
            "author_label": c.author_label,
            "parent_id": str(c.parent_id) if c.parent_id else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "replies": [],
        }
        comment_map[str(c.id)] = node

    for c in comments:
        node = comment_map[str(c.id)]
        if c.parent_id and str(c.parent_id) in comment_map:
            comment_map[str(c.parent_id)]["replies"].append(node)
        else:
            root_comments.append(node)

    total_all = len(comments)
    total_top_level = len(root_comments)

    return {
        "issue_id": str(issue_id),
        "comments": root_comments,
        "total_top_level": total_top_level,
        "total_all": total_all,
    }


@router.delete("/{issue_id}/comments/{comment_id}")
def delete_comment(
    issue_id: UUID,
    comment_id: UUID,
    citizen: dict = Depends(get_current_citizen),
    db: Session = Depends(get_db),
):
    """Soft delete a comment. Original author only."""
    comment = db.query(IssueComment).filter(
        IssueComment.id == comment_id,
        IssueComment.issue_id == issue_id,
    ).first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    # Check ownership
    if comment.user_id != citizen["id"]:
        raise HTTPException(status_code=403, detail="Can only delete your own comments")

    # Soft delete: preserve thread integrity
    comment.message_text = "[deleted]"
    comment.author_label = "[deleted]"

    db.commit()

    return {"status": "deleted", "comment_id": str(comment_id)}
