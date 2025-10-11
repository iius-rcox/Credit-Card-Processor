"""
Main FastAPI application.

Credit Card Reconciliation System - Backend API
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .database import close_db, init_db
from .api.routes import aliases, health, progress, reports, sessions, upload
from .api.middleware import LoggingMiddleware


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.

    Startup:
    - Initialize database (development only)

    Shutdown:
    - Close database connections
    """
    # Startup
    if settings.ENVIRONMENT == "development":
        # In development, we can auto-create tables
        # In production, use Alembic migrations
        try:
            await init_db()
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")

    yield

    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title="Credit Card Reconciliation API",
    description="""
    Internal API for reconciling credit card transactions with receipts.

    **Features:**
    - Upload PDF files (credit card statements and receipts)
    - Automatic data extraction using OCR
    - Fuzzy matching of transactions to receipts
    - Excel and CSV report generation
    - 90-day automatic data retention

    **Workflow:**
    1. Upload PDFs via POST /api/upload
    2. System extracts employee, transaction, and receipt data
    3. Matching algorithm links transactions to receipts
    4. Download reconciliation report via GET /api/sessions/{id}/report
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# Logging middleware (first, to log all requests)
app.add_middleware(LoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_PREFIX)
app.include_router(upload.router, prefix=settings.API_V1_PREFIX)
app.include_router(sessions.router, prefix=settings.API_V1_PREFIX)
app.include_router(progress.router, prefix=settings.API_V1_PREFIX)
app.include_router(reports.router, prefix=settings.API_V1_PREFIX)
app.include_router(aliases.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors.

    Args:
        request: FastAPI request
        exc: Exception that was raised

    Returns:
        JSON error response
    """
    # Log the error (in production, send to logging service)
    print(f"Unhandled exception: {type(exc).__name__}: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "error_type": type(exc).__name__
        }
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information.

    Returns:
        API metadata
    """
    return {
        "name": "Credit Card Reconciliation API",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
