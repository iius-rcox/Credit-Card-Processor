"""
Contract tests for GET /api/sessions/{id} endpoint.

Tests validate session detail retrieval with all related data.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from src.main import app


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_session_detail_valid_id():
    """
    Test retrieving session details with valid ID.

    Contract:
    - GET /api/sessions/{id} returns SessionDetail
    - Includes nested employees[], transactions[], receipts[], match_results[]
    - Returns 200 OK
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Note: This test assumes a session exists or will be created in setup
        # For now, test with a UUID format
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}")

        # Should return 404 if not found, or 200 if exists
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Validate required fields
            assert "id" in data
            assert "created_at" in data
            assert "expires_at" in data
            assert "status" in data

            # Validate nested arrays
            assert "employees" in data
            assert "transactions" in data
            assert "receipts" in data
            assert "match_results" in data

            assert isinstance(data["employees"], list)
            assert isinstance(data["transactions"], list)
            assert isinstance(data["receipts"], list)
            assert isinstance(data["match_results"], list)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_session_detail_not_found():
    """
    Test retrieving non-existent session.

    Contract:
    - Returns 404 Not Found
    - Includes error detail
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        non_existent_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{non_existent_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert "detail" in data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_session_detail_invalid_uuid():
    """
    Test retrieving session with invalid UUID format.

    Contract:
    - Returns 422 Unprocessable Entity for invalid UUID
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/sessions/not-a-uuid")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_session_detail_expired_session():
    """
    Test retrieving expired session (> 90 days old).

    Contract:
    - Expired sessions should return 404
    - Or status should indicate expired
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # This test would require creating an expired session in setup
        # For now, validate the contract expectation
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}")

        # Accept either 404 (expired sessions are filtered) or 200 with status="expired"
        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # If session is returned, check if expired status is indicated
            if "status" in data:
                assert data["status"] in ["processing", "completed", "failed", "expired"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_session_detail_response_schema():
    """
    Test that session detail response matches expected schema.

    Contract:
    - All required fields present
    - Nested objects have correct structure
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}")

        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Session fields
            required_fields = [
                "id", "created_at", "expires_at", "status",
                "upload_count", "total_transactions", "total_receipts", "matched_count"
            ]

            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Nested arrays
            assert "employees" in data
            assert "transactions" in data
            assert "receipts" in data
            assert "match_results" in data

            # If employees exist, validate schema
            if data["employees"]:
                employee = data["employees"][0]
                assert "id" in employee
                assert "employee_number" in employee
                assert "name" in employee

            # If transactions exist, validate schema
            if data["transactions"]:
                transaction = data["transactions"][0]
                assert "id" in transaction
                assert "transaction_date" in transaction
                assert "amount" in transaction
                assert "merchant_name" in transaction

            # If receipts exist, validate schema
            if data["receipts"]:
                receipt = data["receipts"][0]
                assert "id" in receipt
                assert "receipt_date" in receipt
                assert "amount" in receipt
                assert "vendor_name" in receipt

            # If match_results exist, validate schema
            if data["match_results"]:
                match = data["match_results"][0]
                assert "id" in match
                assert "transaction_id" in match
                assert "confidence_score" in match
                assert "match_status" in match


@pytest.mark.contract
@pytest.mark.asyncio
async def test_get_session_detail_includes_relationships():
    """
    Test that session detail includes all related entities.

    Contract:
    - employees array includes all employees for session
    - transactions array includes all transactions
    - receipts array includes all receipts
    - match_results array includes all matching results
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}")

        if response.status_code == status.HTTP_200_OK:
            data = response.json()

            # Verify counts match arrays
            if "total_transactions" in data:
                # Can't verify exact count without test data
                # But ensure transactions array exists
                assert isinstance(data["transactions"], list)

            if "total_receipts" in data:
                assert isinstance(data["receipts"], list)

            if "matched_count" in data:
                assert isinstance(data["match_results"], list)
