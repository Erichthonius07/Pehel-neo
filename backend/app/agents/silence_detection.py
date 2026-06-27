"""Silence Detection Agent — monitors issues for SLA breaches and inactivity.

This agent runs on a schedule (e.g., daily cron) and:
1. Finds issues that have breached SLA deadlines
2. Finds issues with no activity for extended periods
3. Escalates by creating timeline events
4. Logs all actions to agent_logs
"""

from uuid import UUID
from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.models import Issue, IssueTimeline, AgentLog


def _get_breached_issues(db: Session) -> List[Issue]:
    """Find issues that have breached their SLA deadlines."""
    now = datetime.utcnow()

    return (
        db.query(Issue)
        .filter(
            Issue.state.notin_(["closed", "resolved_confirmed"]),
            (
                (Issue.state.in_(["reported", "acknowledged"]) & (Issue.sla_ack_deadline < now))
                | (Issue.state.in_(["acknowledged", "visited"]) & (Issue.sla_visit_deadline < now))
                | (Issue.state.in_(["in_progress", "resolved_claimed"]) & (Issue.sla_resolution_deadline < now))
            )
        )
        .all()
    )


def _create_sla_breach_event(db: Session, issue: Issue) -> None:
    """Create timeline event and log for SLA breach."""
    now = datetime.utcnow()
    breached_deadlines = []

    if issue.state in ["reported", "acknowledged"] and issue.sla_ack_deadline and issue.sla_ack_deadline < now:
        breached_deadlines.append("acknowledge")
    if issue.state in ["acknowledged", "visited"] and issue.sla_visit_deadline and issue.sla_visit_deadline < now:
        breached_deadlines.append("visit")
    if issue.state in ["in_progress", "resolved_claimed"] and issue.sla_resolution_deadline and issue.sla_resolution_deadline < now:
        breached_deadlines.append("resolution")

    for deadline in breached_deadlines:
        description = f"SLA breach: {deadline} deadline exceeded"

        timeline = IssueTimeline(
            issue_id=issue.id,
            event_type="sla_breach",
            actor_type="system",
            description=description,
        )
        db.add(timeline)

        log = AgentLog(
            agent_name="silence_detection",
            issue_id=issue.id,
            action=f"sla_breach_{deadline}",
            input_summary=f"state={issue.state}, deadline={deadline}",
            output_summary=description,
        )
        db.add(log)


def _get_silent_issues(db: Session, days: int = 7) -> List[Issue]:
    """Find issues with no timeline activity for N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    from sqlalchemy import func
    recent_activity = (
        db.query(IssueTimeline.issue_id)
        .filter(IssueTimeline.created_at > cutoff)
        .distinct()
        .subquery()
    )

    return (
        db.query(Issue)
        .filter(
            Issue.state.notin_(["closed", "resolved_confirmed"]),
            ~Issue.id.in_(recent_activity),
        )
        .all()
    )


def _create_silence_event(db: Session, issue: Issue, days_inactive: int) -> None:
    """Create timeline event for silent issue."""
    description = f"Silence milestone: no activity for {days_inactive}+ days"

    timeline = IssueTimeline(
        issue_id=issue.id,
        event_type="silence_milestone",
        actor_type="system",
        description=description,
    )
    db.add(timeline)

    log = AgentLog(
        agent_name="silence_detection",
        issue_id=issue.id,
        action="silence_detected",
        input_summary=f"state={issue.state}, days_inactive={days_inactive}",
        output_summary=description,
    )
    db.add(log)


def run_silence_detection() -> dict:
    """Run full silence detection sweep. Returns summary stats.

    Call this from APScheduler cron job or manually.
    """
    from app.db.base import SessionLocal

    db = SessionLocal()
    stats = {
        "sla_breaches": 0,
        "silent_issues": 0,
        "total_flagged": 0,
        "errors": [],
    }

    try:
        # Check SLA breaches
        breached = _get_breached_issues(db)
        for issue in breached:
            _create_sla_breach_event(db, issue)
            stats["sla_breaches"] += 1

        # Check silent issues (7+ days no activity)
        silent = _get_silent_issues(db, days=7)
        for issue in silent:
            _create_silence_event(db, issue, days_inactive=7)
            stats["silent_issues"] += 1

        db.commit()

        stats["total_flagged"] = stats["sla_breaches"] + stats["silent_issues"]

    except Exception as e:
        db.rollback()
        stats["errors"].append(str(e))
        try:
            log = AgentLog(
                agent_name="silence_detection",
                issue_id=None,
                action="sweep_failed",
                error_message=str(e)[:500],
            )
            db.add(log)
            db.commit()
        except Exception:
            pass

    finally:
        db.close()

    return stats


def run_silence_detection_for_issue(issue_id: UUID) -> dict:
    """Run silence detection on a single issue. Returns findings."""
    from app.db.base import SessionLocal

    db = SessionLocal()
    result = {
        "issue_id": str(issue_id),
        "sla_breaches": [],
        "is_silent": False,
        "days_inactive": 0,
    }

    try:
        issue = db.query(Issue).filter(Issue.id == issue_id).first()
        if not issue:
            result["error"] = "Issue not found"
            return result

        now = datetime.utcnow()

        # Check SLA breaches
        if issue.state in ["reported", "acknowledged"] and issue.sla_ack_deadline and issue.sla_ack_deadline < now:
            result["sla_breaches"].append("acknowledge")
        if issue.state in ["acknowledged", "visited"] and issue.sla_visit_deadline and issue.sla_visit_deadline < now:
            result["sla_breaches"].append("visit")
        if issue.state in ["in_progress", "resolved_claimed"] and issue.sla_resolution_deadline and issue.sla_resolution_deadline < now:
            result["sla_breaches"].append("resolution")

        # Check silence
        latest_activity = (
            db.query(IssueTimeline)
            .filter(IssueTimeline.issue_id == issue_id)
            .order_by(IssueTimeline.created_at.desc())
            .first()
        )

        if latest_activity:
            days_inactive = (now - latest_activity.created_at).days
            result["days_inactive"] = days_inactive
            if days_inactive >= 7:
                result["is_silent"] = True

    except Exception as e:
        result["error"] = str(e)

    finally:
        db.close()

    return result