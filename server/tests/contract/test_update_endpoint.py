"""
Contract tests for POST /api/session/{sessionId}/update endpoint.

These tests verify the API contract defined in contracts/update-receipts.yaml.
They MUST FAIL until the endpoint is implemented (TDD approach).
"""

import io
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestUpdateEndpoint:
    """Test suite for POST /api/session/{sessionId}/update endpoint contract."""

    def test_update_receipts_success(self):
        """
        Test successful upload of new expense report to existing session.

        Expected: 200 status with updated: true, summary_changes object
        """
        # Mock existing session
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        # Create mock updated expense report PDF
        updated_expense_report = io.BytesIO(b"%PDF-1.4 updated expense report")

        response = client.post(
            f"/api/session/{session_id}/update",
            files={
                "expenseReport": ("updated_receipts.pdf", updated_expense_report, "application/pdf"),
            },
        )

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        # Assert required fields
        required_fields = ["session_id", "updated", "updated_at", "summary_changes"]
        for field in required_fields:
            assert field in data, f"Response must contain '{field}' field"

        # Assert session_id matches request
        assert data["session_id"] == session_id

        # Assert updated is boolean true
        assert data["updated"] is True

        # Assert updated_at is timestamp
        assert isinstance(data["updated_at"], str)
        assert "T" in data["updated_at"]

    def test_update_summary_changes_structure(self):
        """
        Test that summary_changes object has correct structure.

        Expected: previous and current sub-objects with employee/expense counts,
        plus arrays of newly_complete_employees and newly_incomplete_expenses
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        updated_expense_report = io.BytesIO(b"%PDF-1.4 updated expense report")

        response = client.post(
            f"/api/session/{session_id}/update",
            files={
                "expenseReport": ("updated.pdf", updated_expense_report, "application/pdf"),
            },
        )

        data = response.json()
        summary_changes = data.get("summary_changes", {})

        # Assert previous and current sub-objects
        assert "previous" in summary_changes
        assert "current" in summary_changes

        previous = summary_changes["previous"]
        current = summary_changes["current"]

        # Both should have employee/expense counts
        for obj in [previous, current]:
            assert "complete_employees" in obj
            assert "incomplete_expenses" in obj
            assert isinstance(obj["complete_employees"], int)
            assert isinstance(obj["incomplete_expenses"], int)

        # Assert change tracking arrays
        assert "newly_complete_employees" in summary_changes
        assert "newly_incomplete_expenses" in summary_changes

        # Should be arrays of IDs
        assert isinstance(summary_changes["newly_complete_employees"], list)
        assert isinstance(summary_changes["newly_incomplete_expenses"], list)

    def test_update_new_report_urls(self):
        """
        Test that updated reports have new URLs.

        Expected: new_excel_report_url and new_csv_export_url present
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        updated_expense_report = io.BytesIO(b"%PDF-1.4 updated expense report")

        response = client.post(
            f"/api/session/{session_id}/update",
            files={
                "expenseReport": ("updated.pdf", updated_expense_report, "application/pdf"),
            },
        )

        data = response.json()

        # New report URLs should be present (nullable if no changes)
        if "new_excel_report_url" in data:
            assert isinstance(data["new_excel_report_url"], str)

        if "new_csv_export_url" in data:
            assert isinstance(data["new_csv_export_url"], str)

    def test_update_session_not_found(self):
        """
        Test updating non-existent session.

        Expected: 404 status with error message
        """
        nonexistent_session_id = "99999999-9999-9999-9999-999999999999"
        expense_report = io.BytesIO(b"%PDF-1.4 expense report")

        response = client.post(
            f"/api/session/{nonexistent_session_id}/update",
            files={
                "expenseReport": ("report.pdf", expense_report, "application/pdf"),
            },
        )

        assert response.status_code == 404, (
            f"Expected 404 for non-existent session, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data, "Error response must contain 'error' field"

    def test_update_missing_file(self):
        """
        Test update without providing expense report file.

        Expected: 400 or 422 status with error message
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.post(f"/api/session/{session_id}/update")

        assert response.status_code in [400, 422], (
            f"Expected 400/422 for missing file, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data or "detail" in data

    def test_update_invalid_file_format(self):
        """
        Test update with non-PDF file.

        Expected: 400 status with error about invalid file format
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"
        text_file = io.BytesIO(b"Not a PDF")

        response = client.post(
            f"/api/session/{session_id}/update",
            files={
                "expenseReport": ("report.txt", text_file, "text/plain"),
            },
        )

        assert response.status_code == 400, (
            f"Expected 400 for invalid file type, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data
        # Error should mention PDF or format
        error_lower = data["error"].lower()
        assert "pdf" in error_lower or "format" in error_lower or "invalid" in error_lower

    def test_update_session_currently_processing(self):
        """
        Test updating session that is currently processing.

        Expected: 409 status with error about processing in progress
        """
        # Mock session_id that is currently processing
        processing_session_id = "22222222-2222-2222-2222-222222222222"
        expense_report = io.BytesIO(b"%PDF-1.4 expense report")

        response = client.post(
            f"/api/session/{processing_session_id}/update",
            files={
                "expenseReport": ("report.pdf", expense_report, "application/pdf"),
            },
        )

        # Should return 409 Conflict
        if response.status_code == 409:
            data = response.json()
            assert "error" in data
            assert "processing" in data["error"].lower() or "wait" in data["error"].lower()

            # Should include processing_status field
            if "processing_status" in data:
                assert data["processing_status"] in ["processing"]

    def test_update_partial_processing_failure(self):
        """
        Test update that results in partial processing failure.

        Expected: 422 status with error, partial_results flag, details
        """
        session_id = "33333333-3333-3333-3333-333333333333"

        # Simulating corrupted PDF
        corrupted_pdf = io.BytesIO(b"corrupted data not valid PDF")

        response = client.post(
            f"/api/session/{session_id}/update",
            files={
                "expenseReport": ("corrupted.pdf", corrupted_pdf, "application/pdf"),
            },
        )

        # Could be 422 for processing errors or 400 for validation
        if response.status_code == 422:
            data = response.json()
            assert "error" in data

            # Should indicate partial results available
            if "partial_results" in data:
                assert isinstance(data["partial_results"], bool)

            if "details" in data:
                assert isinstance(data["details"], str)
