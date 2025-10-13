"""add_extracting_matching_status

Revision ID: 20251013_1622
Revises: 64f418bb57c8
Create Date: 2025-10-13 16:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251013_1622'
down_revision: Union[str, None] = '64f418bb57c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add 'extracting' and 'matching' statuses to the session status constraint.

    This fixes the bug where sessions get stuck in 'processing' status because
    the code tries to transition to 'matching' which violates the database constraint.
    """
    # Drop the old constraint
    op.drop_constraint('chk_sessions_status', 'sessions', type_='check')

    # Create the new constraint with additional statuses
    op.create_check_constraint(
        'chk_sessions_status',
        'sessions',
        "status IN ('processing', 'extracting', 'matching', 'completed', 'failed', 'expired')"
    )


def downgrade() -> None:
    """
    Revert to the original constraint (removes 'extracting' and 'matching').

    Warning: If any sessions have status='extracting' or status='matching',
    this downgrade will fail due to constraint violation.
    """
    # Drop the new constraint
    op.drop_constraint('chk_sessions_status', 'sessions', type_='check')

    # Recreate the old constraint
    op.create_check_constraint(
        'chk_sessions_status',
        'sessions',
        "status IN ('processing', 'completed', 'failed', 'expired')"
    )
