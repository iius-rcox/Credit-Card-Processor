"""
MatchResult model - Results of matching transactions to receipts.

This module defines the MatchResult SQLAlchemy model representing the fuzzy
matching results between transactions and receipts.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class MatchResult(Base):
    """
    MatchResult model representing transaction-to-receipt matching results.

    Each transaction gets exactly one MatchResult (enforced by unique constraint).
    The MatchResult may link to a receipt (matched) or be null (unmatched).
    Confidence scores and matching factors help users understand the match quality.

    Attributes:
        id: Unique match result identifier (UUID)
        session_id: Parent session reference (FK)
        transaction_id: Transaction being matched (FK, unique)
        receipt_id: Matched receipt (FK, nullable for unmatched)
        confidence_score: Match confidence (0.0-1.0)
        match_status: Match outcome (matched/unmatched/manual_review/approved/rejected)
        match_reason: Explanation of match logic or failure reason
        amount_difference: Absolute difference between amounts
        date_difference_days: Days between transaction and receipt dates
        merchant_similarity: Fuzzy string match score (0.0-1.0)
        matching_factors: Detailed breakdown of matching algorithm (JSONB)
        reviewed_by: User who performed manual review (optional)
        reviewed_at: Manual review timestamp (optional)
        notes: User notes from manual review (optional)
        created_at: Match execution timestamp
    """

    __tablename__ = "matchresults"

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

    transaction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    receipt_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("receipts.id", ondelete="SET NULL"),
        nullable=True
    )

    # Match metrics
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4),
        nullable=False
    )

    match_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    match_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    amount_difference: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

    date_difference_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    merchant_similarity: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True
    )

    matching_factors: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True
    )

    # Manual review fields
    reviewed_by: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
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
        back_populates="match_results"
    )

    transaction: Mapped["Transaction"] = relationship(
        "Transaction",
        back_populates="match_result"
    )

    receipt: Mapped[Optional["Receipt"]] = relationship(
        "Receipt",
        back_populates="match_result"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "confidence_score BETWEEN 0 AND 1",
            name="chk_matchresults_confidence"
        ),
        CheckConstraint(
            "match_status IN ('matched', 'unmatched', 'manual_review', 'approved', 'rejected')",
            name="chk_matchresults_status"
        ),
        CheckConstraint(
            "date_difference_days IS NULL OR date_difference_days >= 0",
            name="chk_matchresults_date_diff"
        ),
        CheckConstraint(
            "merchant_similarity IS NULL OR (merchant_similarity BETWEEN 0 AND 1)",
            name="chk_matchresults_merchant_sim"
        ),
        CheckConstraint(
            "(match_status = 'matched' AND receipt_id IS NOT NULL) OR (match_status != 'matched')",
            name="chk_matchresults_matched_receipt"
        ),
        UniqueConstraint(
            "transaction_id",
            name="uq_matchresults_transaction"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MatchResult(id={self.id}, status={self.match_status}, "
            f"confidence={self.confidence_score})>"
        )
