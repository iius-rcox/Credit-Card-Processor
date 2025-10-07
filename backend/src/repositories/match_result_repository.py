"""
MatchResultRepository - Data access layer for MatchResult entities.

This module provides CRUD operations and queries for MatchResult records.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.match_result import MatchResult


class MatchResultRepository:
    """
    Repository for MatchResult entity operations.

    Provides methods for creating, retrieving, updating, and querying match results.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def create_match_result(
        self,
        session_id: UUID,
        transaction_id: UUID,
        receipt_id: Optional[UUID],
        data: dict
    ) -> MatchResult:
        """
        Create a new match result.

        Args:
            session_id: UUID of the parent session
            transaction_id: UUID of the transaction
            receipt_id: UUID of the receipt (None for unmatched)
            data: Dictionary with match result data

        Returns:
            Created MatchResult instance

        Example:
            match = await repo.create_match_result(
                session_id=uuid4(),
                transaction_id=uuid4(),
                receipt_id=uuid4(),
                data={
                    "confidence_score": Decimal("0.95"),
                    "match_status": "matched",
                    "match_reason": "Exact amount and date match",
                    "amount_difference": Decimal("0.00"),
                    "date_difference_days": 0,
                    "merchant_similarity": Decimal("0.92"),
                    "matching_factors": {
                        "amount_match": 1.0,
                        "date_proximity": 1.0,
                        "merchant_match": 0.92
                    }
                }
            )
        """
        match_data = {
            "session_id": session_id,
            "transaction_id": transaction_id,
            "receipt_id": receipt_id,
            **data
        }
        match_result = MatchResult(**match_data)
        self.db.add(match_result)
        await self.db.flush()
        await self.db.refresh(match_result)
        return match_result

    async def bulk_create_match_results(
        self, matches: list[dict]
    ) -> list[MatchResult]:
        """
        Bulk create match results (batch insert).

        Args:
            matches: List of match result data dictionaries
                    (must include session_id, transaction_id, receipt_id)

        Returns:
            List of created MatchResult instances

        Example:
            matches = await repo.bulk_create_match_results([
                {
                    "session_id": uuid4(),
                    "transaction_id": uuid4(),
                    "receipt_id": uuid4(),
                    "confidence_score": Decimal("0.95"),
                    "match_status": "matched",
                    "match_reason": "Strong match"
                },
                ...
            ])
        """
        match_objects = [MatchResult(**match_data) for match_data in matches]
        self.db.add_all(match_objects)
        await self.db.flush()

        # Refresh all objects
        for match in match_objects:
            await self.db.refresh(match)

        return match_objects

    async def get_match_results_by_session(
        self, session_id: UUID
    ) -> list[MatchResult]:
        """
        Get all match results for a session.

        Args:
            session_id: UUID of the session

        Returns:
            List of MatchResult instances ordered by confidence score

        Example:
            matches = await repo.get_match_results_by_session(session_id)
        """
        stmt = (
            select(MatchResult)
            .where(MatchResult.session_id == session_id)
            .options(
                selectinload(MatchResult.transaction),
                selectinload(MatchResult.receipt)
            )
            .order_by(MatchResult.confidence_score.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_match_by_transaction(
        self, transaction_id: UUID
    ) -> Optional[MatchResult]:
        """
        Get match result by transaction ID (unique constraint).

        Args:
            transaction_id: UUID of the transaction

        Returns:
            MatchResult instance if found, None otherwise

        Example:
            match = await repo.get_match_by_transaction(transaction_id)
        """
        stmt = (
            select(MatchResult)
            .where(MatchResult.transaction_id == transaction_id)
            .options(
                selectinload(MatchResult.transaction),
                selectinload(MatchResult.receipt)
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_match_by_id(self, match_id: UUID) -> Optional[MatchResult]:
        """
        Get match result by ID.

        Args:
            match_id: UUID of the match result

        Returns:
            MatchResult instance if found, None otherwise
        """
        stmt = select(MatchResult).where(MatchResult.id == match_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_match_review(
        self,
        match_id: UUID,
        status: str,
        reviewed_by: str,
        notes: Optional[str] = None
    ) -> None:
        """
        Update match result with manual review information.

        Args:
            match_id: UUID of the match result
            status: New match status (manual_review/approved/rejected)
            reviewed_by: Username/ID of reviewer
            notes: Optional review notes

        Example:
            await repo.update_match_review(
                match_id=uuid4(),
                status="approved",
                reviewed_by="john.doe@example.com",
                notes="Verified with receipt copy"
            )
        """
        update_values = {
            "match_status": status,
            "reviewed_by": reviewed_by,
            "reviewed_at": datetime.utcnow()
        }

        if notes is not None:
            update_values["notes"] = notes

        stmt = (
            update(MatchResult)
            .where(MatchResult.id == match_id)
            .values(**update_values)
        )
        await self.db.execute(stmt)
        await self.db.flush()

    async def get_matches_by_status(
        self, session_id: UUID, status: str
    ) -> list[MatchResult]:
        """
        Get match results filtered by status.

        Args:
            session_id: UUID of the session
            status: Match status to filter by

        Returns:
            List of MatchResult instances with specified status

        Example:
            unmatched = await repo.get_matches_by_status(session_id, "unmatched")
        """
        stmt = (
            select(MatchResult)
            .where(MatchResult.session_id == session_id)
            .where(MatchResult.match_status == status)
            .options(
                selectinload(MatchResult.transaction),
                selectinload(MatchResult.receipt)
            )
            .order_by(MatchResult.confidence_score.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_matches_for_review(
        self, session_id: UUID, confidence_threshold: float = 0.7
    ) -> list[MatchResult]:
        """
        Get match results that need manual review.

        Args:
            session_id: UUID of the session
            confidence_threshold: Confidence score below which matches need review

        Returns:
            List of MatchResult instances needing review

        Example:
            needs_review = await repo.get_matches_for_review(session_id, 0.7)
        """
        stmt = (
            select(MatchResult)
            .where(MatchResult.session_id == session_id)
            .where(
                (MatchResult.match_status == "manual_review") |
                (MatchResult.confidence_score < confidence_threshold)
            )
            .options(
                selectinload(MatchResult.transaction),
                selectinload(MatchResult.receipt)
            )
            .order_by(MatchResult.confidence_score.asc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
