"""
Session model - Primary entity representing a reconciliation workflow instance.

This module defines the Session SQLAlchemy model with automatic 90-day expiration.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    Computed,
    DateTime,
    Integer,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Create the declarative base
Base = declarative_base()


class Session(Base):
    """
    Session model representing a single reconciliation workflow instance.

    Sessions automatically expire 90 days after creation. All related entities
    (employees, transactions, receipts, match_results) are cascade-deleted
    when the session is removed.

    Attributes:
        id: Unique session identifier (UUID)
        created_at: Session creation timestamp
        expires_at: Auto-calculated expiration (created_at + 90 days)
        status: Current processing state (processing/completed/failed/expired)
        upload_count: Number of files uploaded
        total_transactions: Count of transactions processed
        total_receipts: Count of receipts uploaded
        matched_count: Count of successful matches
        updated_at: Last modification timestamp
        processing_progress: JSONB field containing detailed progress tracking
        current_phase: Cached current phase for filtering (upload/processing/matching/report_generation/completed/failed)
        overall_percentage: Cached aggregate progress percentage (0.00-100.00)
    """

    __tablename__ = "sessions"

    # Status validation constants
    VALID_STATUSES = [
        'processing',
        'extracting',
        'matching',
        'completed',
        'failed',
        'expired'
    ]

    VALID_TRANSITIONS = {
        'processing': ['extracting', 'matching', 'completed', 'failed'],
        'extracting': ['matching', 'completed', 'failed'],
        'matching': ['completed', 'failed'],
        'completed': [],
        'failed': [],
        'expired': []
    }

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=datetime.utcnow
    )

    # Status and counts
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="processing"
    )

    upload_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0"
    )

    total_transactions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0"
    )

    total_receipts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0"
    )

    matched_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0"
    )

    # Progress tracking fields (added for better status updates)
    processing_progress: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        default=None,
        comment="Complete progress state snapshot in JSONB format"
    )

    current_phase: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default=None,
        index=True,  # Index for efficient filtering
        comment="Cached current phase for filtering"
    )

    overall_percentage: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2),  # Allows 0.00 to 100.00
        nullable=True,
        default=0.00,
        server_default="0.00",
        comment="Cached aggregate progress percentage"
    )

    summary: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        default=None,
        comment="Summary text for frontend display"
    )

    # Relationships (cascade delete to all child entities)
    employees: Mapped[list["Employee"]] = relationship(
        "Employee",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    receipts: Mapped[list["Receipt"]] = relationship(
        "Receipt",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    match_results: Mapped[list["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="session",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing', 'extracting', 'matching', 'completed', 'failed', 'expired')",
            name="chk_sessions_status"
        ),
        CheckConstraint(
            "upload_count >= 0",
            name="chk_sessions_upload_count"
        ),
        CheckConstraint(
            "total_transactions >= 0",
            name="chk_sessions_total_transactions"
        ),
        CheckConstraint(
            "total_receipts >= 0",
            name="chk_sessions_total_receipts"
        ),
        CheckConstraint(
            "matched_count >= 0",
            name="chk_sessions_matched_count"
        ),
        CheckConstraint(
            "overall_percentage >= 0 AND overall_percentage <= 100",
            name="chk_sessions_overall_percentage"
        ),
        CheckConstraint(
            "current_phase IS NULL OR current_phase IN ('upload', 'processing', 'matching', 'report_generation', 'completed', 'failed')",
            name="chk_sessions_current_phase"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Session(id={self.id}, status={self.status}, "
            f"created_at={self.created_at}, expires_at={self.expires_at})>"
        )

    @classmethod
    def validate_status_transition(cls, from_status: str, to_status: str) -> bool:
        """
        Validate if a status transition is allowed.

        Args:
            from_status: Current session status
            to_status: Desired new status

        Returns:
            True if transition is valid, False otherwise

        Raises:
            ValueError: If either status is not in VALID_STATUSES

        Example:
            >>> Session.validate_status_transition('processing', 'matching')
            True
            >>> Session.validate_status_transition('completed', 'processing')
            False
        """
        import logging
        logger = logging.getLogger(__name__)

        # Validate that both statuses are in the allowed list
        if to_status not in cls.VALID_STATUSES:
            raise ValueError(f"Invalid status: {to_status}. Must be one of {cls.VALID_STATUSES}")

        if from_status not in cls.VALID_STATUSES:
            raise ValueError(f"Invalid current status: {from_status}. Must be one of {cls.VALID_STATUSES}")

        # Check if transition is allowed
        allowed_transitions = cls.VALID_TRANSITIONS.get(from_status, [])
        if to_status not in allowed_transitions:
            logger.warning(
                f"Unusual status transition: {from_status} -> {to_status}. "
                f"Allowed transitions from {from_status}: {allowed_transitions}"
            )
            return False

        return True
