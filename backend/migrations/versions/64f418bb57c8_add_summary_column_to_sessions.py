"""add_summary_column_to_sessions

Revision ID: 64f418bb57c8
Revises: 34992237d751
Create Date: 2025-10-09 22:51:06.380986

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64f418bb57c8'
down_revision: Union[str, None] = '34992237d751'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add summary column to sessions table
    op.add_column('sessions', sa.Column('summary', sa.String(length=500), nullable=True, comment='Summary text for frontend display'))


def downgrade() -> None:
    # Remove summary column from sessions table
    op.drop_column('sessions', 'summary')
