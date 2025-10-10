"""add_progress_tracking

Revision ID: 34992237d751
Revises:
Create Date: 2025-10-08 10:14:54.912510

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34992237d751'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add progress tracking fields to sessions table."""
    # Add processing_progress JSONB column for flexible progress state
    op.add_column(
        'sessions',
        sa.Column('processing_progress', sa.dialects.postgresql.JSONB, nullable=True)
    )

    # Add current_phase VARCHAR column for fast filtering
    op.add_column(
        'sessions',
        sa.Column('current_phase', sa.String(50), nullable=True)
    )

    # Add overall_percentage DECIMAL column for cached aggregate
    op.add_column(
        'sessions',
        sa.Column('overall_percentage', sa.Numeric(5, 2), nullable=True)
    )

    # Add index on current_phase for efficient queries
    op.create_index(
        'idx_sessions_current_phase',
        'sessions',
        ['current_phase'],
        postgresql_where=sa.text('current_phase IS NOT NULL')
    )

    # Add check constraint for overall_percentage range
    op.create_check_constraint(
        'chk_sessions_overall_percentage',
        'sessions',
        sa.text('overall_percentage >= 0 AND overall_percentage <= 100')
    )

    # Add check constraint for valid current_phase values
    op.create_check_constraint(
        'chk_sessions_current_phase',
        'sessions',
        sa.text(
            "current_phase IN ('upload', 'processing', 'matching', "
            "'report_generation', 'completed', 'failed')"
        )
    )


def downgrade() -> None:
    """Remove progress tracking fields from sessions table."""
    # Drop constraints
    op.drop_constraint('chk_sessions_current_phase', 'sessions', type_='check')
    op.drop_constraint('chk_sessions_overall_percentage', 'sessions', type_='check')

    # Drop index
    op.drop_index('idx_sessions_current_phase', table_name='sessions')

    # Drop columns
    op.drop_column('sessions', 'overall_percentage')
    op.drop_column('sessions', 'current_phase')
    op.drop_column('sessions', 'processing_progress')
