"""Narrative Agent - generates human-readable issue summaries and chat answers."""

import json
import re
from uuid import UUID
from datetime import datetime

from groq import Groq
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Issue, IssueTimeline, AgentLog, User

settings = get_settings()
client = Groq(api_key=settings.GROQ_API_KEY)

STATE_LABELS = {
    "reported": "Reported - awaiting acknowledgement",
    "acknowledged": "Acknowledged - authority has seen this",
    "visited": "Site visited - inspection completed",
    "in_progress": "Work in progress",
    "resolved_claimed": "Resolution claimed - pending verification",
    "resolved_confirmed": "Resolved and verified",
    "resolution_unverified": "Resolution unverified - evidence inconclusive",
    "disputed": "Disputed - resolution contested by citizens",
    "reopened": "Reopened - previous resolution failed",
    "closed": "Closed",
}

NARRATIVE_PROMPT = """You are a civic information assistant for Pehel Neo,
a civic accountability platform in Kanpur, India.

Write a clear, neutral, factual summary of this civic issue for citizens.
Use simple language. No accusations. No speculation. Max 3 sentences.

Issue: {title}
Category: {category}
Location: {location_text}, {ward_name}, Kanpur
Current State: {state_label}
Reported: {created_at}
People Affected: {support_count}
SLA Status: {sla_status}
Recent Timeline:
{timeline_summary}

Write the summary now:"""

CHAT_PROMPT = """You are a civic assistant for Pehel Neo in Kanpur, India.
Answer the citizen's question about this specific issue.
Use ONLY the information provided. Be factual, neutral, concise.
Never speculate. Never name individuals.
If information is not available, say so clearly.

Issue Summary: {ai_summary}
Current State: {state_label}
Full Timeline:
{timeline_text}

Citizen's Question: {question}

Answer:"""


def _get_state_label(state: str) -> str:
    return STATE_LABELS.get(state, state)


def _build_timeline_summary(db: Session, issue_id: UUID) -> str:
    """Build a text summary of recent timeline events."""
    events = (
        db.query(IssueTimeline)
        .filter(IssueTimeline.issue_id == issue_id)
        .order_by(IssueTimeline.sequence_number.desc())
        .limit(10)
        .all()
    )
    lines = []
    for e in reversed(events):
        actor = e.actor_type or "system"
        desc = e.description or ""
        lines.append(f"- [{actor}]: {desc}")
    return "\n".join(lines) if lines else "No recent activity."


def _build_full_timeline_text(db: Session, issue_id: UUID) -> str:
    """Build complete timeline text for chat context."""
    events = (
        db.query(IssueTimeline)
        .filter(IssueTimeline.issue_id == issue_id)
        .order_by(IssueTimeline.sequence_number.asc())
        .all()
    )
    lines = []
    for e in events:
        actor = e.actor_type or "system"
        desc = e.description or ""
        state = f" -> {e.new_state}" if e.new_state else ""
        lines.append(f"[{actor}]: {desc}{state}")
    return "\n".join(lines) if lines else "No events yet."


def _get_sla_status(issue) -> str:
    """Get human-readable SLA status."""
    from datetime import timezone
    now = datetime.now(timezone.utc)
    if issue.state in ["closed", "resolved_confirmed"]:
        return "Completed"
    if issue.sla_resolution_deadline and issue.sla_resolution_deadline < now:
        return "Overdue"
    if issue.sla_ack_deadline and issue.sla_ack_deadline < now:
        return "Acknowledgement overdue"
    return "On track"
def _call_narrative_llm(issue, state_label: str, timeline_summary: str, ward_name: str) -> str:
    """Call Groq LLM to generate narrative summary."""
    prompt = NARRATIVE_PROMPT.format(
        title=issue.title,
        category=issue.category,
        location_text=issue.location_text or "Unknown location",
        ward_name=ward_name,
        state_label=state_label,
        created_at=issue.created_at.strftime("%Y-%m-%d") if issue.created_at else "Unknown",
        support_count=issue.support_count or 0,
        sla_status=_get_sla_status(issue),
        timeline_summary=timeline_summary,
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=256,
    )

    return response.choices[0].message.content.strip()


def _call_chat_llm(ai_summary: str, state_label: str, timeline_text: str, question: str) -> str:
    """Call Groq LLM to answer citizen question."""
    prompt = CHAT_PROMPT.format(
        ai_summary=ai_summary or "No summary available.",
        state_label=state_label,
        timeline_text=timeline_text,
        question=question,
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=512,
    )

    return response.choices[0].message.content.strip()


def run_narrative_agent(issue_id: UUID) -> None:
    """Generate/update plain-language summary. Call as background task."""
    from app.db.base import SessionLocal
    from app.models import Ward

    db = SessionLocal()
    issue = None

    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return

        # Check if already processed recently
        existing = db.query(AgentLog).filter(
            AgentLog.issue_id == issue_id,
            AgentLog.action.in_(["summary_generated", "summary_updated"])
        ).order_by(AgentLog.created_at.desc()).first()

        action = "summary_updated" if existing else "summary_generated"

        ward = db.query(Ward).filter(Ward.id == issue.ward_id).first()
        ward_name = ward.name if ward else "Unknown ward"

        state_label = _get_state_label(issue.state)
        timeline_summary = _build_timeline_summary(db, issue_id)

        narrative = _call_narrative_llm(issue, state_label, timeline_summary, ward_name)

        # Update issue ai_summary
        issue.ai_summary = narrative[:500]

        db.flush()
        db.commit()

        # Log
        log = AgentLog(
            agent_name="narrative",
            issue_id=issue_id,
            action=action,
            input_summary=f"state={issue.state}, events={timeline_summary.count(chr(10)) + 1}",
            output_summary=narrative[:200],
        )
        db.add(log)
        db.commit()

    except Exception as e:
        import sys
        print(f"NARRATIVE AGENT ERROR: {e}", file=sys.stderr)
        import sys
        print(f"NARRATIVE AGENT ERROR: {e}", file=sys.stderr)
        try:
            db.rollback()
            db.rollback()
            log = AgentLog(
                agent_name="narrative",
                issue_id=issue_id,
                action="summary_failed",
                error_message=str(e)[:500],
            )
            db.add(log)
            db.commit()
        except Exception:
            pass

    finally:
        db.close()


def answer_issue_query(issue_id: UUID, question: str) -> dict:
    """Answer citizen question about specific issue. Sync call from chat endpoint."""
    from app.db.base import SessionLocal
    from app.models import Ward

    db = SessionLocal()
    result = {"answer": "", "issue_id": str(issue_id), "context_used": "summary"}

    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return
            return result

        state_label = _get_state_label(issue.state)
        timeline_text = _build_full_timeline_text(db, issue_id)

        # Use full timeline if question asks about history/timeline
        history_keywords = ["history", "timeline", "what happened", "when", "past", "before"]
        if any(kw in question.lower() for kw in history_keywords):
            result["context_used"] = "full_timeline"

        answer = _call_chat_llm(
            ai_summary=issue.ai_summary,
            state_label=state_label,
            timeline_text=timeline_text,
            question=question,
        )

        result["answer"] = answer

        # Log
        log = AgentLog(
            agent_name="narrative",
            issue_id=issue_id,
            action="chat_answer",
            input_summary=f"question={question[:100]}",
            output_summary=answer[:200],
        )
        db.add(log)
        db.commit()

    except Exception as e:
        result["answer"] = f"Sorry, I couldn't answer that. Error: {str(e)[:200]}"

    finally:
        db.close()

    return result
