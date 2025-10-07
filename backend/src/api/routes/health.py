"""
Health check API endpoint.

GET /health - Check application health status.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db


router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="""
    Check application health status.

    **Checks:**
    - Database connectivity
    - Timestamp for monitoring

    **Response:**
    - 200 OK: Application is healthy
    - 503 Service Unavailable: Database connection failed
    """
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint.

    Args:
        db: Database session

    Returns:
        Health status dictionary

    Raises:
        HTTPException 503: If health check fails
    """
    try:
        # Test database connection
        result = await db.execute(text("SELECT 1"))
        db_connected = result.scalar_one() == 1

        if not db_connected:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": datetime.utcnow().isoformat()
            }, status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, status.HTTP_503_SERVICE_UNAVAILABLE
