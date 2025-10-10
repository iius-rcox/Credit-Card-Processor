"""
Error handling middleware for progress API endpoints.

This module provides middleware to catch and properly format errors
that occur during progress tracking operations.
"""

import logging
import traceback
from datetime import datetime
from typing import Callable
from uuid import UUID

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import DatabaseError, IntegrityError

from ...schemas.phase_progress import ErrorContext

logger = logging.getLogger(__name__)


class ProgressErrorMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling errors in progress-related endpoints.

    This middleware catches exceptions from progress endpoints and
    formats them consistently with ErrorContext schema.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process the request and handle any errors that occur.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            Response object with error details if an error occurred
        """
        try:
            # Only apply to progress endpoints
            if not self._is_progress_endpoint(request.url.path):
                return await call_next(request)

            # Process the request
            response = await call_next(request)
            return response

        except HTTPException as e:
            # Let FastAPI handle HTTP exceptions normally
            raise

        except DatabaseError as e:
            # Database-related errors
            error_context = self._create_error_context(
                error_type="DatabaseError",
                message="Database operation failed while updating progress",
                request=request,
                exception=e
            )
            logger.error(f"Database error in progress endpoint: {e}")
            return self._create_error_response(error_context, status_code=503)

        except IntegrityError as e:
            # Data integrity errors
            error_context = self._create_error_context(
                error_type="IntegrityError",
                message="Data integrity violation in progress update",
                request=request,
                exception=e
            )
            logger.error(f"Integrity error in progress endpoint: {e}")
            return self._create_error_response(error_context, status_code=400)

        except ValueError as e:
            # Validation errors
            error_context = self._create_error_context(
                error_type="ValidationError",
                message=str(e),
                request=request,
                exception=e
            )
            logger.warning(f"Validation error in progress endpoint: {e}")
            return self._create_error_response(error_context, status_code=422)

        except Exception as e:
            # Unexpected errors
            error_context = self._create_error_context(
                error_type="UnexpectedError",
                message="An unexpected error occurred during progress operation",
                request=request,
                exception=e
            )
            logger.error(f"Unexpected error in progress endpoint: {e}", exc_info=True)
            return self._create_error_response(error_context, status_code=500)

    def _is_progress_endpoint(self, path: str) -> bool:
        """
        Check if the request path is a progress-related endpoint.

        Args:
            path: Request path

        Returns:
            True if this is a progress endpoint
        """
        progress_paths = [
            "/progress",
            "/progress/stream",
            "/progress/test"
        ]
        return any(progress_path in path for progress_path in progress_paths)

    def _create_error_context(
        self,
        error_type: str,
        message: str,
        request: Request,
        exception: Exception
    ) -> ErrorContext:
        """
        Create an ErrorContext object from an exception.

        Args:
            error_type: Type of error
            message: Error message
            request: The request that caused the error
            exception: The exception that was raised

        Returns:
            ErrorContext object
        """
        # Extract session ID from path if present
        session_id = None
        path_parts = request.url.path.split("/")
        if "sessions" in path_parts:
            try:
                idx = path_parts.index("sessions")
                if idx + 1 < len(path_parts):
                    session_id = path_parts[idx + 1]
            except (ValueError, IndexError):
                pass

        # Build context dictionary
        context = {
            "endpoint": request.url.path,
            "method": request.method,
            "phase": "progress_tracking"
        }

        if session_id:
            context["sessionId"] = session_id

        # Create ErrorContext
        return ErrorContext(
            type=error_type,
            message=message,
            context=context,
            timestamp=datetime.utcnow(),
            traceback=traceback.format_exc() if logger.level <= logging.DEBUG else None
        )

    def _create_error_response(
        self,
        error_context: ErrorContext,
        status_code: int = 500
    ) -> JSONResponse:
        """
        Create a JSON response from an ErrorContext.

        Args:
            error_context: The error context
            status_code: HTTP status code

        Returns:
            JSONResponse with error details
        """
        return JSONResponse(
            status_code=status_code,
            content={
                "error": error_context.dict(exclude_none=True)
            }
        )


class ProgressValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating progress-related requests.

    This middleware performs validation checks on progress requests
    before they reach the endpoint handlers.
    """

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Validate progress requests before processing.

        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler

        Returns:
            Response object
        """
        try:
            # Only apply to progress endpoints
            if not self._is_progress_endpoint(request.url.path):
                return await call_next(request)

            # Validate session ID format if present
            session_id = self._extract_session_id(request.url.path)
            if session_id:
                try:
                    UUID(session_id)
                except ValueError:
                    raise ValueError(f"Invalid session ID format: {session_id}")

            # Process the request
            response = await call_next(request)

            # Add cache headers for progress endpoints
            if request.method == "GET" and "/stream" not in request.url.path:
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"

            return response

        except ValueError as e:
            return JSONResponse(
                status_code=400,
                content={"error": {"message": str(e), "type": "ValidationError"}}
            )

    def _is_progress_endpoint(self, path: str) -> bool:
        """Check if this is a progress endpoint."""
        return "/progress" in path

    def _extract_session_id(self, path: str) -> str | None:
        """Extract session ID from path."""
        path_parts = path.split("/")
        if "sessions" in path_parts:
            try:
                idx = path_parts.index("sessions")
                if idx + 1 < len(path_parts):
                    return path_parts[idx + 1]
            except (ValueError, IndexError):
                pass
        return None


def setup_progress_error_handling(app):
    """
    Add progress error handling middleware to the FastAPI app.

    Args:
        app: FastAPI application instance
    """
    app.add_middleware(ProgressValidationMiddleware)
    app.add_middleware(ProgressErrorMiddleware)

    logger.info("Progress error handling middleware configured")