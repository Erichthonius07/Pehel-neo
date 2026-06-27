from enum import Enum as PyEnum
from datetime import timedelta


class IssueState(str, PyEnum):
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    VISITED = "visited"
    IN_PROGRESS = "in_progress"
    RESOLVED_CLAIMED = "resolved_claimed"
    RESOLVED_CONFIRMED = "resolved_confirmed"
    RESOLUTION_UNVERIFIED = "resolution_unverified"
    DISPUTED = "disputed"
    REOPENED = "reopened"
    CLOSED = "closed"


class UserRole(str, PyEnum):
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    FIELD_OFFICER = "field_officer"
    VIEWER = "viewer"


class IssueCategory(str, PyEnum):
    ROADS = "roads"
    WATER = "water"
    GARBAGE = "garbage"


class SeverityLevel(str, PyEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class MediaType(str, PyEnum):
    COMPLAINT_PHOTO = "complaint_photo"
    RESOLUTION_PHOTO = "resolution_photo"
    VISIT_PHOTO = "visit_photo"
    AUDIO = "audio"


class EventType(str, PyEnum):
    STATE_CHANGE = "state_change"
    SLA_BREACH = "sla_breach"
    SILENCE_MILESTONE = "silence_milestone"
    AI_ANALYSIS = "ai_analysis"
    COMMENT = "comment"
    CONFIDENCE_UPDATE = "confidence_update"
    MERGE = "merge"
    REPEAT_FAILURE = "repeat_failure"


class ActorType(str, PyEnum):
    CITIZEN = "citizen"
    AUTHORITY = "authority"
    SYSTEM = "system"
    AGENT = "agent"


# State machine: valid transitions
VALID_TRANSITIONS = {
    IssueState.REPORTED: [IssueState.ACKNOWLEDGED],
    IssueState.ACKNOWLEDGED: [IssueState.VISITED],
    IssueState.VISITED: [IssueState.IN_PROGRESS],
    IssueState.IN_PROGRESS: [IssueState.RESOLVED_CLAIMED],
    IssueState.RESOLVED_CLAIMED: [IssueState.RESOLVED_CONFIRMED, IssueState.DISPUTED, IssueState.RESOLUTION_UNVERIFIED],
    IssueState.DISPUTED: [IssueState.REOPENED, IssueState.CLOSED],
    IssueState.REOPENED: [IssueState.ACKNOWLEDGED],
    IssueState.RESOLVED_CONFIRMED: [IssueState.CLOSED],
    IssueState.RESOLUTION_UNVERIFIED: [IssueState.REOPENED, IssueState.CLOSED],
    IssueState.CLOSED: [],
}

# SLA defaults (hours for ack/visit, days for resolution)
SLA_DEFAULTS = {
    IssueCategory.ROADS: {"ack": 4, "visit": 48, "resolution": 10, "time_decay_days": 30},
    IssueCategory.WATER: {"ack": 2, "visit": 24, "resolution": 5, "time_decay_days": 14},
    IssueCategory.GARBAGE: {"ack": 4, "visit": 24, "resolution": 2, "time_decay_days": 7},
}

# Confidence weights per category
CONFIDENCE_WEIGHTS = {
    IssueCategory.ROADS: {"ai": 0.50, "community": 0.30, "time": 0.20},
    IssueCategory.WATER: {"ai": 0.20, "community": 0.40, "time": 0.40},
    IssueCategory.GARBAGE: {"ai": 0.10, "community": 0.40, "time": 0.50},
}

# Duplicate detection
DUPLICATE_COSINE_THRESHOLD = 0.82
DUPLICATE_TIME_WINDOW_DAYS = 30

# Repeat failure
REPEAT_FAILURE_MONTHS = 6
