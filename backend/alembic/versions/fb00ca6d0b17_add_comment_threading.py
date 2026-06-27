"""add_comment_threading

Revision ID: fb00ca6d0b17
Revises: 001_initial_schema
Create Date: 2026-06-27 21:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fb00ca6d0b17'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add threading columns to issue_comments
    op.add_column('issue_comments', sa.Column('parent_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('issue_comments.id'), nullable=True))
    op.add_column('issue_comments', sa.Column('author_type', sa.String(20), server_default='citizen', nullable=False))
    op.add_column('issue_comments', sa.Column('author_label', sa.String(150), nullable=True))
    
    # Create indexes
    op.create_index('ix_issue_comments_parent_id', 'issue_comments', ['parent_id'])
    op.create_index('ix_issue_comments_issue_id_parent', 'issue_comments', ['issue_id', 'parent_id'])


def downgrade() -> None:
    op.drop_index('ix_issue_comments_issue_id_parent', table_name='issue_comments')
    op.drop_index('ix_issue_comments_parent_id', table_name='issue_comments')
    op.drop_column('issue_comments', 'author_label')
    op.drop_column('issue_comments', 'author_type')
    op.drop_column('issue_comments', 'parent_id')
