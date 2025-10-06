"""
Request/Response logging middleware.

Logs incoming requests and outgoing responses with timing information.
"""

import json
import logging
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Features:
    - Adds unique request ID to each request
    - Logs request method, path, query params, headers (excluding sensitive)
    - Logs response status code and timing
    - Uses structured JSON logging for production
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.sensitive_headers = {
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
        }

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and log details.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response from downstream
        """
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Record start time
        start_time = time.time()

        # Log incoming request
        self._log_request(request, request_id)

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log outgoing response
        self._log_response(request, response, request_id, duration_ms)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response

    def _log_request(self, request: Request, request_id: str) -> None:
        """
        Log incoming request details.

        Args:
            request: FastAPI request
            request_id: Unique request identifier
        """
        # Filter sensitive headers
        safe_headers = {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in self.sensitive_headers
        }

        log_data = {
            "event": "request",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": safe_headers,
            "client": {
                "host": request.client.host if request.client else None,
                "port": request.client.port if request.client else None,
            },
        }

        logger.info(json.dumps(log_data))

    def _log_response(
        self,
        request: Request,
        response: Response,
        request_id: str,
        duration_ms: float,
    ) -> None:
        """
        Log outgoing response details.

        Args:
            request: FastAPI request
            response: FastAPI response
            request_id: Unique request identifier
            duration_ms: Request duration in milliseconds
        """
        log_data = {
            "event": "response",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        # Log level based on status code
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
