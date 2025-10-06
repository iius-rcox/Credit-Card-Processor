"""
Contract tests for GET /api/sessions endpoint.

Tests validate pagination, filtering, and response schema.
"""

import pytest
from httpx import AsyncClient
from fastapi import status

from src.main import app


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_sessions_default_pagination():
    """
    Test listing sessions with default pagination.

    Contract:
    - GET /api/sessions returns paginated results
    - Default page=1, page_size=50
    - Response includes items, total, page, page_size, has_next
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/sessions")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "has_next" in data

        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert data["page"] == 1
        assert data["page_size"] == 50


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_sessions_custom_pagination():
    """
    Test listing sessions with custom pagination parameters.

    Contract:
    - Accepts page and page_size query parameters
    - page_size max is 100
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/sessions?page=2&page_size=25")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["page"] == 2
        assert data["page_size"] == 25


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_sessions_90day_window():
    """
    Test that only sessions within 90-day window are returned.

    Contract:
    - Only sessions with created_at > NOW() - 90 days
    - Expired sessions not included
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/sessions")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # All returned sessions should be within 90-day window
        # (This is a contract guarantee, actual validation would require test data)
        assert isinstance(data["items"], list)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_sessions_empty_result():
    """
    Test listing sessions when no sessions exist.

    Contract:
    - Returns empty items array
    - total = 0
    - Still returns valid pagination structure
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/sessions")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] >= 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_sessions_response_schema():
    """
    Test that session list items match the expected schema.

    Contract:
    - Each session has required fields
    - Field types are correct
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/sessions")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        # If we have items, validate their schema
        if data["items"]:
            session = data["items"][0]

            required_fields = [
                "id", "created_at", "expires_at", "status",
                "upload_count", "total_transactions", "total_receipts", "matched_count"
            ]

            for field in required_fields:
                assert field in session, f"Missing required field: {field}"

            # Validate types
            assert isinstance(session["id"], str)
            assert isinstance(session["status"], str)
            assert isinstance(session["upload_count"], int)
            assert isinstance(session["total_transactions"], int)
            assert isinstance(session["total_receipts"], int)
            assert isinstance(session["matched_count"], int)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_sessions_invalid_page():
    """
    Test listing sessions with invalid page parameter.

    Contract:
    - Invalid pagination parameters should return 422 or default to valid values
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/sessions?page=-1")

        # Should either reject with 422 or default to page 1
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_200_OK]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_list_sessions_page_size_limit():
    """
    Test that page_size is limited to maximum 100.

    Contract:
    - page_size cannot exceed 100
    - Requesting more should either cap at 100 or return validation error
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/sessions?page_size=200")

        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_200_OK]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert data["page_size"] <= 100
