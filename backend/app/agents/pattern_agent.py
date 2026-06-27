"""Pattern Intelligence Agent — weekly analysis of issue clusters.

Runs weekly via APScheduler cron (Sunday 3:00 AM).
Clusters issues by ward + category + time window.
Detects repeat failure hotspots. Stores in pattern_clusters table.
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from uuid import UUID

from groq import Groq
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.core.config import get_settings
from app.models import Issue, IssueTimeline, AgentLog, Ward, PatternCluster

settings = get_settings()
client = Groq(api_key=settings.GROQ_API_KEY)

PATTERN_PROMPT = """You are analyzing civic issue patterns for Kanpur, India.
Based on the data below, write a 2-sentence neutral summary of the pattern.
No accusations. Evidence-based only.

Ward: {ward_name}
Category: {category}
Issues in last 60 days: {total_count}
Resolved: {resolved_count}
Reopened: {reopened_count}
Repeat failures: {repeat_count}
Avg resolution time: {avg_resolution_hours} hours

Write the pattern summary:"""


def _get_ward_category_issues(db: Session, ward_id: UUID, category: str, days: int = 60) -> List[Issue]:
    """Get issues for a specific ward + category in the last N days."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    return (
        db.query(Issue)
        .filter(
            Issue.ward_id == ward_id,
            Issue.category == category,
            Issue.created_at >= cutoff,
        )
        .all()
    )


def _analyze_cluster(db: Session, ward_id: UUID, category: str, issues: List[Issue]) -> Optional[dict]:
    """Analyze a ward+category cluster and return data for storage."""
    if len(issues) < 3:
        return None  # Insufficient signal

    total_count = len(issues)
    issue_ids = [i.id for i in issues]
    
    resolved_count = sum(1 for i in issues if i.state == "resolved_confirmed")
    reopened_count = sum(1 for i in issues if i.state == "reopened")
    
    # Count repeat failures: issues that were resolved then reopened
    repeat_count = 0
    for issue in issues:
        # Check timeline for resolved -> reopened sequence
        events = (
            db.query(IssueTimeline)
            .filter(IssueTimeline.issue_id == issue.id)
            .order_by(IssueTimeline.sequence_number.asc())
            .all()
        )
        states = [e.new_state for e in events if e.new_state]
        if "resolved_confirmed" in states and "reopened" in states:
            repeat_count += 1
    
    # Calculate avg resolution time (hours) for resolved issues
    resolution_hours = []
    for issue in issues:
        if issue.state == "resolved_confirmed" and issue.created_at:
            # Find resolution event
            resolved_event = (
                db.query(IssueTimeline)
                .filter(
                    IssueTimeline.issue_id == issue.id,
                    IssueTimeline.new_state == "resolved_confirmed",
                )
                .order_by(IssueTimeline.sequence_number.asc())
                .first()
            )
            if resolved_event and resolved_event.created_at:
                hours = (resolved_event.created_at - issue.created_at).total_seconds() / 3600
                resolution_hours.append(hours)
    
    avg_resolution_hours = round(sum(resolution_hours) / len(resolution_hours), 1) if resolution_hours else 0

    # Determine cluster type
    if total_count > 0 and (reopened_count + repeat_count) / total_count > 0.3:
        cluster_type = "repeat_failure_hotspot"
    else:
        cluster_type = "activity_cluster"

    # Get ward name
    ward = db.query(Ward).filter(Ward.id == ward_id).first()
    ward_name = ward.name if ward else "Unknown"

    # Call Groq for summary
    prompt = PATTERN_PROMPT.format(
        ward_name=ward_name,
        category=category,
        total_count=total_count,
        resolved_count=resolved_count,
        reopened_count=reopened_count,
        repeat_count=repeat_count,
        avg_resolution_hours=avg_resolution_hours,
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=256,
    )

    summary = response.choices[0].message.content.strip()

    return {
        "ward_id": ward_id,
        "category": category,
        "cluster_type": cluster_type,
        "issue_ids": issue_ids,
        "summary": summary,
        "detected_at": datetime.utcnow(),
        "is_active": True,
        "stats": {
            "total_count": total_count,
            "resolved_count": resolved_count,
            "reopened_count": reopened_count,
            "repeat_count": repeat_count,
            "avg_resolution_hours": avg_resolution_hours,
        }
    }


def run_pattern_agent(city_id: UUID = None) -> dict:
    """Run pattern intelligence sweep.
    
    For each ward x category combination:
    1. Count issues in last 60 days
    2. Skip if < 3 issues (insufficient signal)
    3. Count resolved, reopened, repeat failures
    4. Calculate avg resolution time
    5. Call Groq for plain-language summary
    6. Upsert into pattern_clusters table
    7. Log to agent_logs
    
    Args:
        city_id: Optional city filter. If None, analyzes all cities.
    """
    from app.db.base import SessionLocal
    from app.models import City

    db = SessionLocal()
    result = {
        "clusters_generated": 0,
        "wards_analyzed": 0,
        "combinations_checked": 0,
        "errors": [],
    }

    try:
        # Get wards to analyze
        wards_query = db.query(Ward)
        if city_id:
            wards_query = wards_query.filter(Ward.city_id == city_id)
        wards = wards_query.all()
        
        # Get all distinct categories from issues in last 60 days
        cutoff = datetime.utcnow() - timedelta(days=60)
        categories = (
            db.query(Issue.category)
            .filter(Issue.created_at >= cutoff)
            .distinct()
            .all()
        )
        categories = [c[0] for c in categories if c[0]]

        result["wards_analyzed"] = len(wards)
        result["combinations_checked"] = len(wards) * len(categories)

        for ward in wards:
            for category in categories:
                issues = _get_ward_category_issues(db, ward.id, category, days=60)
                
                cluster_data = _analyze_cluster(db, ward.id, category, issues)
                if not cluster_data:
                    continue

                # Deactivate old cluster for this ward+category
                db.query(PatternCluster).filter(
                    PatternCluster.ward_id == ward.id,
                    PatternCluster.category == category,
                ).update({"is_active": False})

                # Insert new cluster
                cluster = PatternCluster(
                    ward_id=cluster_data["ward_id"],
                    category=cluster_data["category"],
                    cluster_type=cluster_data["cluster_type"],
                    issue_ids=cluster_data["issue_ids"],
                    summary=cluster_data["summary"],
                    detected_at=cluster_data["detected_at"],
                    is_active=cluster_data["is_active"],
                )
                db.add(cluster)
                result["clusters_generated"] += 1

        db.commit()

        # Log
        log = AgentLog(
            agent_name="pattern_intelligence",
            issue_id=None,
            action="weekly_analysis",
            input_summary=f"wards={len(wards)}, categories={len(categories)}",
            output_summary=f"clusters_generated={result['clusters_generated']}",
        )
        db.add(log)
        db.commit()

    except Exception as e:
        db.rollback()
        result["errors"].append(str(e)[:500])
        try:
            log = AgentLog(
                agent_name="pattern_intelligence",
                issue_id=None,
                action="analysis_failed",
                error_message=str(e)[:500],
            )
            db.add(log)
            db.commit()
        except Exception:
            pass

    finally:
        db.close()

    return result
