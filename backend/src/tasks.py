"""
Celery tasks for background processing.

This module defines Celery tasks that run outside the request/response cycle.
"""

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
logger.info(f"  Task name: tasks.process_session")
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
