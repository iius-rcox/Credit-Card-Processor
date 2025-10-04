"""
Integration test: Full upload-to-report workflow (T011).

This test verifies the complete end-to-end flow:
1. Upload 2 PDFs
2. Process them
3. Verify Excel report generated with only incomplete expenses
4. Verify CSV export generated with only complete employees

This test MUST FAIL until full implementation is complete (TDD approach).
"""

import os
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestFullWorkflow:
    """Integration test for complete upload → process → report generation flow."""

    def test_upload_process_generate_reports_workflow(self):
        """
        Test the complete workflow from upload to report download.

        Scenario:
        1. Upload test_credit_card_statement.pdf and test_expense_report.pdf
        2. Initiate processing
        3. Verify processing completes successfully
        4. Verify Excel report contains only incomplete expenses
        5. Verify CSV export contains only complete employees (100% receipted + coded)

        This is the primary acceptance test for the feature.
        """
        # Step 1: Upload PDFs
        # Using mock PDFs for now - in full implementation, use actual test fixtures
        credit_card_pdf_content = self._create_mock_credit_card_pdf()
        expense_report_pdf_content = self._create_mock_expense_report_pdf()

        upload_response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": (
                    "test_cc_statement.pdf",
                    credit_card_pdf_content,
                    "application/pdf",
                ),
                "expenseReport": (
                    "test_expense_report.pdf",
                    expense_report_pdf_content,
                    "application/pdf",
                ),
            },
        )

        assert upload_response.status_code == 201, "Upload should succeed"

        upload_data = upload_response.json()
        session_id = upload_data["session_id"]

        assert session_id is not None, "Should receive session_id"

        # Step 2: Initiate processing
        process_response = client.post(
            "/api/process",
            json={"session_id": session_id},
            headers={"Accept": "text/event-stream"},
        )

        assert process_response.status_code == 200, "Processing should start successfully"

        # Verify SSE stream contains progress updates
        stream_text = process_response.text
        assert "progress" in stream_text, "Stream should contain progress updates"
        assert "100" in stream_text, "Processing should reach 100%"
        assert "complete" in stream_text.lower(), "Should show completion status"

        # Step 3: Retrieve session data
        session_response = client.get(f"/api/session/{session_id}")
        assert session_response.status_code == 200, "Session should be retrievable"

        session_data = session_response.json()
        assert session_data["processing_status"] == "complete", "Processing should be complete"
        assert len(session_data["employees"]) > 0, "Should have parsed employees"

        # Step 4: Get reports
        reports_response = client.get(f"/api/reports/{session_id}")
        assert reports_response.status_code == 200, "Reports should be available"

        reports_data = reports_response.json()

        # Verify Excel report exists
        assert reports_data.get("excel_report") is not None, "Excel report should be generated"
        excel_report = reports_data["excel_report"]
        assert excel_report["row_count"] >= 0, "Excel should have row count"

        # Verify CSV export exists
        assert reports_data.get("csv_export") is not None, "CSV export should be generated"
        csv_export = reports_data["csv_export"]
        assert csv_export["row_count"] >= 0, "CSV should have row count"

        # Verify summary statistics
        summary = reports_data["summary"]
        assert summary["total_employees"] > 0, "Should have employees"
        assert summary["total_expenses"] > 0, "Should have expenses"

        # Step 5: Verify Excel report contains ONLY incomplete expenses
        # Excel row count should equal incomplete expenses count
        incomplete_count = (
            summary["expenses_missing_receipts"]
            + summary["expenses_missing_gl_codes"]
            + summary["expenses_missing_both"]
        )

        assert excel_report["row_count"] == incomplete_count, (
            f"Excel should have {incomplete_count} rows for incomplete expenses, "
            f"got {excel_report['row_count']}"
        )

        # Step 6: Verify CSV export includes ONLY complete employees
        # CSV should only include employees where completion_status = "complete"
        assert csv_export["included_employee_count"] == summary["complete_employees"], (
            "CSV should only include complete employees"
        )

        # Verify CSV row count matches complete expenses from complete employees
        assert csv_export["row_count"] == summary["complete_expenses"], (
            "CSV row count should match complete expenses"
        )

    def test_workflow_with_no_complete_employees(self):
        """
        Test workflow when all employees have at least one missing item.

        Expected: Excel report has rows, CSV export is empty or null
        """
        # Mock PDFs where all employees have incomplete expenses
        credit_card_pdf = self._create_mock_credit_card_pdf()
        expense_report_pdf = self._create_mock_incomplete_expense_report()

        # Upload
        upload_response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("cc.pdf", credit_card_pdf, "application/pdf"),
                "expenseReport": ("er.pdf", expense_report_pdf, "application/pdf"),
            },
        )

        session_id = upload_response.json()["session_id"]

        # Process
        client.post("/api/process", json={"session_id": session_id})

        # Get reports
        reports_response = client.get(f"/api/reports/{session_id}")
        reports_data = reports_response.json()

        summary = reports_data["summary"]

        # All employees should be incomplete
        assert summary["complete_employees"] == 0, "No employees should be complete"
        assert summary["incomplete_employees"] > 0, "All employees should be incomplete"

        # Excel should have rows
        assert reports_data["excel_report"]["row_count"] > 0, "Excel should have incomplete items"

        # CSV should be empty or have 0 rows
        csv_export = reports_data.get("csv_export")
        if csv_export:
            assert csv_export["row_count"] == 0, "CSV should be empty (no complete employees)"
            assert csv_export["included_employee_count"] == 0

    def test_workflow_with_all_complete_employees(self):
        """
        Test workflow when all employees have all expenses complete.

        Expected: Excel report is empty, CSV export contains all expenses
        """
        # Mock PDFs where all employees are 100% complete
        credit_card_pdf = self._create_mock_credit_card_pdf()
        expense_report_pdf = self._create_mock_complete_expense_report()

        # Upload
        upload_response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("cc.pdf", credit_card_pdf, "application/pdf"),
                "expenseReport": ("er.pdf", expense_report_pdf, "application/pdf"),
            },
        )

        session_id = upload_response.json()["session_id"]

        # Process
        client.post("/api/process", json={"session_id": session_id})

        # Get reports
        reports_response = client.get(f"/api/reports/{session_id}")
        reports_data = reports_response.json()

        summary = reports_data["summary"]

        # All employees should be complete
        assert summary["complete_employees"] > 0, "Should have complete employees"
        assert summary["incomplete_employees"] == 0, "No employees should be incomplete"

        # Excel should be empty (no incomplete items)
        assert reports_data["excel_report"]["row_count"] == 0, (
            "Excel should be empty (no incomplete expenses)"
        )

        # CSV should contain all expenses
        csv_export = reports_data["csv_export"]
        assert csv_export["row_count"] == summary["total_expenses"], (
            "CSV should contain all expenses (all complete)"
        )
        assert csv_export["included_employee_count"] == summary["total_employees"]

    # Helper methods to create mock PDF content

    def _create_mock_credit_card_pdf(self):
        """Create mock credit card statement PDF content."""
        import io

        return io.BytesIO(b"%PDF-1.4\nMock Credit Card Statement\n")

    def _create_mock_expense_report_pdf(self):
        """Create mock expense report PDF with mix of receipts."""
        import io

        return io.BytesIO(b"%PDF-1.4\nMock Expense Report with some receipts\n")

    def _create_mock_incomplete_expense_report(self):
        """Create mock expense report where no employee is complete."""
        import io

        return io.BytesIO(b"%PDF-1.4\nIncomplete expense report\n")

    def _create_mock_complete_expense_report(self):
        """Create mock expense report where all expenses are complete."""
        import io

        return io.BytesIO(b"%PDF-1.4\nComplete expense report with all receipts and GL codes\n")
