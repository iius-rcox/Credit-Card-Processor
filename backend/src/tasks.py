"""
Celery tasks for background processing.

This module defines Celery tasks that run outside the request/response cycle.
"""

import asyncio
import logging
from pathlib import Path
from uuid import UUID

from .celery_app import celery_app
from .services.upload_service import process_session_background

logger = logging.getLogger(__name__)

# Log task registration
logger.info("=" * 80)
logger.info("CELERY TASKS MODULE LOADED")
logger.info(f"  Module: {__name__}")
logger.info(f"  Celery app: {celery_app}")
logger.info(f"  Task names: tasks.process_session, tasks.match_session")
logger.info("=" * 80)


@celery_app.task(name="tasks.process_session")
def process_session_task(session_id_str: str) -> dict:
    """
    Celery task to process uploaded files for a session.

    This task runs asynchronously in a Celery worker process.

    Args:
        session_id_str: String representation of session UUID

    Returns:
        dict with status and session_id
    """
    import asyncio
    from uuid import UUID

    logger.info("=" * 80)
    logger.info(f"✓ CELERY TASK STARTED: process_session_task")
    logger.info(f"  Task ID: {process_session_task.request.id}")
    logger.info(f"  Session ID (str): {session_id_str}")
    logger.info("=" * 80)

    session_id = UUID(session_id_str)
    logger.info(f"  Session ID (UUID): {session_id}")

    try:
        logger.info(f"→ Running async background processing for session {session_id}...")
        # Run the async function in a new event loop
        # Each Celery worker task runs in its own process with its own event loop
        asyncio.run(process_session_background(session_id))

        logger.info(f"✓ Task completed successfully for session {session_id}")
        return {
            "status": "success",
            "session_id": session_id_str
        }
    except Exception as e:
        logger.error(f"✗ Task failed for session {session_id}: {e}", exc_info=True)
        logger.error(f"  Error type: {type(e).__name__}")
        logger.error(f"  Error message: {str(e)}")
        return {
            "status": "error",
            "session_id": session_id_str,
            "error": str(e)
        }


@celery_app.task(name="tasks.match_session")
def match_session_task(session_id_str: str) -> dict:
    """
    Background task to match transactions with receipts.

    Args:
        session_id: Session UUID string

    Returns:
        dict with status and counts

    Note:
        Transactions are already extracted and in database.
        This task only performs matching logic.
    """
    logger.info("=" * 80)
    logger.info(f"✓ CELERY TASK STARTED: match_session_task")
    logger.info(f"  Task ID: {match_session_task.request.id}")
    logger.info(f"  Session ID (str): {session_id_str}")
    logger.info("=" * 80)

    session_id = UUID(session_id_str)
    logger.info(f"  Session ID (UUID): {session_id}")

    try:
        logger.info(f"→ Running async matching for session {session_id}...")
        result = asyncio.run(match_session_background(session_id))

        logger.info(f"✓ Matching task completed successfully for session {session_id}")
        return result
    except Exception as e:
        logger.error(f"✗ Matching task failed for session {session_id}: {e}", exc_info=True)
        logger.error(f"  Error type: {type(e).__name__}")
        logger.error(f"  Error message: {str(e)}")
        return {
            "status": "error",
            "session_id": session_id_str,
            "error": str(e)
        }


async def match_session_background(session_id: UUID) -> dict:
    """
    Background function to match transactions with receipts.

    Args:
        session_id: Session UUID

    Returns:
        dict with status, session_id, and match counts

    Note:
        Creates its own DB session since it runs outside the request context.
        Only handles matching - extraction is already complete.
    """
    from urllib.parse import quote_plus
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from .config import settings
    from .repositories.session_repository import SessionRepository
    from .repositories.transaction_repository import TransactionRepository
    from .repositories.receipt_repository import ReceiptRepository
    from .repositories.match_result_repository import MatchResultRepository
    from .services.matching_service import MatchingService

    # Create a new engine for this event loop (Celery worker context)
    database_url = (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{quote_plus(settings.POSTGRES_PASSWORD)}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )

    worker_engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=2,
        max_overflow=3,
        pool_pre_ping=True,
        connect_args={"server_settings": {"jit": "off"}}
    )

    WorkerSessionLocal = async_sessionmaker(
        worker_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )

    try:
        async with WorkerSessionLocal() as db:
            try:
                logger.info(f"Starting matching for session {session_id}")

                # Create repositories and services
                session_repo = SessionRepository(db)
                transaction_repo = TransactionRepository(db)
                receipt_repo = ReceiptRepository(db)
                match_result_repo = MatchResultRepository(db)

                matching_service = MatchingService(
                    session_repo, transaction_repo, receipt_repo, match_result_repo
                )

                # TODO: Implement actual matching logic
                # For now, just mark session as completed
                # In a real implementation, you would:
                # 1. Load transactions and receipts from database
                # 2. Run matching algorithm
                # 3. Save match results
                # 4. Update session counts

                logger.info(f"Matching logic placeholder - marking session {session_id} as completed")

                # Mark session as completed
                await session_repo.update_session_status(session_id, "completed")

                # Commit the database session
                await db.commit()

                logger.info(f"Matching completed successfully for session {session_id}")

                return {
                    "status": "success",
                    "session_id": str(session_id),
                    "matches_created": 0  # Placeholder
                }

            except Exception as e:
                logger.error(
                    f"Matching failed for session {session_id}: {type(e).__name__}: {str(e)}",
                    exc_info=True
                )

                # Rollback on error
                await db.rollback()

                # Mark session as failed
                try:
                    session_repo = SessionRepository(db)
                    await session_repo.update_session_status(session_id, "failed")
                    await db.commit()
                except Exception as cleanup_error:
                    logger.error(
                        f"Failed to update session status after error: {cleanup_error}",
                        exc_info=True
                    )

                raise

    finally:
        # Dispose of the worker engine to close all connections
        try:
            await worker_engine.dispose()
            logger.info(f"Disposed worker engine for session {session_id}")
        except Exception as engine_error:
            logger.error(f"Failed to dispose worker engine: {engine_error}", exc_info=True)
