"""
SessionRepository - Data access layer for Session entities.

This module provides CRUD operations and queries for Session records using
SQLAlchemy 2.0 async style.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.session import Session


class SessionRepository:
    """
    Repository for Session entity operations.

    Provides methods for creating, retrieving, updating, and deleting sessions
    with proper 90-day window filtering.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def create_session(self, data: dict) -> Session:
        """
        Create a new session.

        Args:
            data: Dictionary with session data (status, upload_count, etc.)

        Returns:
            Created Session instance

        Example:
            session = await repo.create_session({
                "status": "processing",
                "upload_count": 5
            })
        """
        session = Session(**data)
        self.db.add(session)
        await self.db.flush()
        await self.db.refresh(session)
        return session

    async def get_session_by_id(self, session_id: UUID) -> Optional[Session]:
        """
        Retrieve session by ID with 90-day window check.

        Args:
            session_id: UUID of the session

        Returns:
            Session instance if found and not expired, None otherwise

        Note:
            Only returns sessions where expires_at > NOW()
        """
        stmt = (
            select(Session)
            .where(Session.id == session_id)
            .where(Session.expires_at > func.now())
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sessions(
        self, page: int = 1, page_size: int = 50
    ) -> tuple[list[Session], int]:
        """
        List sessions with pagination and 90-day window filtering.

        Args:
            page: Page number (1-based)
            page_size: Number of sessions per page (default: 50, max: 100)

        Returns:
            Tuple of (sessions list, total count)

        Example:
            sessions, total = await repo.list_sessions(page=1, page_size=50)
        """
        # Enforce max page size
        page_size = min(page_size, 100)
        offset = (page - 1) * page_size

        # Count total sessions in 90-day window
        count_stmt = (
            select(func.count(Session.id))
            .where(Session.expires_at > func.now())
        )
        count_result = await self.db.execute(count_stmt)
        total = count_result.scalar_one()

        # Get paginated sessions
        stmt = (
            select(Session)
            .where(Session.expires_at > func.now())
            .order_by(Session.created_at.desc())
            .limit(page_size)
            .offset(offset)
        )
        result = await self.db.execute(stmt)
        sessions = list(result.scalars().all())

        return sessions, total

    async def delete_session(self, session_id: UUID) -> bool:
        """
        Delete a session by ID (cascade deletes all related records).

        Args:
            session_id: UUID of the session to delete

        Returns:
            True if session was deleted, False if not found

        Note:
            Cascade deletion removes all employees, transactions, receipts,
            and match_results associated with this session.
        """
        stmt = delete(Session).where(Session.id == session_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount > 0

    async def delete_expired_sessions(self, days: int = 90) -> int:
        """
        Delete sessions older than specified days (cleanup job).

        Args:
            days: Number of days to retain (default: 90)

        Returns:
            Count of deleted sessions

        Note:
            This is typically run by a scheduled cleanup job. Sessions with
            status='processing' are not deleted to prevent data loss.
        """
        expiration_date = datetime.utcnow() - timedelta(days=days)
        stmt = (
            delete(Session)
            .where(Session.created_at < expiration_date)
            .where(Session.status != "processing")
        )
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount

    async def update_session_counts(self, session_id: UUID) -> None:
        """
        Recalculate and update session counts from child records.

        Args:
            session_id: UUID of the session to update

        Note:
            Updates total_transactions, total_receipts, and matched_count
            based on actual database counts.
        """
        # This would typically be done with subqueries, but for simplicity
        # we'll fetch the session and update it
        session = await self.get_session_by_id(session_id)
        if not session:
            return

        # Count transactions
        from ..models.transaction import Transaction
        trans_count_stmt = (
            select(func.count(Transaction.id))
            .where(Transaction.session_id == session_id)
        )
        trans_result = await self.db.execute(trans_count_stmt)
        total_transactions = trans_result.scalar_one()

        # Count receipts
        from ..models.receipt import Receipt
        receipt_count_stmt = (
            select(func.count(Receipt.id))
            .where(Receipt.session_id == session_id)
        )
        receipt_result = await self.db.execute(receipt_count_stmt)
        total_receipts = receipt_result.scalar_one()

        # Count matched results
        from ..models.match_result import MatchResult
        match_count_stmt = (
            select(func.count(MatchResult.id))
            .where(MatchResult.session_id == session_id)
            .where(MatchResult.match_status == "matched")
        )
        match_result = await self.db.execute(match_count_stmt)
        matched_count = match_result.scalar_one()

        # Update session
        session.total_transactions = total_transactions
        session.total_receipts = total_receipts
        session.matched_count = matched_count
        await self.db.flush()

    async def update_session_status(self, session_id: UUID, status: str) -> None:
        """
        Update session status.

        Args:
            session_id: UUID of the session
            status: New status (processing/completed/failed/expired)
        """
        stmt = (
            update(Session)
            .where(Session.id == session_id)
            .values(status=status)
        )
        await self.db.execute(stmt)
        await self.db.flush()
