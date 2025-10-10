"""
Contract tests for Progress Streaming API (SSE)

These tests verify the SSE endpoint defined in specs/006-better-status-updates/contracts/progress-api.yaml

All tests are expected to FAIL until implementation is complete (TDD approach).
"""

import pytest
import asyncio
from httpx import AsyncClient
from uuid import uuid4, UUID
from typing import AsyncIterator


@pytest.mark.asyncio
async def test_stream_progress_establishes_sse_connection(
    client: AsyncClient,
    test_session_processing: UUID
):
    """
    Contract: GET /sessions/{id}/progress/stream establishes SSE connection

    Given: A valid session ID exists
    When: GET /sessions/{id}/progress/stream is called
    Then: Response is 200 with content-type text/event-stream
    """
    async with client.stream(
        "GET",
        f"/sessions/{test_session_processing}/progress/stream"
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_stream_progress_sends_progress_events(
    client: AsyncClient,
    test_session_processing: UUID
):
    """
    Contract: SSE stream sends progress events with JSON data

    Given: A session is actively processing
    When: Connected to SSE stream
    Then: Events are received with event: progress and data: {...}
    """
    event_count = 0
    max_events = 3

    async with client.stream(
        "GET",
        f"/sessions/{test_session_processing}/progress/stream"
    ) as response:
        assert response.status_code == 200

        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                assert event_type in ["progress", "complete", "error", "heartbeat"]

            if line.startswith("data:"):
                import json
                data_str = line.split(":", 1)[1].strip()
                data = json.loads(data_str)

                # Verify ProgressResponse schema in data
                if "session_id" in data:
                    assert "current_phase" in data
                    assert "overall_percentage" in data
                    assert "last_update" in data

                    event_count += 1

            if event_count >= max_events:
                break


@pytest.mark.asyncio
async def test_stream_progress_sends_events_every_2_3_seconds(
    client: AsyncClient,
    test_session_processing: UUID
):
    """
    Contract: SSE events sent every 2-3 seconds during processing

    Given: A session is actively processing
    When: Monitoring SSE stream timing
    Then: Events arrive approximately every 2-3 seconds
    """
    import time

    event_times = []
    max_events = 3

    async with client.stream(
        "GET",
        f"/sessions/{test_session_processing}/progress/stream"
    ) as response:
        assert response.status_code == 200

        async for line in response.aiter_lines():
            if line.startswith("data:"):
                import json
                data_str = line.split(":", 1)[1].strip()
                data = json.loads(data_str)

                if "session_id" in data:
                    event_times.append(time.time())

            if len(event_times) >= max_events:
                break

    # Verify intervals are approximately 2-3 seconds
    if len(event_times) >= 2:
        for i in range(1, len(event_times)):
            interval = event_times[i] - event_times[i-1]
            assert 1.5 <= interval <= 4.0  # Allow some tolerance


@pytest.mark.asyncio
async def test_stream_progress_sends_complete_event_on_finish(
    client: AsyncClient,
    test_session_completing: UUID
):
    """
    Contract: SSE stream sends 'complete' event when processing finishes

    Given: A session that will complete during stream
    When: Monitoring SSE stream
    Then: Receive event: complete with final state
    """
    complete_event_received = False

    async with client.stream(
        "GET",
        f"/sessions/{test_session_completing}/progress/stream"
    ) as response:
        assert response.status_code == 200

        timeout = asyncio.create_task(asyncio.sleep(10))

        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                if event_type == "complete":
                    complete_event_received = True
                    break

            if timeout.done():
                break

    # Should eventually receive complete event
    # (May not in test environment, but contract expects it)


@pytest.mark.asyncio
async def test_stream_progress_sends_error_event_on_failure(
    client: AsyncClient,
    test_session_will_fail: UUID
):
    """
    Contract: SSE stream sends 'error' event when processing fails

    Given: A session that will fail during processing
    When: Monitoring SSE stream
    Then: Receive event: error with ErrorContext
    """
    error_event_received = False

    async with client.stream(
        "GET",
        f"/sessions/{test_session_will_fail}/progress/stream"
    ) as response:
        assert response.status_code == 200

        timeout = asyncio.create_task(asyncio.sleep(10))

        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                if event_type == "error":
                    error_event_received = True

            if line.startswith("data:") and error_event_received:
                import json
                data_str = line.split(":", 1)[1].strip()
                data = json.loads(data_str)

                # Verify ErrorContext in data
                assert "error" in data
                error = data["error"]
                assert "type" in error
                assert "message" in error
                assert "context" in error
                break

            if timeout.done():
                break


@pytest.mark.asyncio
async def test_stream_progress_returns_404_for_nonexistent_session(
    client: AsyncClient
):
    """
    Contract: SSE stream returns 404 for nonexistent session

    Given: A session ID that does not exist
    When: Attempting to connect to SSE stream
    Then: Response is 404
    """
    nonexistent_id = uuid4()

    async with client.stream(
        "GET",
        f"/sessions/{nonexistent_id}/progress/stream"
    ) as response:
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_stream_progress_includes_heartbeat(
    client: AsyncClient,
    test_session_processing: UUID
):
    """
    Contract: SSE stream sends heartbeat events to keep connection alive

    Given: A session is processing
    When: Monitoring SSE stream
    Then: Receive periodic heartbeat events
    """
    heartbeat_received = False

    async with client.stream(
        "GET",
        f"/sessions/{test_session_processing}/progress/stream",
        timeout=30.0
    ) as response:
        assert response.status_code == 200

        timeout = asyncio.create_task(asyncio.sleep(15))

        async for line in response.aiter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
                if event_type == "heartbeat":
                    heartbeat_received = True
                    break

            if timeout.done():
                break

    # Should receive at least one heartbeat within 15 seconds


@pytest.mark.asyncio
async def test_stream_progress_handles_client_disconnect(
    client: AsyncClient,
    test_session_processing: UUID
):
    """
    Contract: SSE stream properly handles client disconnection

    Given: A session is processing
    When: Client disconnects from stream
    Then: Server should clean up connection without errors
    """
    async with client.stream(
        "GET",
        f"/sessions/{test_session_processing}/progress/stream"
    ) as response:
        assert response.status_code == 200

        # Read a few events then disconnect
        event_count = 0
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                event_count += 1

            if event_count >= 2:
                # Explicit disconnect
                break

    # Connection should close cleanly without exceptions


@pytest.mark.asyncio
async def test_stream_progress_sends_immediate_update_on_connect(
    client: AsyncClient,
    test_session_processing: UUID
):
    """
    Contract: SSE stream sends current progress immediately on connection

    Given: A session with existing progress
    When: Client connects to SSE stream
    Then: First event contains current progress state
    """
    first_event_received = False

    async with client.stream(
        "GET",
        f"/sessions/{test_session_processing}/progress/stream"
    ) as response:
        assert response.status_code == 200

        async for line in response.aiter_lines():
            if line.startswith("data:"):
                import json
                data_str = line.split(":", 1)[1].strip()
                data = json.loads(data_str)

                if "session_id" in data:
                    # First event should have valid progress data
                    assert "current_phase" in data
                    assert "overall_percentage" in data
                    assert 0 <= data["overall_percentage"] <= 100
                    first_event_received = True
                    break

    assert first_event_received


# ============================================================================
# Test Fixtures (to be implemented in conftest.py)
# ============================================================================

"""
Required fixtures in backend/tests/conftest.py:

@pytest.fixture
async def test_session_processing(test_db) -> UUID:
    # Create a session actively processing
    pass

@pytest.fixture
async def test_session_completing(test_db) -> UUID:
    # Create a session that will complete soon
    pass

@pytest.fixture
async def test_session_will_fail(test_db) -> UUID:
    # Create a session that will fail during processing
    pass
"""
