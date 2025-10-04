"""
Contract tests for POST /api/process endpoint.

These tests verify the API contract defined in contracts/process-pdfs.yaml.
Tests Server-Sent Events (SSE) streaming for progress updates.
They MUST FAIL until the endpoint is implemented (TDD approach).
"""

import json
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestProcessEndpoint:
    """Test suite for POST /api/process endpoint contract (SSE streaming)."""

    def test_process_with_valid_session_id(self):
        """
        Test processing with valid session_id.

        Expected: 200 status with SSE stream containing progress events
        Each event should have: progress (int 0-100), step (string), status (string)
        """
        # Use a mock session_id (UUID format)
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.post(
            "/api/process",
            json={"session_id": session_id},
            headers={"Accept": "text/event-stream"},
        )

        # SSE responses return 200 even if streaming
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        # SSE content type check
        content_type = response.headers.get("content-type", "")
        assert "text/event-stream" in content_type or "application/octet-stream" in content_type, (
            f"Expected SSE content type, got {content_type}"
        )

        # Parse SSE stream
        # SSE format: "data: {json}\n\n"
        events = self._parse_sse_stream(response.text)

        # Assert at least some progress events received
        assert len(events) > 0, "Should receive at least one progress event"

        # Verify each event structure
        for event in events:
            assert "progress" in event, "Each event must have 'progress' field"
            assert "step" in event, "Each event must have 'step' field"
            assert "status" in event, "Each event must have 'status' field"

            # Validate field types
            assert isinstance(event["progress"], int), "progress must be integer"
            assert 0 <= event["progress"] <= 100, "progress must be 0-100"
            assert isinstance(event["step"], str), "step must be string"
            assert isinstance(event["status"], str), "status must be string"

            # Validate status values
            assert event["status"] in ["processing", "complete", "error"], (
                f"status must be processing/complete/error, got {event['status']}"
            )

        # Verify final event shows completion
        final_event = events[-1]
        assert final_event["progress"] == 100, "Final event should have progress=100"
        assert final_event["status"] == "complete", "Final event should have status='complete'"

    def test_process_with_missing_session_id(self):
        """
        Test processing without session_id in request body.

        Expected: 400 status with error message
        """
        response = client.post(
            "/api/process",
            json={},  # Missing session_id
        )

        assert response.status_code == 400 or response.status_code == 422, (
            f"Expected 400/422 for missing session_id, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data or "detail" in data, (
            "Error response must contain 'error' or 'detail' field"
        )

    def test_process_with_invalid_session_id_format(self):
        """
        Test processing with invalid session_id (not UUID format).

        Expected: 400 status with error message
        """
        response = client.post(
            "/api/process",
            json={"session_id": "not-a-uuid"},
        )

        assert response.status_code == 400 or response.status_code == 422, (
            f"Expected 400/422 for invalid UUID, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data or "detail" in data

    def test_process_with_nonexistent_session_id(self):
        """
        Test processing with valid UUID but session doesn't exist.

        Expected: 404 status with error message
        """
        # Valid UUID format but doesn't exist
        nonexistent_session_id = "99999999-9999-9999-9999-999999999999"

        response = client.post(
            "/api/process",
            json={"session_id": nonexistent_session_id},
        )

        assert response.status_code == 404, (
            f"Expected 404 for non-existent session, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data, "Error response must contain 'error' field"
        assert "not found" in data["error"].lower() or "does not exist" in data["error"].lower()

    def test_process_progress_increments(self):
        """
        Test that progress values increment logically.

        Expected: Progress should go from 0 → 100 in ascending order
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.post(
            "/api/process",
            json={"session_id": session_id},
            headers={"Accept": "text/event-stream"},
        )

        events = self._parse_sse_stream(response.text)

        # Extract progress values
        progress_values = [event["progress"] for event in events]

        # Verify progress is in ascending order (non-decreasing)
        for i in range(1, len(progress_values)):
            assert progress_values[i] >= progress_values[i - 1], (
                f"Progress should not decrease: {progress_values}"
            )

        # Verify starts at or near 0 and ends at 100
        assert progress_values[0] <= 10, "First progress should be at or near 0"
        assert progress_values[-1] == 100, "Final progress should be 100"

    def test_process_expected_steps(self):
        """
        Test that processing includes expected step descriptions.

        Expected steps:
        - Parsing Credit Card Statement
        - Extracting employee data
        - Parsing Expense Report
        - Matching expenses to receipts
        - Generating Excel report
        - Generating CSV export
        - Complete
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.post(
            "/api/process",
            json={"session_id": session_id},
            headers={"Accept": "text/event-stream"},
        )

        events = self._parse_sse_stream(response.text)
        steps = [event["step"] for event in events]

        # Join all steps into one string for easier checking
        all_steps = " ".join(steps).lower()

        # Verify key processing steps are mentioned
        expected_keywords = [
            "parsing",
            "credit card",
            "employee",
            "expense report",
            "matching",
            "excel",
            "csv",
            "complete",
        ]

        for keyword in expected_keywords:
            assert keyword in all_steps, (
                f"Expected to see '{keyword}' in processing steps, got: {steps}"
            )

    def _parse_sse_stream(self, stream_text: str) -> list:
        """
        Parse Server-Sent Events stream into list of event objects.

        SSE format:
        data: {"progress": 10, "step": "...", "status": "processing"}

        data: {"progress": 25, "step": "...", "status": "processing"}

        Args:
            stream_text: Raw SSE stream text

        Returns:
            List of parsed event dictionaries
        """
        events = []
        lines = stream_text.strip().split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("data:"):
                # Extract JSON after "data: "
                json_str = line[5:].strip()
                try:
                    event = json.loads(json_str)
                    events.append(event)
                except json.JSONDecodeError:
                    # Skip malformed events
                    pass

        return events
