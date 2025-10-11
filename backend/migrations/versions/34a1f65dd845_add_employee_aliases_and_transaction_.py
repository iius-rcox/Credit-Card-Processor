"""add_employee_aliases_and_transaction_flags

Revision ID: 34a1f65dd845
Revises: 64f418bb57c8
Create Date: 2025-10-10 18:31:50.533515

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '34a1f65dd845'
down_revision: Union[str, None] = '64f418bb57c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create employee_aliases table
    op.create_table(
        'employee_aliases',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('extracted_name', sa.String(length=255), nullable=False),
        sa.Column('employee_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('extracted_name')
    )

    # Create indexes on employee_aliases
    op.create_index('idx_employee_aliases_extracted_name', 'employee_aliases', ['extracted_name'])
    op.create_index('idx_employee_aliases_employee_id', 'employee_aliases', ['employee_id'])

    # Add new columns to transactions table
    op.add_column('transactions', sa.Column('incomplete_flag', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('transactions', sa.Column('is_credit', sa.Boolean(), nullable=False, server_default='false'))

    # Create partial index on incomplete_flag
    op.execute('''
        CREATE INDEX idx_transactions_incomplete
        ON transactions(incomplete_flag)
        WHERE incomplete_flag = TRUE
    ''')

    # Remove positive-only constraint on amount (if exists)
    # Note: This may vary by database - using safe approach
    op.execute('ALTER TABLE transactions DROP CONSTRAINT IF EXISTS chk_transactions_amount')


def downgrade() -> None:
    # Remove partial index
    op.drop_index('idx_transactions_incomplete', table_name='transactions')

    # Remove columns from transactions
    op.drop_column('transactions', 'is_credit')
    op.drop_column('transactions', 'incomplete_flag')

    # Drop indexes on employee_aliases
    op.drop_index('idx_employee_aliases_employee_id', table_name='employee_aliases')
    op.drop_index('idx_employee_aliases_extracted_name', table_name='employee_aliases')

    # Drop employee_aliases table
    op.drop_table('employee_aliases')

    # Re-add constraint on transactions.amount (if it was present originally)
    # op.execute('ALTER TABLE transactions ADD CONSTRAINT chk_transactions_amount CHECK (amount > 0)')
