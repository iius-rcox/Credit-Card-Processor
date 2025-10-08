"""
ProgressRepository - Handles progress tracking data persistence.

This module manages reading and writing progress data to the sessions table,
specifically the JSONB processing_progress column and cached fields.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.session import Session
from ..schemas.processing_progress import ProcessingProgress


class ProgressRepository:
    """
    Repository for managing progress tracking data in the database.

    Provides methods to read and update progress information stored
    as JSONB in the sessions table.
    """

    def __init__(self, db_session: AsyncSession):
        """
        Initialize the progress repository.

        Args:
            db_session: AsyncSession instance for database operations
        """
        self.db = db_session

    async def get_session_progress(self, session_id: UUID) -> Optional[ProcessingProgress]:
        """
        Retrieve the current progress for a session.

        Args:
            session_id: UUID of the session

        Returns:
            ProcessingProgress object if exists, None otherwise

        Example:
            progress = await repo.get_session_progress(session_id)
            if progress:
                print(f"Overall: {progress.overall_percentage}%")
                print(f"Phase: {progress.current_phase}")
        """
        result = await self.db.execute(
            select(Session.processing_progress)
            .where(Session.id == session_id)
        )
        row = result.scalar_one_or_none()

        if row and isinstance(row, dict):
            # Convert JSONB dict to ProcessingProgress
            return ProcessingProgress(**row)

        return None

    async def update_session_progress(
        self,
        session_id: UUID,
        progress: ProcessingProgress
    ) -> bool:
        """
        Update the progress for a session.

        This method updates both the JSONB progress data and the cached
        columns (current_phase, overall_percentage) for efficient filtering.

        Args:
            session_id: UUID of the session
            progress: ProcessingProgress object with updated state

        Returns:
            True if update was successful, False otherwise

        Example:
            progress = ProcessingProgress(
                overall_percentage=45,
                current_phase="processing",
                phases={...},
                last_update=datetime.utcnow(),
                status_message="Processing File 2 of 3"
            )
            success = await repo.update_session_progress(session_id, progress)
        """
        try:
            # Convert ProcessingProgress to dict for JSONB storage
            progress_dict = progress.dict()

            # Update session with progress data and cached fields
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(
                    processing_progress=progress_dict,
                    current_phase=progress.current_phase,
                    overall_percentage=float(progress.overall_percentage),
                    updated_at=datetime.utcnow()
                )
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            raise

    async def clear_session_progress(self, session_id: UUID) -> bool:
        """
        Clear the progress data for a session.

        This is typically called when processing completes successfully
        to free up storage space.

        Args:
            session_id: UUID of the session

        Returns:
            True if clear was successful, False otherwise

        Example:
            await repo.clear_session_progress(session_id)
        """
        try:
            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(
                    processing_progress=None,
                    current_phase=None,
                    overall_percentage=0.00,
                    updated_at=datetime.utcnow()
                )
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            raise

    async def get_session_summary(self, session_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get a summary of session progress without full JSONB parsing.

        Uses the cached columns for efficient retrieval.

        Args:
            session_id: UUID of the session

        Returns:
            Dictionary with summary data or None if not found

        Example:
            summary = await repo.get_session_summary(session_id)
            # Returns: {
            #     "session_id": "...",
            #     "current_phase": "processing",
            #     "overall_percentage": 45.5,
            #     "status": "processing"
            # }
        """
        result = await self.db.execute(
            select(
                Session.id,
                Session.current_phase,
                Session.overall_percentage,
                Session.status,
                Session.updated_at
            )
            .where(Session.id == session_id)
        )
        row = result.first()

        if row:
            return {
                "session_id": row.id,
                "current_phase": row.current_phase,
                "overall_percentage": float(row.overall_percentage) if row.overall_percentage else 0.0,
                "status": row.status,
                "last_update": row.updated_at
            }

        return None

    async def list_active_sessions_progress(self) -> list[Dict[str, Any]]:
        """
        List progress summaries for all active sessions.

        Returns sessions that have a current_phase set (actively processing).

        Returns:
            List of progress summaries

        Example:
            active = await repo.list_active_sessions_progress()
            for session in active:
                print(f"Session {session['session_id']}: {session['overall_percentage']}%")
        """
        result = await self.db.execute(
            select(
                Session.id,
                Session.current_phase,
                Session.overall_percentage,
                Session.status,
                Session.created_at,
                Session.updated_at
            )
            .where(Session.current_phase.isnot(None))
            .order_by(Session.updated_at.desc())
        )

        return [
            {
                "session_id": row.id,
                "current_phase": row.current_phase,
                "overall_percentage": float(row.overall_percentage) if row.overall_percentage else 0.0,
                "status": row.status,
                "created_at": row.created_at,
                "last_update": row.updated_at
            }
            for row in result
        ]

    async def update_phase_only(
        self,
        session_id: UUID,
        phase: str,
        percentage: Optional[int] = None
    ) -> bool:
        """
        Quick update of just the phase and optionally percentage.

        Useful for phase transitions without full progress object.

        Args:
            session_id: UUID of the session
            phase: New phase name
            percentage: Optional overall percentage

        Returns:
            True if update was successful, False otherwise

        Example:
            await repo.update_phase_only(session_id, "matching", 60)
        """
        try:
            values = {
                "current_phase": phase,
                "updated_at": datetime.utcnow()
            }

            if percentage is not None:
                values["overall_percentage"] = float(percentage)

            stmt = (
                update(Session)
                .where(Session.id == session_id)
                .values(**values)
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            await self.db.rollback()
            raise