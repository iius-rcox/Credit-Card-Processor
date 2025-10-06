"""
Receipt model - Uploaded receipt images and extracted OCR data.

This module defines the Receipt SQLAlchemy model representing receipt uploads
with OCR extraction results.
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
    Integer,
    Numeric,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .session import Base


class Receipt(Base):
    """
    Receipt model representing uploaded receipt images and OCR data.

    Receipts are processed via OCR to extract date, amount, vendor, and line items.
    The extracted data is stored in JSONB format for flexibility. Each receipt
    can be matched to one transaction.

    Attributes:
        id: Unique receipt identifier (UUID)
        session_id: Parent session reference (FK)
        receipt_date: Date on receipt
        amount: Total amount on receipt (positive values only)
        currency: ISO 4217 currency code (default: USD)
        vendor_name: Vendor name from receipt
        file_name: Original uploaded filename
        file_path: Storage path or blob reference
        file_size: File size in bytes
        mime_type: MIME type (image/jpeg, application/pdf, etc.)
        ocr_confidence: OCR extraction confidence score (0.0-1.0)
        extracted_data: Full OCR extraction results (JSONB)
        processing_status: OCR processing state
        error_message: Error details if processing failed
        created_at: Upload timestamp
        processed_at: OCR completion timestamp
    """

    __tablename__ = "receipts"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        server_default=text("gen_random_uuid()")
    )

    # Foreign key
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False
    )

    # Receipt data
    receipt_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False
    )

    currency: Mapped[str] = mapped_column(
        CHAR(3),
        nullable=False,
        server_default="USD"
    )

    vendor_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # File metadata
    file_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    file_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # OCR data
    ocr_confidence: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 4),
        nullable=True
    )

    extracted_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
    )

    # Processing status
    processing_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="pending"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("NOW()")
    )

    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="receipts"
    )

    match_result: Mapped[Optional["MatchResult"]] = relationship(
        "MatchResult",
        back_populates="receipt",
        uselist=False
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="chk_receipts_amount"
        ),
        CheckConstraint(
            "file_size > 0",
            name="chk_receipts_file_size"
        ),
        CheckConstraint(
            "ocr_confidence IS NULL OR (ocr_confidence BETWEEN 0 AND 1)",
            name="chk_receipts_ocr_confidence"
        ),
        CheckConstraint(
            "processing_status IN ('pending', 'processing', 'completed', 'failed')",
            name="chk_receipts_status"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Receipt(id={self.id}, date={self.receipt_date}, "
            f"amount={self.amount}, vendor={self.vendor_name})>"
        )
