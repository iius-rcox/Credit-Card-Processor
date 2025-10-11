"""
Pytest configuration and fixtures for all tests.

Provides shared fixtures for contract, integration, and unit tests.
"""

import asyncio
import pytest
from typing import AsyncGenerator, Generator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from httpx import AsyncClient

from src.main import app
from src.database import get_db
from src.models.session import Base
from src.config import settings


# Test database URL
# Using PostgreSQL for tests to match production and support JSONB types
TEST_DATABASE_URL = "postgresql+asyncpg://ccprocessor:password@localhost:5432/credit_card_db_test"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for the test session.

    Yields:
        Event loop for async tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_engine():
    """
    Create a test database engine.

    Yields:
        Async SQLAlchemy engine for testing
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def test_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Args:
        test_engine: Test database engine fixture

    Yields:
        Async database session for tests
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def test_client(test_session) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test HTTP client with database override.

    Args:
        test_session: Test database session fixture

    Yields:
        Async HTTP client for API testing
    """

    async def override_get_db():
        yield test_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_content() -> bytes:
    """
    Create sample PDF content for testing.

    Returns:
        Mock PDF file content
    """
    return b"%PDF-1.4\n%mock PDF content\n%%EOF"


@pytest.fixture
def sample_session_data() -> dict:
    """
    Create sample session data for testing.

    Returns:
        Dictionary with session attributes
    """
    return {
        "status": "processing",
        "upload_count": 2,
        "total_transactions": 0,
        "total_receipts": 0,
        "matched_count": 0
    }


@pytest.fixture
def sample_employee_data() -> dict:
    """
    Create sample employee data for testing.

    Returns:
        Dictionary with employee attributes
    """
    return {
        "employee_number": "EMP001",
        "name": "John Doe",
        "department": "Engineering",
        "cost_center": "CC-123"
    }


@pytest.fixture
def sample_transaction_data() -> dict:
    """
    Create sample transaction data for testing.

    Returns:
        Dictionary with transaction attributes
    """
    return {
        "transaction_date": "2025-01-15",
        "post_date": "2025-01-16",
        "amount": 123.45,
        "currency": "USD",
        "merchant_name": "Test Merchant",
        "merchant_category": "Dining",
        "description": "Business lunch",
        "card_last_four": "1234",
        "reference_number": "REF001"
    }


@pytest.fixture
def sample_receipt_data() -> dict:
    """
    Create sample receipt data for testing.

    Returns:
        Dictionary with receipt attributes
    """
    return {
        "receipt_date": "2025-01-15",
        "amount": 123.45,
        "currency": "USD",
        "vendor_name": "Test Restaurant",
        "file_name": "receipt.pdf",
        "file_path": "/tmp/receipt.pdf",
        "file_size": 1024,
        "mime_type": "application/pdf",
        "ocr_confidence": 0.95,
        "extracted_data": {
            "items": ["Lunch", "Coffee"],
            "total": 123.45
        },
        "processing_status": "completed"
    }


@pytest.fixture
def sample_match_result_data() -> dict:
    """
    Create sample match result data for testing.

    Returns:
        Dictionary with match result attributes
    """
    return {
        "confidence_score": 0.95,
        "match_status": "matched",
        "match_reason": "Exact amount and date match",
        "amount_difference": 0.0,
        "date_difference_days": 0,
        "merchant_similarity": 0.95,
        "matching_factors": {
            "amount_match": True,
            "date_match": True,
            "merchant_match": True
        }
    }


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest markers.

    Args:
        config: Pytest configuration object
    """
    config.addinivalue_line(
        "markers", "contract: Contract tests for API endpoints"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for end-to-end scenarios"
    )
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to run"
    )
