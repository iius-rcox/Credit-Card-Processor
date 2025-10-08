"""
Progress API endpoints for better status updates.

This module provides endpoints for retrieving progress information
and streaming real-time updates via Server-Sent Events (SSE).
"""

import asyncio
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse

from ...database import get_db
from ...repositories.progress_repository import ProgressRepository
from ...schemas.processing_progress import ProcessingProgress


router = APIRouter(prefix="/sessions", tags=["progress"])


@router.get("/{session_id}/progress")
async def get_progress(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get the current progress for a session.

    This endpoint returns a snapshot of the current processing progress
    including overall percentage, current phase, and detailed phase information.

    Args:
        session_id: UUID of the session to retrieve progress for

    Returns:
        Progress information dictionary

    Raises:
        HTTPException: If session not found

    Example Response:
        {
            "session_id": "123e4567-e89b-12d3-a456-426614174000",
            "overall_percentage": 45,
            "current_phase": "processing",
            "phases": {
                "upload": {
                    "status": "completed",
                    "percentage": 100
                },
                "processing": {
                    "status": "in_progress",
                    "percentage": 35,
                    "current_file": {
                        "name": "statement.pdf",
                        "current_page": 5,
                        "total_pages": 12
                    }
                }
            },
            "status_message": "Processing File 2 of 3: Page 5/12",
            "last_update": "2025-10-08T14:25:42Z"
        }
    """
    repo = ProgressRepository(db)

    # First try to get full progress data
    progress = await repo.get_session_progress(session_id)

    if progress:
        # Return full progress data
        return {
            "session_id": session_id,
            "overall_percentage": progress.overall_percentage,
            "current_phase": progress.current_phase,
            "phases": progress.phases,
            "status_message": progress.status_message,
            "last_update": progress.last_update,
            "error": progress.error
        }

    # If no progress data, try to get session summary
    summary = await repo.get_session_summary(session_id)

    if summary:
        # Session exists but no detailed progress yet
        return {
            "session_id": session_id,
            "overall_percentage": summary["overall_percentage"],
            "current_phase": summary["current_phase"] or "pending",
            "phases": {},
            "status_message": f"Status: {summary['status']}",
            "last_update": summary["last_update"]
        }

    # Session not found
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("/{session_id}/progress/stream")
async def stream_progress(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    heartbeat: int = Query(default=30, description="Heartbeat interval in seconds")
) -> EventSourceResponse:
    """
    Stream progress updates via Server-Sent Events (SSE).

    This endpoint establishes an SSE connection and streams progress updates
    as they occur. It includes heartbeat messages to keep the connection alive.

    Args:
        session_id: UUID of the session to stream progress for
        heartbeat: Interval in seconds between heartbeat messages (default: 30)

    Returns:
        EventSourceResponse streaming progress updates

    Raises:
        HTTPException: If session not found

    SSE Event Format:
        event: progress
        data: {
            "overall_percentage": 45,
            "current_phase": "processing",
            "status_message": "Processing File 2 of 3: Page 5/12"
        }

        event: heartbeat
        data: {"timestamp": "2025-10-08T14:25:42Z"}

        event: complete
        data: {"message": "Processing completed successfully"}

        event: error
        data: {"error": "Processing failed: Invalid PDF format"}
    """
    # Verify session exists
    repo = ProgressRepository(db)
    summary = await repo.get_session_summary(session_id)

    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")

    async def event_generator():
        """Generate SSE events for progress updates."""
        last_update = None
        heartbeat_counter = 0

        try:
            while True:
                # Check for new progress data
                progress = await repo.get_session_progress(session_id)

                if progress:
                    # Check if there's a new update
                    if progress.last_update != last_update:
                        last_update = progress.last_update

                        # Prepare progress event data
                        event_data = {
                            "overall_percentage": progress.overall_percentage,
                            "current_phase": progress.current_phase,
                            "status_message": progress.status_message,
                            "phases": {
                                name: {
                                    "status": phase.status,
                                    "percentage": phase.percentage
                                }
                                for name, phase in progress.phases.items()
                            }
                        }

                        # Check for completion or error
                        if progress.error:
                            yield {
                                "event": "error",
                                "data": {
                                    "error": progress.error.message,
                                    "context": progress.error.context
                                }
                            }
                            break
                        elif progress.current_phase == "completed":
                            yield {
                                "event": "complete",
                                "data": {"message": "Processing completed successfully"}
                            }
                            break
                        else:
                            yield {
                                "event": "progress",
                                "data": event_data
                            }

                # Send heartbeat every N iterations
                heartbeat_counter += 1
                if heartbeat_counter >= heartbeat:
                    yield {
                        "event": "heartbeat",
                        "data": {"timestamp": datetime.utcnow().isoformat() + "Z"}
                    }
                    heartbeat_counter = 0

                # Wait before checking again (polling interval)
                await asyncio.sleep(2)  # Check every 2 seconds

        except asyncio.CancelledError:
            # Client disconnected
            pass
        except Exception as e:
            yield {
                "event": "error",
                "data": {"error": f"Stream error: {str(e)}"}
            }

    return EventSourceResponse(event_generator())


@router.post("/{session_id}/progress/test")
async def test_progress_update(
    session_id: UUID,
    phase: str = "processing",
    percentage: int = 50,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Test endpoint to manually update progress (for development/testing).

    This endpoint allows manual progress updates for testing the progress
    tracking system without running actual processing.

    Args:
        session_id: UUID of the session
        phase: Phase name to set
        percentage: Overall percentage to set

    Returns:
        Success message

    Note:
        This endpoint should be disabled in production.
    """
    from datetime import datetime
    from ...schemas.phase_progress import PhaseProgress

    repo = ProgressRepository(db)

    # Create test progress data
    test_progress = ProcessingProgress(
        overall_percentage=percentage,
        current_phase=phase,
        phases={
            "upload": PhaseProgress(
                status="completed" if phase != "upload" else "in_progress",
                percentage=100 if phase != "upload" else percentage
            ),
            "processing": PhaseProgress(
                status="in_progress" if phase == "processing" else "pending",
                percentage=percentage if phase == "processing" else 0
            ),
            "matching": PhaseProgress(
                status="pending",
                percentage=0
            ),
            "report_generation": PhaseProgress(
                status="pending",
                percentage=0
            )
        },
        last_update=datetime.utcnow(),
        status_message=f"Test update: {phase} phase at {percentage}%"
    )

    success = await repo.update_session_progress(session_id, test_progress)

    if success:
        return {"message": "Progress updated successfully"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")