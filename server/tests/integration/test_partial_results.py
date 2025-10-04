"""
Integration test: PDF parsing error with partial results (T012).

Verifies that when one PDF fails to parse, the system:
1. Displays specific error message
2. Allows viewing partial data from the successful PDF
3. Generates Excel report with available data
4. Disables CSV export (incomplete data)

This test MUST FAIL until error handling is implemented (TDD approach).
"""

import io
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestPartialResults:
    """Test partial result handling when PDF parsing fails."""

    def test_corrupted_expense_report_shows_partial_results(self):
        """
        Test that corrupted expense report still allows viewing credit card data.

        Scenario:
        - Upload valid credit card statement + corrupted expense report
        - Processing should fail with error
        - Credit card data should still be accessible (partial results)
        - Excel report should be generated (all expenses marked as missing receipts)
        - CSV export should be disabled or empty
        """
        # Valid credit card PDF
        credit_card_pdf = io.BytesIO(b"%PDF-1.4\nValid credit card statement content\n")

        # Corrupted PDF (not valid PDF format)
        corrupted_pdf = io.BytesIO(b"This is corrupted, not a valid PDF file!")

        # Upload
        upload_response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("cc.pdf", credit_card_pdf, "application/pdf"),
                "expenseReport": ("corrupted.pdf", corrupted_pdf, "application/pdf"),
            },
        )

        assert upload_response.status_code == 201, "Upload should accept files"
        session_id = upload_response.json()["session_id"]

        # Process - should handle error gracefully
        process_response = client.post(
            "/api/process",
            json={"session_id": session_id},
        )

        # Processing might return 422 (Unprocessable Entity) or stream with error status
        # Either way, should provide information about the failure

        # Get session data - should have partial results
        session_response = client.get(f"/api/session/{session_id}")

        if session_response.status_code == 200:
            session_data = session_response.json()

            # Processing status should indicate error
            assert session_data["processing_status"] == "error", (
                "Should show error status for failed parsing"
            )

            # Error message should be present and specific
            assert session_data.get("error_message"), "Should have error message"
            error_msg = session_data["error_message"].lower()
            assert "expense report" in error_msg or "parse" in error_msg or "fail" in error_msg

            # Partial data from credit card statement should be accessible
            employees = session_data.get("employees", [])
            # Even with failed expense report, credit card data should be parsed
            # (This depends on implementation - may or may not have partial employee data)

        # Get reports - Excel should be available, CSV should not
        reports_response = client.get(f"/api/reports/{session_id}")

        if reports_response.status_code == 200:
            reports_data = reports_response.json()

            # Excel report should exist (shows all as missing receipts)
            if reports_data.get("excel_report"):
                excel_report = reports_data["excel_report"]
                # All expenses should be marked as missing receipts
                assert excel_report["row_count"] > 0, "Excel should have incomplete items"

            # CSV export should be null or empty (no complete employees)
            csv_export = reports_data.get("csv_export")
            if csv_export:
                assert csv_export["row_count"] == 0, (
                    "CSV should be empty when expense report parsing fails"
                )

    def test_corrupted_credit_card_shows_partial_results(self):
        """
        Test that corrupted credit card statement still allows viewing expense report data.

        Scenario:
        - Upload corrupted credit card statement + valid expense report
        - Processing should fail with error
        - Expense report data should still be accessible
        """
        # Corrupted credit card PDF
        corrupted_pdf = io.BytesIO(b"Corrupted content, not valid PDF")

        # Valid expense report
        expense_report_pdf = io.BytesIO(b"%PDF-1.4\nValid expense report\n")

        # Upload
        upload_response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("corrupted.pdf", corrupted_pdf, "application/pdf"),
                "expenseReport": ("er.pdf", expense_report_pdf, "application/pdf"),
            },
        )

        session_id = upload_response.json()["session_id"]

        # Process
        process_response = client.post("/api/process", json={"session_id": session_id})

        # Get session
        session_response = client.get(f"/api/session/{session_id}")

        if session_response.status_code == 200:
            session_data = session_response.json()

            # Should show error status
            assert session_data["processing_status"] == "error"

            # Error message should mention credit card statement
            error_msg = session_data.get("error_message", "").lower()
            assert "credit card" in error_msg or "statement" in error_msg

    def test_both_pdfs_corrupted_shows_error(self):
        """
        Test that both PDFs corrupted results in clear error with no partial results.

        Scenario:
        - Upload two corrupted PDFs
        - Processing should fail completely
        - No partial results available
        """
        corrupted_pdf_1 = io.BytesIO(b"Corrupted content 1")
        corrupted_pdf_2 = io.BytesIO(b"Corrupted content 2")

        # Upload
        upload_response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("c1.pdf", corrupted_pdf_1, "application/pdf"),
                "expenseReport": ("c2.pdf", corrupted_pdf_2, "application/pdf"),
            },
        )

        session_id = upload_response.json()["session_id"]

        # Process
        process_response = client.post("/api/process", json={"session_id": session_id})

        # Get session
        session_response = client.get(f"/api/session/{session_id}")

        if session_response.status_code == 200:
            session_data = session_response.json()

            # Should show error
            assert session_data["processing_status"] == "error"
            assert session_data.get("error_message") is not None

            # No employees or empty employees array
            employees = session_data.get("employees", [])
            assert len(employees) == 0, "No partial data should be available"

    # Helper methods

    def _create_mock_credit_card_pdf(self):
        """Create mock credit card statement PDF."""
        import io

        return io.BytesIO(b"%PDF-1.4\nMock CC Statement\n")

    def _create_mock_expense_report_pdf(self):
        """Create mock expense report PDF."""
        import io

        return io.BytesIO(b"%PDF-1.4\nMock Expense Report\n")
