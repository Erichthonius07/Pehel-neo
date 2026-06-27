"""Initial schema - complete

Revision ID: 001
Revises:
Create Date: 2024-06-26 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Enable PostGIS
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # Create sequence BEFORE table that references it
    op.execute("CREATE SEQUENCE issue_timeline_seq START 1;")

    # states
    op.create_table(
        'states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # cities
    op.create_table(
        'cities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('state_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('states.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('is_pilot', sa.Boolean(), default=False),
        sa.Column('boundary_geojson', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # wards
    op.create_table(
        'wards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('city_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cities.id'), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('ward_number', sa.String(20), nullable=False),
        sa.Column('boundary_geojson', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('phone_hash', sa.String(255), nullable=False, unique=True),
        sa.Column('pseudonym', sa.String(50), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('last_active_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # authorities (organizations)
    op.create_table(
        'authorities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('city_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cities.id')),
        sa.Column('contact_email', sa.String(255)),
        sa.Column('contact_phone', sa.String(50)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # authority_users (individuals within authority org)
    op.create_table(
        'authority_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('authority_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('authorities.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='viewer'),
        sa.Column('ward_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wards.id')),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.CheckConstraint("role IN ('admin', 'supervisor', 'field_officer', 'viewer')", name='ck_authority_users_role'),
    )

    # issues
    op.create_table(
        'issues',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('ward_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wards.id'), nullable=False),
        sa.Column('city_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('cities.id')),
        sa.Column('category', sa.String(20), nullable=False, server_default='roads'),
        sa.Column('severity', sa.String(20), nullable=False, server_default='medium'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('geo_lat', sa.Numeric(10, 8), nullable=False),
        sa.Column('geo_lng', sa.Numeric(11, 8), nullable=False),
        sa.Column('location_text', sa.String(255)),
        sa.Column('state', sa.String(30), nullable=False, server_default='reported'),
        sa.Column('ai_summary', sa.Text()),
        sa.Column('ai_tags', postgresql.ARRAY(sa.Text())),
        sa.Column('confidence_ai', sa.Numeric(5, 2)),
        sa.Column('confidence_community', sa.Numeric(5, 2), server_default='100.00'),
        sa.Column('confidence_time', sa.Numeric(5, 2)),
        sa.Column('net_confidence', sa.Numeric(5, 2)),
        sa.Column('confidence_updated_at', sa.DateTime(timezone=True)),
        sa.Column('priority_score', sa.Numeric(6, 2), server_default='0'),
        sa.Column('support_count', sa.Integer(), server_default='0'),
        sa.Column('is_safety_risk', sa.Boolean(), server_default='false'),
        sa.Column('has_unverified_closure', sa.Boolean(), server_default='false'),
        sa.Column('previous_issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id')),
        sa.Column('sla_ack_deadline', sa.DateTime(timezone=True)),
        sa.Column('sla_visit_deadline', sa.DateTime(timezone=True)),
        sa.Column('sla_resolution_deadline', sa.DateTime(timezone=True)),
        sa.Column('time_decay_window_ends_at', sa.DateTime(timezone=True)),
        sa.Column('is_repeat_failure', sa.Boolean(), server_default='false'),
        sa.Column('repeat_count', sa.Integer(), server_default='0'),
        sa.Column('merged_into_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.CheckConstraint("category IN ('roads', 'water', 'garbage')", name='ck_issues_category'),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name='ck_issues_severity'),
        sa.CheckConstraint("state IN ('reported', 'acknowledged', 'visited', 'in_progress', 'resolved_claimed', 'resolved_confirmed', 'resolution_unverified', 'disputed', 'reopened', 'closed')", name='ck_issues_state'),
    )

    # Add PostGIS geometry column to issues
    op.execute("""
        ALTER TABLE issues
        ADD COLUMN location GEOMETRY(POINT, 4326)
    """)
    op.execute("""
        CREATE INDEX idx_issues_location ON issues USING GIST(location)
    """)

    # issue_media
    op.create_table(
        'issue_media',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id'), nullable=False),
        sa.Column('media_type', sa.String(20), nullable=False, server_default='complaint_photo'),
        sa.Column('s3_key', sa.String(512), nullable=False),
        sa.Column('s3_bucket', sa.String(100), nullable=False),
        sa.Column('original_filename', sa.String(255)),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('file_size', sa.BigInteger()),
        sa.Column('geo_lat', sa.Numeric(10, 8)),
        sa.Column('geo_lng', sa.Numeric(11, 8)),
        sa.Column('ai_vision_description', sa.Text()),
        sa.Column('embedding_vector', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.CheckConstraint("media_type IN ('complaint_photo', 'resolution_photo', 'visit_photo', 'audio')", name='ck_issue_media_type'),
    )

    # issue_timeline
    op.create_table(
        'issue_timeline',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id'), nullable=False),
        sa.Column('event_type', sa.String(30), nullable=False, server_default='state_change'),
        sa.Column('old_state', sa.String(30)),
        sa.Column('new_state', sa.String(30)),
        sa.Column('actor_type', sa.String(20)),
        sa.Column('actor_id', postgresql.UUID(as_uuid=True)),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB()),
        sa.Column('sequence_number', sa.BigInteger(), nullable=False, server_default=sa.text("nextval('issue_timeline_seq')")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.CheckConstraint("event_type IN ('state_change', 'sla_breach', 'silence_milestone', 'ai_analysis', 'comment', 'confidence_update', 'merge', 'repeat_failure')", name='ck_timeline_event_type'),
    )

    # issue_comments
    op.create_table(
        'issue_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('authority_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('authority_users.id')),
        sa.Column('is_agent', sa.Boolean(), server_default='false'),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('agent_metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # issue_supports
    op.create_table(
        'issue_supports',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.UniqueConstraint('issue_id', 'user_id', name='uq_issue_support'),
    )

    # bookmarks (supports issue, city, ward)
    op.create_table(
        'bookmarks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('entity_type', sa.String(20), nullable=False),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.CheckConstraint("entity_type IN ('issue', 'city', 'ward')", name='ck_bookmarks_entity_type'),
        sa.UniqueConstraint('user_id', 'entity_type', 'entity_id', name='uq_bookmark'),
    )

    # authority_notes
    op.create_table(
        'authority_notes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id'), nullable=False),
        sa.Column('authority_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('authority_users.id'), nullable=False),
        sa.Column('note_text', sa.Text(), nullable=False),
        sa.Column('is_internal', sa.Boolean(), server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # sla_extensions
    op.create_table(
        'sla_extensions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id'), nullable=False),
        sa.Column('original_deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('new_deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('authority_users.id')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # otp_store
    op.create_table(
        'otp_store',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('phone_hash', sa.String(255), nullable=False),
        sa.Column('otp_code', sa.String(10), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_used', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # agent_logs
    op.create_table(
        'agent_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('agent_name', sa.String(50), nullable=False),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('input_summary', sa.Text()),
        sa.Column('output_summary', sa.Text()),
        sa.Column('confidence_score', sa.Numeric(5, 2)),
        sa.Column('processing_time_ms', sa.Integer()),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # pattern_clusters
    op.create_table(
        'pattern_clusters',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('ward_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('wards.id'), nullable=False),
        sa.Column('category', sa.String(20)),
        sa.Column('cluster_type', sa.String(50), nullable=False),
        sa.Column('issue_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True))),
        sa.Column('summary', sa.Text()),
        sa.Column('geojson', sa.Text()),
        sa.Column('detected_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
    )

    # notifications
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
        sa.Column('issue_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issues.id')),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )

    # Indexes
    op.create_index('ix_issues_user_id', 'issues', ['user_id'])
    op.create_index('ix_issues_ward_id', 'issues', ['ward_id'])
    op.create_index('ix_issues_city_id', 'issues', ['city_id'])
    op.create_index('ix_issues_state', 'issues', ['state'])
    op.create_index('ix_issues_category', 'issues', ['category'])
    op.create_index('ix_issues_created_at', 'issues', ['created_at'])
    op.create_index('ix_issues_priority_score', 'issues', ['priority_score'])
    op.create_index('ix_issue_media_issue_id', 'issue_media', ['issue_id'])
    op.create_index('ix_issue_timeline_issue_id', 'issue_timeline', ['issue_id'])
    op.create_index('ix_issue_timeline_sequence', 'issue_timeline', ['issue_id', 'sequence_number'])
    op.create_index('ix_issue_comments_issue_id', 'issue_comments', ['issue_id'])
    op.create_index('ix_agent_logs_issue_id', 'agent_logs', ['issue_id'])
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_otp_store_phone_hash', 'otp_store', ['phone_hash'])
    op.create_index('ix_authority_notes_issue_id', 'authority_notes', ['issue_id'])
    op.create_index('ix_sla_extensions_issue_id', 'sla_extensions', ['issue_id'])


def downgrade():
    op.execute("DROP SEQUENCE IF EXISTS issue_timeline_seq;")
    op.drop_table('notifications')
    op.drop_table('pattern_clusters')
    op.drop_table('agent_logs')
    op.drop_table('otp_store')
    op.drop_table('sla_extensions')
    op.drop_table('authority_notes')
    op.drop_table('bookmarks')
    op.drop_table('issue_supports')
    op.drop_table('issue_comments')
    op.drop_table('issue_timeline')
    op.drop_table('issue_media')
    op.drop_table('issues')
    op.drop_table('authority_users')
    op.drop_table('authorities')
    op.drop_table('users')
    op.drop_table('wards')
    op.drop_table('cities')
    op.drop_table('states')