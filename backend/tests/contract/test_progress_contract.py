"""
Contract tests for Progress Tracking API

These tests verify the API contract defined in specs/006-better-status-updates/contracts/progress-api.yaml

All tests are expected to FAIL until implementation is complete (TDD approach).
"""

import pytest
from httpx import AsyncClient
from uuid import uuid4, UUID
from datetime import datetime


@pytest.mark.asyncio
async def test_get_progress_returns_200_for_valid_session(client: AsyncClient, test_session_id: UUID):
    """
    Contract: GET /sessions/{id}/progress returns 200 with progress data

    Given: A valid session ID exists
    When: GET /sessions/{id}/progress is called
    Then: Response is 200 with ProgressResponse schema
    """
    response = await client.get(f"/sessions/{test_session_id}/progress")

    assert response.status_code == 200

    data = response.json()

    # Verify required fields
    assert "session_id" in data
    assert "current_phase" in data
    assert "overall_percentage" in data
    assert "last_update" in data
    assert "status_message" in data

    # Verify types
    assert isinstance(data["session_id"], str)
    assert UUID(data["session_id"])  # Valid UUID format
    assert isinstance(data["current_phase"], str)
    assert isinstance(data["overall_percentage"], int)
    assert isinstance(data["status_message"], str)

    # Verify constraints
    assert 0 <= data["overall_percentage"] <= 100
    assert data["current_phase"] in [
        "upload", "processing", "matching",
        "report_generation", "completed", "failed"
    ]


@pytest.mark.asyncio
async def test_get_progress_returns_404_for_nonexistent_session(client: AsyncClient):
    """
    Contract: GET /sessions/{id}/progress returns 404 for nonexistent session

    Given: A session ID that does not exist
    When: GET /sessions/{id}/progress is called
    Then: Response is 404 with error message
    """
    nonexistent_id = uuid4()
    response = await client.get(f"/sessions/{nonexistent_id}/progress")

    assert response.status_code == 404

    data = response.json()
    assert "error" in data


@pytest.mark.asyncio
async def test_get_progress_includes_phase_details_when_processing(
    client: AsyncClient,
    test_session_processing: UUID
):
    """
    Contract: phase_details contains PhaseProgress objects during processing

    Given: A session is actively processing
    When: GET /sessions/{id}/progress is called
    Then: phase_details contains status, percentage, and phase-specific fields
    """
    response = await client.get(f"/sessions/{test_session_processing}/progress")

    assert response.status_code == 200

    data = response.json()
    phase_details = data.get("phase_details")

    # Should have phase details when processing
    if data["current_phase"] in ["processing", "matching", "upload"]:
        assert phase_details is not None
        assert isinstance(phase_details, dict)

        # Check at least one phase exists
        assert len(phase_details) > 0

        # Verify PhaseProgress schema
        for phase_name, phase_data in phase_details.items():
            assert "status" in phase_data
            assert "percentage" in phase_data

            assert phase_data["status"] in ["pending", "in_progress", "completed", "failed"]
            assert 0 <= phase_data["percentage"] <= 100

            # If status is in_progress, started_at should exist
            if phase_data["status"] == "in_progress":
                assert "started_at" in phase_data


@pytest.mark.asyncio
async def test_get_progress_includes_file_progress_during_processing(
    client: AsyncClient,
    test_session_with_files: UUID
):
    """
    Contract: current_file contains FileProgress details during file processing

    Given: A session is processing files
    When: GET /sessions/{id}/progress is called
    Then: phase_details.processing.current_file contains file progress
    """
    response = await client.get(f"/sessions/{test_session_with_files}/progress")

    assert response.status_code == 200

    data = response.json()

    if data["current_phase"] == "processing":
        phase_details = data.get("phase_details", {})
        processing = phase_details.get("processing", {})
        current_file = processing.get("current_file")

        if current_file:
            # Verify FileProgress schema
            assert "name" in current_file
            assert "total_pages" in current_file
            assert "current_page" in current_file
            assert "regex_matches_found" in current_file

            # Verify types and constraints
            assert isinstance(current_file["name"], str)
            assert current_file["total_pages"] >= 1
            assert 1 <= current_file["current_page"] <= current_file["total_pages"]
            assert current_file["regex_matches_found"] >= 0


@pytest.mark.asyncio
async def test_get_progress_includes_error_context_on_failure(
    client: AsyncClient,
    test_session_failed: UUID
):
    """
    Contract: error field contains ErrorContext when processing fails

    Given: A session has failed during processing
    When: GET /sessions/{id}/progress is called
    Then: error field contains type, message, context, timestamp
    """
    response = await client.get(f"/sessions/{test_session_failed}/progress")

    assert response.status_code == 200

    data = response.json()

    if data["current_phase"] == "failed":
        error = data.get("error")

        assert error is not None

        # Verify ErrorContext schema
        assert "type" in error
        assert "message" in error
        assert "context" in error
        assert "timestamp" in error

        # Verify context contains phase
        assert "phase" in error["context"]

        # May optionally contain file and page
        # (depending on where error occurred)


@pytest.mark.asyncio
async def test_get_progress_null_phase_details_when_completed(
    client: AsyncClient,
    test_session_completed: UUID
):
    """
    Contract: phase_details is null when processing is complete

    Given: A session has completed processing
    When: GET /sessions/{id}/progress is called
    Then: phase_details is null, overall_percentage is 100
    """
    response = await client.get(f"/sessions/{test_session_completed}/progress")

    assert response.status_code == 200

    data = response.json()

    if data["current_phase"] == "completed":
        assert data["overall_percentage"] == 100
        assert data.get("phase_details") is None


@pytest.mark.asyncio
async def test_get_progress_status_message_is_descriptive(
    client: AsyncClient,
    test_session_id: UUID
):
    """
    Contract: status_message provides human-readable description

    Given: A session with progress
    When: GET /sessions/{id}/progress is called
    Then: status_message is descriptive (not generic "Processing...")
    """
    response = await client.get(f"/sessions/{test_session_id}/progress")

    assert response.status_code == 200

    data = response.json()
    status_message = data["status_message"]

    # Should not be empty or generic
    assert len(status_message) > 0
    assert status_message.lower() != "processing"
    assert status_message.lower() != "processing..."


@pytest.mark.asyncio
async def test_get_progress_last_update_is_recent(
    client: AsyncClient,
    test_session_processing: UUID
):
    """
    Contract: last_update timestamp is in ISO 8601 format and recent

    Given: A session is actively processing
    When: GET /sessions/{id}/progress is called
    Then: last_update is valid ISO 8601 and within last 5 minutes
    """
    response = await client.get(f"/sessions/{test_session_processing}/progress")

    assert response.status_code == 200

    data = response.json()
    last_update_str = data["last_update"]

    # Verify ISO 8601 format
    last_update = datetime.fromisoformat(last_update_str.replace('Z', '+00:00'))

    # Should be recent (within last 5 minutes) for active processing
    now = datetime.now(last_update.tzinfo)
    elapsed_seconds = (now - last_update).total_seconds()

    assert elapsed_seconds < 300  # 5 minutes


@pytest.mark.asyncio
async def test_get_progress_aggregate_percentage_calculation(
    client: AsyncClient,
    test_session_multi_file: UUID
):
    """
    Contract: overall_percentage correctly aggregates multi-file progress

    Given: A session processing multiple files
    When: GET /sessions/{id}/progress is called
    Then: overall_percentage reflects weighted progress across files
    """
    response = await client.get(f"/sessions/{test_session_multi_file}/progress")

    assert response.status_code == 200

    data = response.json()

    if data["current_phase"] == "processing":
        phase_details = data.get("phase_details", {})
        processing = phase_details.get("processing", {})

        total_files = processing.get("total_files")
        current_file_index = processing.get("current_file_index")
        current_file = processing.get("current_file")

        if total_files and current_file:
            # Calculate expected aggregate
            files_completed = current_file_index - 1
            current_file_pct = (
                current_file["current_page"] / current_file["total_pages"]
            )
            expected_aggregate_approx = (
                (files_completed + current_file_pct) / total_files * 100
            )

            # Allow 5% tolerance (due to phase weighting)
            actual_aggregate = data["overall_percentage"]
            assert abs(actual_aggregate - expected_aggregate_approx) <= 5


# ============================================================================
# Test Fixtures (to be implemented in conftest.py)
# ============================================================================

"""
Required fixtures in backend/tests/conftest.py:

@pytest.fixture
async def test_session_id(test_db) -> UUID:
    # Create a test session
    pass

@pytest.fixture
async def test_session_processing(test_db) -> UUID:
    # Create a session with in_progress status
    pass

@pytest.fixture
async def test_session_with_files(test_db) -> UUID:
    # Create a session processing multiple files
    pass

@pytest.fixture
async def test_session_failed(test_db) -> UUID:
    # Create a session that failed
    pass

@pytest.fixture
async def test_session_completed(test_db) -> UUID:
    # Create a completed session
    pass

@pytest.fixture
async def test_session_multi_file(test_db) -> UUID:
    # Create a session with multi-file progress
    pass
"""
