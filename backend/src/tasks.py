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

    session_id = UUID(session_id_str)

    try:
        # Run the async function in a new event loop
        # Each Celery worker task runs in its own process with its own event loop
        asyncio.run(process_session_background(session_id))

        return {
            "status": "success",
            "session_id": session_id_str
        }
    except Exception as e:
        logger.error(f"Task failed for session {session_id}: {e}", exc_info=True)
        return {
            "status": "error",
            "session_id": session_id_str,
            "error": str(e)
        }
