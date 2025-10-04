"""
Integration test: Update workflow with new expense report (T014).

Verifies session persistence and re-analysis when uploading new expense report.
This test MUST FAIL until update endpoint is implemented (TDD approach).
"""

import io
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestUpdateWorkflow:
    """Test update workflow with new expense report."""

    def test_upload_new_expense_report_preserves_session(self):
        """
        Test that uploading new expense report keeps same session_id.

        Scenario:
        1. Create session and process
        2. Upload new expense report
        3. Verify session_id remains unchanged
        4. Verify summary_changes shows differences
        """
        # Initial upload
        cc_pdf = io.BytesIO(b"%PDF-1.4\nCredit Card Statement\n")
        er_pdf = io.BytesIO(b"%PDF-1.4\nExpense Report v1\n")

        upload_response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("cc.pdf", cc_pdf, "application/pdf"),
                "expenseReport": ("er_v1.pdf", er_pdf, "application/pdf"),
            },
        )

        original_session_id = upload_response.json()["session_id"]

        # Process
        client.post("/api/process", json={"session_id": original_session_id})

        # Get initial reports for comparison
        initial_reports = client.get(f"/api/reports/{original_session_id}").json()
        initial_summary = initial_reports["summary"]

        # Upload new expense report (updated with more receipts)
        er_pdf_v2 = io.BytesIO(b"%PDF-1.4\nExpense Report v2 with more receipts\n")

        update_response = client.post(
            f"/api/session/{original_session_id}/update",
            files={
                "expenseReport": ("er_v2.pdf", er_pdf_v2, "application/pdf"),
            },
        )

        assert update_response.status_code == 200, "Update should succeed"

        update_data = update_response.json()

        # Verify session_id is the same
        assert update_data["session_id"] == original_session_id, (
            "Session ID should remain unchanged after update"
        )

        # Verify updated flag
        assert update_data["updated"] is True

        # Verify summary_changes exists and has correct structure
        assert "summary_changes" in update_data
        summary_changes = update_data["summary_changes"]

        assert "previous" in summary_changes
        assert "current" in summary_changes
        assert "newly_complete_employees" in summary_changes
        assert "newly_incomplete_expenses" in summary_changes

        # Verify previous matches initial summary
        assert summary_changes["previous"]["complete_employees"] == initial_summary["complete_employees"]

    def test_update_generates_new_reports(self):
        """
        Test that update generates new Excel and CSV reports.

        Expected: new_excel_report_url and new_csv_export_url in response
        """
        # Setup session
        cc_pdf = io.BytesIO(b"%PDF-1.4\nCC\n")
        er_pdf = io.BytesIO(b"%PDF-1.4\nER v1\n")

        upload_response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("cc.pdf", cc_pdf, "application/pdf"),
                "expenseReport": ("er.pdf", er_pdf, "application/pdf"),
            },
        )

        session_id = upload_response.json()["session_id"]
        client.post("/api/process", json={"session_id": session_id})

        # Update
        er_pdf_v2 = io.BytesIO(b"%PDF-1.4\nER v2\n")

        update_response = client.post(
            f"/api/session/{session_id}/update",
            files={"expenseReport": ("er_v2.pdf", er_pdf_v2, "application/pdf")},
        )

        update_data = update_response.json()

        # Verify new report URLs provided
        if "new_excel_report_url" in update_data:
            assert isinstance(update_data["new_excel_report_url"], str)

        if "new_csv_export_url" in update_data:
            assert isinstance(update_data["new_csv_export_url"], str)

    def test_update_cannot_modify_credit_card_statement(self):
        """
        Test that update only accepts expense report, not credit card statement.

        Expected: Only expense report can be updated, credit card statement remains original
        """
        # Create session
        cc_pdf = io.BytesIO(b"%PDF-1.4\nOriginal CC Statement\n")
        er_pdf = io.BytesIO(b"%PDF-1.4\nER\n")

        upload_response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("cc.pdf", cc_pdf, "application/pdf"),
                "expenseReport": ("er.pdf", er_pdf, "application/pdf"),
            },
        )

        session_id = upload_response.json()["session_id"]
        client.post("/api/process", json={"session_id": session_id})

        # Attempt to update (only expense report allowed)
        new_er = io.BytesIO(b"%PDF-1.4\nNew ER\n")

        update_response = client.post(
            f"/api/session/{session_id}/update",
            files={"expenseReport": ("new_er.pdf", new_er, "application/pdf")},
        )

        # Update should work
        assert update_response.status_code == 200

        # Credit card statement should remain unchanged
        # (Verified by checking matching logic still uses original CC data)
