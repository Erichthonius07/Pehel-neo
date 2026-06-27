"""Resolution Validator Agent â€” validates authority resolution claims.

This agent runs when an authority marks an issue as `resolved_claimed`.
It cross-checks the resolution and outputs an evidence score that feeds
into the issue's net_confidence.
"""

import json
import re
import sys
from uuid import UUID
from datetime import datetime

from groq import Groq
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Issue, IssueTimeline, AgentLog

settings = get_settings()
client = Groq(api_key=settings.GROQ_API_KEY)

# Category weights for net confidence calculation
CATEGORY_WEIGHTS = {
    'roads':   {'ai': 0.50, 'community': 0.30, 'time': 0.20},
    'water':   {'ai': 0.20, 'community': 0.40, 'time': 0.40},
    'garbage': {'ai': 0.10, 'community': 0.40, 'time': 0.50},
}

VALIDATION_PROMPT = """You are a resolution validator for civic issues in Kanpur, India.
An authority has claimed they resolved an issue. Assess the quality
and completeness of the resolution based on available evidence.

Issue reported:
- Category: {category}
- Original description: {original_description}
- Severity: {severity}
- Location: {location_text}

Authority resolution claim:
- Resolution notes: {resolution_notes}
- Photos uploaded: {has_photos}

Return ONLY valid JSON. No preamble.

{{
  "ai_evidence_score": 0-100,
  "reasoning": "one sentence explaining the score"
}}
"""


def _call_validation_llm(
    category: str,
    original_description: str,
    severity: str,
    location_text: str,
    resolution_notes: str,
    has_photos: bool,
) -> dict:
    """Call Groq LLM to validate resolution quality."""
    prompt = VALIDATION_PROMPT.format(
        category=category,
        original_description=original_description,
        severity=severity,
        location_text=location_text or "Unknown",
        resolution_notes=resolution_notes or "No notes provided",
        has_photos="Yes" if has_photos else "No",
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=256,
    )

    text = response.choices[0].message.content.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    return json.loads(text)


def _compute_net_confidence(ai_evidence_score: float, category: str, community_score: float, time_score: float) -> float:
    """Compute weighted net confidence from component scores."""
    w = CATEGORY_WEIGHTS.get(category, {'ai': 0.50, 'community': 0.30, 'time': 0.20})
    net = (ai_evidence_score * w['ai']) + (community_score * w['community']) + (time_score * w['time'])
    return round(net, 2)


def run_resolution_validator(issue_id: UUID) -> None:
    """Run Resolution Validator Agent as background task.

    Call this after authority marks issue as resolved_claimed.
    Updates issue confidence scores and creates timeline event.
    """
    from app.db.base import SessionLocal

    db = SessionLocal()
    issue = None

    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return

        # Only validate if state is resolved_claimed
        if issue.state != "resolved_claimed":
            return

        # Skip if already validated
        existing_log = (
            db.query(AgentLog)
            .filter(AgentLog.issue_id == issue_id, AgentLog.action == "resolution_validated")
            .first()
        )
        if existing_log:
            return

        # Check if resolution photos exist
        from app.models import IssueMedia
        has_photos = db.query(IssueMedia).filter(
            IssueMedia.issue_id == issue_id,
            IssueMedia.media_type == "resolution_photo"
        ).first() is not None

        # Get resolution notes from latest authority timeline entry
        timeline_entry = (
            db.query(IssueTimeline)
            .filter(
                IssueTimeline.issue_id == issue_id,
                IssueTimeline.event_type == "state_change",
                IssueTimeline.new_state == "resolved_claimed",
            )
            .order_by(IssueTimeline.sequence_number.desc())
            .first()
        )
        resolution_notes = timeline_entry.description if timeline_entry else None

        result = _call_validation_llm(
            category=issue.category,
            original_description=issue.description,
            severity=issue.severity,
            location_text=issue.location_text,
            resolution_notes=resolution_notes,
            has_photos=has_photos,
        )

        ai_evidence_score = result.get("ai_evidence_score", 50)
        reasoning = result.get("reasoning", "No reasoning provided")

                # Update issue confidence scores
        community = float(issue.confidence_community or 100)
        time_score = float(issue.confidence_time or 0)
        net_confidence = _compute_net_confidence(ai_evidence_score, issue.category, community, time_score)

        issue.confidence_ai = ai_evidence_score
        issue.net_confidence = net_confidence
        issue.confidence_updated_at = datetime.utcnow()

        # Set confidence label
        if net_confidence >= 70:
            issue.confidence_label = "High"
        elif net_confidence >= 40:
            issue.confidence_label = "Medium"
        else:
            issue.confidence_label = "Low"

        db.flush()
        db.commit()

        # Log to agent_logs
        log = AgentLog(
            agent_name="resolution_validator",
            issue_id=issue_id,
            action="resolution_validated",
            input_summary=f"category={issue.category}, severity={issue.severity}",
            output_summary=f"ai_evidence_score={ai_evidence_score}, net_confidence={net_confidence}",
            confidence_score=ai_evidence_score,
        )
        db.add(log)

        # Create timeline event
        timeline = IssueTimeline(
            issue_id=issue_id,
            event_type="ai_analysis",
            actor_type="system",
            description=f"Resolution Validator: ai_evidence_score={ai_evidence_score}, net_confidence={net_confidence}. {reasoning}",
        )
        db.add(timeline)

        db.commit()

    except Exception as e:
        try:
            db.rollback()
            log = AgentLog(
                agent_name="resolution_validator",
                issue_id=issue_id,
                action="resolution_validation_failed",
                error_message=str(e)[:500],
            )
            db.add(log)
            db.commit()
        except Exception as inner_e:
            print(f"RESOLUTION VALIDATOR CRITICAL ERROR: {inner_e}", file=sys.stderr)

    finally:
        db.close()
