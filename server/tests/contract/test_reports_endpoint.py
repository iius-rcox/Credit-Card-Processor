"""
Contract tests for GET /api/reports/{sessionId} endpoint.

These tests verify the API contract defined in contracts/get-reports.yaml.
They MUST FAIL until the endpoint is implemented (TDD approach).
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestReportsEndpoint:
    """Test suite for GET /api/reports/{sessionId} endpoint contract."""

    def test_get_reports_success(self):
        """
        Test retrieving reports for a completed session.

        Expected: 200 status with excel_report, csv_export, and summary objects
        """
        # Mock session_id that has completed processing
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/reports/{session_id}")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()

        # Assert required top-level fields
        assert "session_id" in data
        assert "summary" in data

        # session_id should match request
        assert data["session_id"] == session_id

        # summary is required
        assert isinstance(data["summary"], dict)

    def test_get_reports_excel_report_structure(self):
        """
        Test that excel_report object has correct structure.

        Expected fields: url, file_size, row_count, generated_at
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/reports/{session_id}")

        data = response.json()

        # excel_report is nullable but if present, verify structure
        if data.get("excel_report") is not None:
            excel_report = data["excel_report"]

            required_fields = ["url", "file_size", "row_count", "generated_at"]
            for field in required_fields:
                assert field in excel_report, f"excel_report must have '{field}' field"

            # Verify types
            assert isinstance(excel_report["url"], str)
            assert isinstance(excel_report["file_size"], int)
            assert isinstance(excel_report["row_count"], int)
            assert isinstance(excel_report["generated_at"], str)

            # Verify row_count >= 0
            assert excel_report["row_count"] >= 0

    def test_get_reports_csv_export_structure(self):
        """
        Test that csv_export object has correct structure.

        Expected fields: url, file_size, row_count, included_employee_count, generated_at
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/reports/{session_id}")

        data = response.json()

        # csv_export is nullable but if present, verify structure
        if data.get("csv_export") is not None:
            csv_export = data["csv_export"]

            required_fields = [
                "url",
                "file_size",
                "row_count",
                "included_employee_count",
                "generated_at",
            ]
            for field in required_fields:
                assert field in csv_export, f"csv_export must have '{field}' field"

            # Verify types
            assert isinstance(csv_export["url"], str)
            assert isinstance(csv_export["file_size"], int)
            assert isinstance(csv_export["row_count"], int)
            assert isinstance(csv_export["included_employee_count"], int)
            assert isinstance(csv_export["generated_at"], str)

            # Verify counts >= 0
            assert csv_export["row_count"] >= 0
            assert csv_export["included_employee_count"] >= 0

    def test_get_reports_summary_structure(self):
        """
        Test that summary object has correct structure.

        Expected fields: total_employees, complete_employees, incomplete_employees,
        total_expenses, complete_expenses, expenses_missing_receipts,
        expenses_missing_gl_codes, expenses_missing_both
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/reports/{session_id}")

        data = response.json()
        summary = data["summary"]

        required_summary_fields = [
            "total_employees",
            "complete_employees",
            "incomplete_employees",
            "total_expenses",
            "complete_expenses",
            "expenses_missing_receipts",
            "expenses_missing_gl_codes",
            "expenses_missing_both",
        ]

        for field in required_summary_fields:
            assert field in summary, f"summary must have '{field}' field"
            assert isinstance(summary[field], int), f"{field} must be an integer"
            assert summary[field] >= 0, f"{field} must be >= 0"

        # Verify logical relationships
        total_employees = summary["total_employees"]
        complete_employees = summary["complete_employees"]
        incomplete_employees = summary["incomplete_employees"]

        assert complete_employees + incomplete_employees == total_employees, (
            "complete + incomplete should equal total employees"
        )

        total_expenses = summary["total_expenses"]
        complete_expenses = summary["complete_expenses"]
        missing_receipts = summary["expenses_missing_receipts"]
        missing_gl = summary["expenses_missing_gl_codes"]
        missing_both = summary["expenses_missing_both"]

        # All expenses should be accounted for
        assert complete_expenses + missing_receipts + missing_gl + missing_both == total_expenses, (
            "Sum of expense categories should equal total_expenses"
        )

    def test_get_reports_not_found(self):
        """
        Test retrieving reports for non-existent session.

        Expected: 404 status with error message
        """
        nonexistent_session_id = "99999999-9999-9999-9999-999999999999"

        response = client.get(f"/api/reports/{nonexistent_session_id}")

        assert response.status_code == 404, (
            f"Expected 404 for non-existent session, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data, "Error response must contain 'error' field"

    def test_get_reports_processing_not_complete(self):
        """
        Test retrieving reports when processing is not complete.

        Expected: 409 status with error about incomplete processing
        """
        # Mock session_id that is still processing
        processing_session_id = "11111111-1111-1111-1111-111111111111"

        response = client.get(f"/api/reports/{processing_session_id}")

        # Could be 409 (Conflict) or 200 with null reports
        if response.status_code == 409:
            data = response.json()
            assert "error" in data
            assert "processing" in data["error"].lower() or "not available" in data["error"].lower()
        elif response.status_code == 200:
            data = response.json()
            # If 200, excel_report and csv_export should be null
            assert data.get("excel_report") is None or data.get("csv_export") is None

    def test_get_reports_url_format(self):
        """
        Test that report URLs are properly formatted.

        Expected: URLs should start with / or http and point to download location
        """
        session_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/reports/{session_id}")

        if response.status_code == 200:
            data = response.json()

            if data.get("excel_report"):
                excel_url = data["excel_report"]["url"]
                assert isinstance(excel_url, str)
                assert len(excel_url) > 0
                # URL should be absolute or relative path
                assert excel_url.startswith("/") or excel_url.startswith("http")

            if data.get("csv_export"):
                csv_url = data["csv_export"]["url"]
                assert isinstance(csv_url, str)
                assert len(csv_url) > 0
                assert csv_url.startswith("/") or csv_url.startswith("http")
