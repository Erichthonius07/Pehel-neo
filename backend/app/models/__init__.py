from sqlalchemy import (
    Column, String, Integer, BigInteger, Numeric, Boolean, DateTime, Text, ForeignKey, UniqueConstraint, Index, CheckConstraint, Sequence
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func, text
import uuid

from app.db.base import Base
from app.core.constants import IssueState, UserRole, IssueCategory, SeverityLevel, MediaType, EventType, ActorType


class State(Base):
    __tablename__ = "states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    code = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    cities = relationship("City", back_populates="state")


class City(Base):
    __tablename__ = "cities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    state_id = Column(UUID(as_uuid=True), ForeignKey("states.id"), nullable=False)
    name = Column(String(100), nullable=False)
    is_pilot = Column(Boolean, default=False)
    boundary_geojson = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    state = relationship("State", back_populates="cities")
    wards = relationship("Ward", back_populates="city")
    issues = relationship("Issue", back_populates="city")


class Ward(Base):
    __tablename__ = "wards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"), nullable=False)
    name = Column(String(100), nullable=False)
    ward_number = Column(String(20), nullable=False)
    boundary_geojson = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    city = relationship("City", back_populates="wards")
    issues = relationship("Issue", back_populates="ward")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_hash = Column(String(255), nullable=False, unique=True)
    pseudonym = Column(String(50), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active_at = Column(DateTime(timezone=True), server_default=func.now())

    issues = relationship("Issue", back_populates="user")
    supports = relationship("IssueSupport", back_populates="user")
    # bookmarks: polymorphic ï¿½ access via user.bookmarks
    comments = relationship("IssueComment", back_populates="user")


class Authority(Base):
    __tablename__ = "authorities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    city = relationship("City")
    users = relationship("AuthorityUser", back_populates="authority")


class AuthorityUser(Base):
    __tablename__ = "authority_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    authority_id = Column(UUID(as_uuid=True), ForeignKey("authorities.id"), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=False)
    role = Column(String(20), nullable=False, server_default="viewer")
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    authority = relationship("Authority", back_populates="users")
    ward = relationship("Ward")
    comments = relationship("IssueComment", back_populates="authority_user")
    notes = relationship("AuthorityNote", back_populates="authority_user")

    __table_args__ = (
        CheckConstraint("role IN ('admin', 'supervisor', 'field_officer', 'viewer')", name="ck_authority_users_role"),
    )


class Issue(Base):
    __tablename__ = "issues"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"), nullable=False)
    city_id = Column(UUID(as_uuid=True), ForeignKey("cities.id"))
    category = Column(String(20), nullable=False, server_default="roads")
    severity = Column(String(20), nullable=False, server_default="medium")
    title = Column(String(255), nullable=False)
    description = Column(Text)
    geo_lat = Column(Numeric(10, 8), nullable=False)
    geo_lng = Column(Numeric(11, 8), nullable=False)
    location_text = Column(String(255))
    state = Column(String(30), nullable=False, server_default="reported")
    ai_summary = Column(Text)
    ai_tags = Column(ARRAY(Text))
    confidence_ai = Column(Numeric(5, 2))
    confidence_community = Column(Numeric(5, 2), default=100.00)
    confidence_time = Column(Numeric(5, 2))
    net_confidence = Column(Numeric(5, 2))
    confidence_updated_at = Column(DateTime(timezone=True))
    confidence_label = Column(String(20))
    priority_score = Column(Numeric(6, 2), default=0)
    support_count = Column(Integer, default=0)
    is_safety_risk = Column(Boolean, default=False)
    has_unverified_closure = Column(Boolean, default=False)
    previous_issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"))
    sla_ack_deadline = Column(DateTime(timezone=True))
    sla_visit_deadline = Column(DateTime(timezone=True))
    sla_resolution_deadline = Column(DateTime(timezone=True))
    time_decay_window_ends_at = Column(DateTime(timezone=True))
    is_repeat_failure = Column(Boolean, default=False)
    repeat_count = Column(Integer, default=0)
    merged_into_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="issues")
    ward = relationship("Ward", back_populates="issues")
    city = relationship("City", back_populates="issues")
    media = relationship("IssueMedia", back_populates="issue")
    timeline = relationship("IssueTimeline", back_populates="issue")
    supports = relationship("IssueSupport", back_populates="issue")
    comments = relationship("IssueComment", back_populates="issue")
    notes = relationship("AuthorityNote", back_populates="issue")
    merged_into = relationship("Issue", remote_side=[id], foreign_keys=[merged_into_id])
    previous_issue = relationship("Issue", remote_side=[id], foreign_keys=[previous_issue_id])

    __table_args__ = (
        CheckConstraint("category IN ('roads', 'water', 'garbage')", name="ck_issues_category"),
        CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="ck_issues_severity"),
        CheckConstraint("state IN ('reported', 'acknowledged', 'visited', 'in_progress', 'resolved_claimed', 'resolved_confirmed', 'resolution_unverified', 'disputed', 'reopened', 'closed')", name="ck_issues_state"),
    )


class IssueMedia(Base):
    __tablename__ = "issue_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    media_type = Column(String(20), nullable=False, server_default="complaint_photo")
    s3_key = Column(String(512), nullable=False)
    s3_bucket = Column(String(100), nullable=False)
    original_filename = Column(String(255))
    mime_type = Column(String(100))
    file_size = Column(BigInteger)
    geo_lat = Column(Numeric(10, 8))
    geo_lng = Column(Numeric(11, 8))
    ai_vision_description = Column(Text)
    embedding_vector = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue", back_populates="media")

    __table_args__ = (
        CheckConstraint("media_type IN ('complaint_photo', 'resolution_photo', 'visit_photo', 'audio')", name="ck_issue_media_type"),
    )


class IssueTimeline(Base):
    __tablename__ = "issue_timeline"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    event_type = Column(String(30), nullable=False, server_default="state_change")
    old_state = Column(String(30))
    new_state = Column(String(30))
    actor_type = Column(String(20))
    actor_id = Column(UUID(as_uuid=True))
    description = Column(Text, nullable=False)
    metadata_json = Column(JSONB)
    sequence_number = Column(BigInteger, nullable=False, server_default=text("nextval('issue_timeline_seq')"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue", back_populates="timeline")

    __table_args__ = (
        CheckConstraint("event_type IN ('state_change', 'sla_breach', 'silence_milestone', 'ai_analysis', 'comment', 'confidence_update', 'merge', 'repeat_failure')", name="ck_timeline_event_type"),
    )


class IssueComment(Base):
    __tablename__ = "issue_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    authority_user_id = Column(UUID(as_uuid=True), ForeignKey("authority_users.id"))
    is_agent = Column(Boolean, default=False)
    message_text = Column(Text, nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey('issue_comments.id'), nullable=True)
    author_type = Column(String(20), nullable=False, server_default='citizen')
    author_label = Column(String(150), nullable=True)
    agent_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue", back_populates="comments")
    user = relationship("User", back_populates="comments")
    authority_user = relationship("AuthorityUser", back_populates="comments")


class IssueSupport(Base):
    __tablename__ = "issue_supports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue", back_populates="supports")
    user = relationship("User", back_populates="supports")

    __table_args__ = (UniqueConstraint("issue_id", "user_id", name="uq_issue_support"),)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    entity_type = Column(String(20), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")

    __table_args__ = (
        CheckConstraint("entity_type IN ('issue', 'city', 'ward')", name="ck_bookmarks_entity_type"),
        UniqueConstraint("user_id", "entity_type", "entity_id", name="uq_bookmark"),
    )


class AuthorityNote(Base):
    __tablename__ = "authority_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    authority_user_id = Column(UUID(as_uuid=True), ForeignKey("authority_users.id"), nullable=False)
    note_text = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue", back_populates="notes")
    authority_user = relationship("AuthorityUser", back_populates="notes")


class SLAExtension(Base):
    __tablename__ = "sla_extensions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"), nullable=False)
    original_deadline = Column(DateTime(timezone=True), nullable=False)
    new_deadline = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=False)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("authority_users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    issue = relationship("Issue")


class OTPStore(Base):
    __tablename__ = "otp_store"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_hash = Column(String(255), nullable=False)
    otp_code = Column(String(10), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String(50), nullable=False)
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"))
    action = Column(String(100), nullable=False)
    input_summary = Column(Text)
    output_summary = Column(Text)
    confidence_score = Column(Numeric(5, 2))
    processing_time_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())



class PatternCluster(Base):
    __tablename__ = "pattern_clusters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("wards.id"), nullable=False)
    category = Column(String(20))
    cluster_type = Column(String(50), nullable=False)
    issue_ids = Column(ARRAY(UUID(as_uuid=True)))
    summary = Column(Text)
    geojson = Column(Text)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    issue_id = Column(UUID(as_uuid=True), ForeignKey("issues.id"))
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
