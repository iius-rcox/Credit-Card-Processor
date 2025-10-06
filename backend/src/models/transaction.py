"""
Transaction model - Credit card or expense transactions to be reconciled.

This module defines the Transaction SQLAlchemy model representing financial
transactions extracted from credit card statements.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class Transaction(Base):
    """
    Transaction model representing credit card/expense transactions.

    Transactions are linked to employees and sessions. Each transaction can have
    one match result linking it to a receipt. Raw transaction data is stored in
    JSONB format for flexibility.

    Attributes:
        id: Unique transaction identifier (UUID)
        session_id: Parent session reference (FK)
        employee_id: Employee who made the transaction (FK)
        transaction_date: Date of transaction
        post_date: Date transaction posted to account (optional)
        amount: Transaction amount (positive values only)
        currency: ISO 4217 currency code (default: USD)
        merchant_name: Merchant/vendor name
        merchant_category: MCC category (optional)
        description: Transaction description/memo (optional)
        card_last_four: Last 4 digits of card used (optional)
        reference_number: Bank reference or transaction ID (optional)
        raw_data: Original transaction data from source file (JSONB)
        created_at: Record creation timestamp
    """

    __tablename__ = "transactions"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Foreign keys
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False
    )

    # Transaction dates
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    post_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True
    )

    # Financial data
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        CHAR(3),
        nullable=False,
        server_default="USD"
    )

    # Merchant information
    merchant_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    merchant_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Card information
    card_last_four: Mapped[Optional[str]] = mapped_column(
        CHAR(4),
        nullable=True
    )

    reference_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    # Raw data storage
    raw_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="transactions"
    )

    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="transactions"
    )

    match_result: Mapped[Optional["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="transaction",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="chk_transactions_amount"
        ),
        CheckConstraint(
            "post_date IS NULL OR post_date >= transaction_date",
            name="chk_transactions_post_date"
        ),
        UniqueConstraint(
            "session_id",
            "reference_number",
            name="uq_transactions_reference"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, date={self.transaction_date}, "
            f"amount={self.amount}, merchant={self.merchant_name})>"
        )
