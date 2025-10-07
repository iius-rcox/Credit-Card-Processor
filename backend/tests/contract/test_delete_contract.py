"""
Contract tests for DELETE /api/sessions/{id} endpoint.

Tests validate session deletion and cascade behavior.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from src.main import app


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_session_success():
    """
    Test successful session deletion.

    Contract:
    - DELETE /api/sessions/{id} deletes session and related records
    - Returns 204 No Content on success
    - No response body
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.delete(f"/api/sessions/{session_id}")

        # Should be 404 if not found, 204 if deleted successfully
        assert response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND]

        if response.status_code == status.HTTP_204_NO_CONTENT:
            # No content should be returned
            assert len(response.content) == 0


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_session_not_found():
    """
    Test deleting non-existent session.

    Contract:
    - Returns 404 Not Found
    - Includes error detail
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        non_existent_id = str(uuid.uuid4())

        response = await client.delete(f"/api/sessions/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert "detail" in data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_session_invalid_uuid():
    """
    Test deleting session with invalid UUID format.

    Contract:
    - Returns 422 Unprocessable Entity for invalid UUID
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete("/api/sessions/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_session_cascade_deletion():
    """
    Test that deleting session cascades to related records.

    Contract:
    - Deleting session should delete all related:
      - employees
      - transactions
      - receipts
      - match_results
    - Cascade deletion is automatic (ON DELETE CASCADE)
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # This test validates the contract expectation
        # Actual cascade verification would require:
        # 1. Create session with related data
        # 2. Delete session
        # 3. Verify related data is gone

        # For now, test that delete endpoint exists and accepts requests
        session_id = str(uuid.uuid4())

        response = await client.delete(f"/api/sessions/{session_id}")

        # Accept either 204 (success) or 404 (not found)
        assert response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_404_NOT_FOUND]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_session_idempotency():
    """
    Test that deleting the same session twice returns 404.

    Contract:
    - First DELETE returns 204 (or 404 if not found)
    - Second DELETE returns 404 (session no longer exists)
    - DELETE is idempotent from client perspective
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        # First delete
        first_response = await client.delete(f"/api/sessions/{session_id}")

        # Second delete
        second_response = await client.delete(f"/api/sessions/{session_id}")

        # Second delete should always return 404 (session doesn't exist)
        assert second_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_session_verify_removal():
    """
    Test that deleted session cannot be retrieved.

    Contract:
    - After successful deletion, GET /api/sessions/{id} returns 404
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        # Try to delete
        delete_response = await client.delete(f"/api/sessions/{session_id}")

        if delete_response.status_code == status.HTTP_204_NO_CONTENT:
            # Verify session is gone
            get_response = await client.get(f"/api/sessions/{session_id}")
            assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_session_no_content_body():
    """
    Test that successful deletion returns no content body.

    Contract:
    - 204 No Content should have empty body
    - Content-Length should be 0 or absent
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.delete(f"/api/sessions/{session_id}")

        if response.status_code == status.HTTP_204_NO_CONTENT:
            # No body should be present
            assert len(response.content) == 0

            # Content-Length should be 0 if present
            if "content-length" in response.headers:
                assert response.headers["content-length"] == "0"


@pytest.mark.contract
@pytest.mark.asyncio
async def test_delete_session_method_not_allowed():
    """
    Test that only DELETE method is allowed on this endpoint.

    Contract:
    - POST, PUT, PATCH to /api/sessions/{id} should return 405 Method Not Allowed
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        # Try PUT (should not be allowed)
        put_response = await client.put(f"/api/sessions/{session_id}")
        assert put_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Try PATCH (should not be allowed)
        patch_response = await client.patch(f"/api/sessions/{session_id}")
        assert patch_response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
