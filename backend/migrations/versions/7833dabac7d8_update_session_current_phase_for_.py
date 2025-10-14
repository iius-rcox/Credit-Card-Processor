"""update_session_current_phase_for_extracting

Revision ID: 7833dabac7d8
Revises: 34631fc059d2
Create Date: 2025-10-13 21:43:57.458759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7833dabac7d8'
down_revision: Union[str, None] = '34631fc059d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old constraint
    op.drop_constraint('chk_sessions_current_phase', 'sessions', type_='check')

    # Add the new constraint with 'extracting' phase included
    op.create_check_constraint(
        'chk_sessions_current_phase',
        'sessions',
        "current_phase IS NULL OR current_phase IN ('upload', 'processing', 'extracting', 'matching', 'report_generation', 'completed', 'failed')"
    )


def downgrade() -> None:
    # Drop the new constraint
    op.drop_constraint('chk_sessions_current_phase', 'sessions', type_='check')

    # Restore the old constraint without 'extracting'
    op.create_check_constraint(
        'chk_sessions_current_phase',
        'sessions',
        "current_phase IS NULL OR current_phase IN ('upload', 'processing', 'matching', 'report_generation', 'completed', 'failed')"
    )
