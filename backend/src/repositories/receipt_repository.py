"""
ReceiptRepository - Data access layer for Receipt entities.

This module provides CRUD operations and queries for Receipt records.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.receipt import Receipt


class ReceiptRepository:
    """
    Repository for Receipt entity operations.

    Provides methods for creating, retrieving, updating, and querying receipts.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def create_receipt(self, session_id: UUID, data: dict) -> Receipt:
        """
        Create a new receipt.

        Args:
            session_id: UUID of the parent session
            data: Dictionary with receipt data

        Returns:
            Created Receipt instance

        Example:
            receipt = await repo.create_receipt(
                session_id=uuid4(),
                data={
                    "receipt_date": date(2025, 10, 1),
                    "amount": Decimal("125.50"),
                    "vendor_name": "Office Depot",
                    "file_name": "receipt_001.pdf",
                    "file_path": "/uploads/session-id/receipt_001.pdf",
                    "file_size": 102400,
                    "mime_type": "application/pdf",
                    "extracted_data": {"vendor": "Office Depot", "total": 125.50}
                }
            )
        """
        receipt_data = {"session_id": session_id, **data}
        receipt = Receipt(**receipt_data)
        self.db.add(receipt)
        await self.db.flush()
        await self.db.refresh(receipt)
        return receipt

    async def bulk_create_receipts(self, receipts: list[dict]) -> list[Receipt]:
        """
        Bulk create receipts (batch insert).

        Args:
            receipts: List of receipt data dictionaries (must include session_id)

        Returns:
            List of created Receipt instances

        Example:
            receipts = await repo.bulk_create_receipts([
                {
                    "session_id": uuid4(),
                    "receipt_date": date(2025, 10, 1),
                    "amount": Decimal("100.00"),
                    "vendor_name": "Store A",
                    "file_name": "receipt1.pdf",
                    "file_path": "/path/to/receipt1.pdf",
                    "file_size": 50000,
                    "mime_type": "application/pdf",
                    "extracted_data": {}
                },
                ...
            ])
        """
        receipt_objects = [Receipt(**receipt_data) for receipt_data in receipts]
        self.db.add_all(receipt_objects)
        await self.db.flush()

        # Refresh all objects
        for receipt in receipt_objects:
            await self.db.refresh(receipt)

        return receipt_objects

    async def get_receipts_by_session(self, session_id: UUID) -> list[Receipt]:
        """
        Get all receipts for a session.

        Args:
            session_id: UUID of the session

        Returns:
            List of Receipt instances ordered by receipt date

        Example:
            receipts = await repo.get_receipts_by_session(session_id)
        """
        stmt = (
            select(Receipt)
            .where(Receipt.session_id == session_id)
            .order_by(Receipt.receipt_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_unmatched_receipts(self, session_id: UUID) -> list[Receipt]:
        """
        Get receipts without match results (unmatched receipts).

        Args:
            session_id: UUID of the session

        Returns:
            List of Receipt instances that haven't been matched

        Example:
            unmatched = await repo.get_unmatched_receipts(session_id)
        """
        from ..models.match_result import MatchResult

        # Use LEFT JOIN to find receipts without match results
        stmt = (
            select(Receipt)
            .outerjoin(MatchResult, Receipt.id == MatchResult.receipt_id)
            .where(Receipt.session_id == session_id)
            .where(MatchResult.id.is_(None))
            .order_by(Receipt.receipt_date.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def update_processing_status(
        self,
        receipt_id: UUID,
        status: str,
        error_message: Optional[str] = None,
        ocr_confidence: Optional[float] = None,
        extracted_data: Optional[dict] = None
    ) -> None:
        """
        Update receipt processing status and OCR results.

        Args:
            receipt_id: UUID of the receipt
            status: New processing status (pending/processing/completed/failed)
            error_message: Error details if status is 'failed'
            ocr_confidence: OCR confidence score (0.0-1.0)
            extracted_data: Extracted data from OCR

        Example:
            await repo.update_processing_status(
                receipt_id=uuid4(),
                status="completed",
                ocr_confidence=0.95,
                extracted_data={"vendor": "Office Depot", "total": 125.50}
            )
        """
        update_values = {
            "processing_status": status,
            "processed_at": datetime.utcnow()
        }

        if error_message is not None:
            update_values["error_message"] = error_message

        if ocr_confidence is not None:
            update_values["ocr_confidence"] = ocr_confidence

        if extracted_data is not None:
            update_values["extracted_data"] = extracted_data

        stmt = (
            update(Receipt)
            .where(Receipt.id == receipt_id)
            .values(**update_values)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_receipt_by_id(self, receipt_id: UUID) -> Optional[Receipt]:
        """
        Get receipt by ID.

        Args:
            receipt_id: UUID of the receipt

        Returns:
            Receipt instance if found, None otherwise
        """
        stmt = select(Receipt).where(Receipt.id == receipt_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_receipts_by_status(
        self, status: str, limit: Optional[int] = None
    ) -> list[Receipt]:
        """
        Get receipts by processing status.

        Args:
            status: Processing status to filter by
            limit: Maximum number of receipts to return

        Returns:
            List of Receipt instances with specified status

        Example:
            pending_receipts = await repo.get_receipts_by_status("pending", limit=10)
        """
        stmt = (
            select(Receipt)
            .where(Receipt.processing_status == status)
            .order_by(Receipt.created_at)
        )

        if limit:
            stmt = stmt.limit(limit)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
