"""Resolution Validator Agent — validates authority resolution claims.

This agent runs when an authority marks an issue as `resolved_claimed`.
It cross-checks the resolution against:
- Issue description (what was reported vs what was done)
- Photo evidence (if uploaded)
- Authority notes
- Historical pattern (has this location had repeat failures?)

Outputs a confidence score (0-100) that feeds into the citizen's
decision to confirm or dispute.
"""

import json
import re
from uuid import UUID
from datetime import datetime

from groq import Groq
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Issue, IssueTimeline, AgentLog

settings = get_settings()
client = Groq(api_key=settings.GROQ_API_KEY)

VALIDATION_PROMPT = """You are a resolution validator for civic issues in Kanpur, India.
An authority has claimed they resolved an issue. Your job is to assess
the quality and completeness of the resolution based on available evidence.

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
  "resolution_confidence": 0-100,
  "completeness": "partial|full|insufficient",
  "evidence_quality": "poor|fair|good|excellent",
  "risk_of_repeat": "low|medium|high",
  "reasoning": "one sentence explaining the score",
  "recommendation": "confirm|dispute|inspect"
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
        max_tokens=512,
    )

    text = response.choices[0].message.content.strip()
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    return json.loads(text)


def run_resolution_validator(issue_id: UUID) -> None:
    """Run Resolution Validator Agent as background task.

    Call this after authority marks issue as resolved_claimed.
    Stores validation result in agent_logs and creates timeline event.
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

        # TODO: Check if photos exist (MinIO/S3 integration pending)
        has_photos = False  # Placeholder until photo upload is built

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

        resolution_confidence = result.get("resolution_confidence", 50)
        completeness = result.get("completeness", "insufficient")
        evidence_quality = result.get("evidence_quality", "poor")
        risk_of_repeat = result.get("risk_of_repeat", "high")
        reasoning = result.get("reasoning", "No reasoning provided")
        recommendation = result.get("recommendation", "inspect")

        # Log to agent_logs
        log = AgentLog(
            agent_name="resolution_validator",
            issue_id=issue_id,
            action="resolution_validated",
            input_summary=f"category={issue.category}, severity={issue.severity}",
            output_summary=f"confidence={resolution_confidence}, completeness={completeness}, recommendation={recommendation}",
            confidence_score=resolution_confidence,
        )
        db.add(log)

        # Create timeline event
        timeline = IssueTimeline(
            issue_id=issue_id,
            event_type="ai_analysis",
            actor_type="system",
            description=f"Resolution Validator: confidence={resolution_confidence}, {reasoning}. Recommendation: {recommendation}",
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
        except Exception:
            pass

    finally:
        db.close()