"""Intake Agent — classifies civic issues using Groq LLM."""
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

INTAKE_PROMPT = """You are a civic issue classifier for Kanpur, India.
Analyze the issue description and return ONLY valid JSON. No preamble.

Description: {description}
Category: {category}
Location: {location_text}

Return JSON:
{{
  "severity": "low|medium|high|critical",
  "structured_title": "concise title under 80 chars",
  "structured_description": "clear factual one paragraph description",
  "is_safety_risk": true|false,
  "confidence": 0-100
}}
"""


def _call_llm(description: str, category: str, location_text: str) -> dict:
    """Call Groq LLM and parse JSON response."""
    prompt = INTAKE_PROMPT.format(
        description=description,
        category=category,
        location_text=location_text or "Unknown",
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


def _calculate_initial_priority_score(severity: str, is_safety_risk: bool, confidence: float) -> int:
    """Calculate initial priority score from agent output.
    
    NOTE: This is a placeholder. Full formula from build doc includes:
    time_score, volume_score, failure_score, risk_score.
    """
    severity_weights = {"low": 10, "medium": 30, "high": 60, "critical": 90}
    base = severity_weights.get(severity, 20)
    safety_bonus = 20 if is_safety_risk else 0
    confidence_factor = confidence / 100.0

    score = int((base + safety_bonus) * confidence_factor)
    return min(score, 100)


def run_intake_agent(issue_id: UUID) -> None:
    """Run Intake Agent with fresh DB session. Call as background task."""
    from app.db.base import SessionLocal

    db = SessionLocal()
    issue = None

    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            return

        # Skip if already processed — check agent_logs, not ai_summary
        existing = db.query(AgentLog).filter(
            AgentLog.issue_id == issue_id,
            AgentLog.action == "intake_complete"
        ).first()
        if existing:
            return

        result = _call_llm(
            description=issue.description,
            category=issue.category,
            location_text=issue.location_text,
        )

        severity = result.get("severity", "medium")
        is_safety_risk = result.get("is_safety_risk", False)
        confidence = result.get("confidence", 50)
        structured_description = result.get("structured_description", issue.description)

        priority_score = _calculate_initial_priority_score(severity, is_safety_risk, confidence)

        # Update issue
        issue.severity = severity
        issue.is_safety_risk = is_safety_risk
        issue.ai_summary = structured_description[:500]
        issue.priority_score = priority_score
        issue.confidence_ai = confidence

        # Explicit flush to ensure SQLAlchemy tracks changes before commit
        db.flush()
        db.commit()

        # Log success
        log = AgentLog(
            agent_name="intake",
            issue_id=issue_id,
            action="intake_complete",
            input_summary=f"category={issue.category}, len={len(issue.description)}",
            output_summary=f"severity={severity}, safety={is_safety_risk}, confidence={confidence}",
            confidence_score=confidence,
        )
        db.add(log)

        # Create timeline event
        timeline = IssueTimeline(
            issue_id=issue_id,
            event_type="ai_analysis",
            actor_type="system",
            description=f"Intake Agent: severity={severity}, safety_risk={is_safety_risk}, confidence={confidence}",
        )
        db.add(timeline)

        db.commit()

    except Exception as e:
        # Log failure — wrapped to prevent logging crash from masking original error
        try:
            db.rollback()
            log = AgentLog(
                agent_name="intake",
                issue_id=issue_id,
                action="intake_failed",
                error_message=str(e)[:500],
            )
            db.add(log)
            db.commit()
        except Exception as inner_e:
            print(f"INTAKE AGENT CRITICAL ERROR: {inner_e}", file=sys.stderr)

    finally:
        db.close()