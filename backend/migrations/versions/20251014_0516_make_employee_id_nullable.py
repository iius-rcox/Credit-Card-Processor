"""make employee_id nullable in transactions

Revision ID: 20251014_0516
Revises: 7833dabac7d8
Create Date: 2025-10-14 05:16:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20251014_0516'
down_revision: Union[str, None] = '7833dabac7d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Make employee_id column nullable in transactions table.

    This allows transactions to be saved even when the employee name
    from the PDF cannot be resolved to an employee record or alias.
    The incomplete_flag will be set to True in such cases.
    """
    # Make employee_id nullable
    op.alter_column(
        'transactions',
        'employee_id',
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=True
    )


def downgrade() -> None:
    """
    Revert employee_id column to NOT NULL.

    WARNING: This will fail if there are any transactions with NULL employee_id.
    Clean up orphaned transactions before downgrading.
    """
    # Make employee_id NOT NULL again
    op.alter_column(
        'transactions',
        'employee_id',
        existing_type=sa.dialects.postgresql.UUID(),
        nullable=False
    )
