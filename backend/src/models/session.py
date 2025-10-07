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
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


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
    """

    __tablename__ = "sessions"

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
        Computed("created_at + INTERVAL '90 days'"),
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
            "status IN ('processing', 'completed', 'failed', 'expired')",
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
    )

    def __repr__(self) -> str:
        return (
            f"<Session(id={self.id}, status={self.status}, "
            f"created_at={self.created_at}, expires_at={self.expires_at})>"
        )
