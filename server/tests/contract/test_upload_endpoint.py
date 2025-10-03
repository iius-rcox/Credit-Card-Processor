"""
Contract tests for POST /api/upload endpoint.

These tests verify the API contract defined in contracts/upload-pdfs.yaml.
They MUST FAIL until the endpoint is implemented (TDD approach).
"""

import io
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestUploadEndpoint:
    """Test suite for POST /api/upload endpoint contract."""

    def test_upload_two_pdfs_success(self):
        """
        Test successful upload of two PDF files.

        Expected: 201 status, session_id (UUID), uploaded_files object, created_at timestamp
        """
        # Create mock PDF files
        credit_card_pdf = io.BytesIO(b"%PDF-1.4 mock credit card statement")
        expense_report_pdf = io.BytesIO(b"%PDF-1.4 mock expense report")

        # Upload both files
        response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("statement.pdf", credit_card_pdf, "application/pdf"),
                "expenseReport": ("expense_report.pdf", expense_report_pdf, "application/pdf"),
            },
        )

        # Assert response structure matches contract
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

        data = response.json()

        # Assert required fields present
        assert "session_id" in data, "Response must contain session_id"
        assert "uploaded_files" in data, "Response must contain uploaded_files"
        assert "created_at" in data, "Response must contain created_at"

        # Assert session_id is UUID format
        session_id = data["session_id"]
        assert isinstance(session_id, str), "session_id must be a string"
        assert len(session_id) == 36, "session_id must be UUID format (36 chars with hyphens)"
        assert session_id.count("-") == 4, "UUID must have 4 hyphens"

        # Assert uploaded_files structure
        uploaded_files = data["uploaded_files"]
        assert "credit_card_statement" in uploaded_files
        assert "expense_report" in uploaded_files

        # Assert credit_card_statement metadata
        cc_meta = uploaded_files["credit_card_statement"]
        assert "filename" in cc_meta
        assert "size" in cc_meta
        assert isinstance(cc_meta["size"], int)
        assert cc_meta["size"] > 0

        # Assert expense_report metadata
        er_meta = uploaded_files["expense_report"]
        assert "filename" in er_meta
        assert "size" in er_meta
        assert isinstance(er_meta["size"], int)
        assert er_meta["size"] > 0

        # Assert created_at is ISO 8601 datetime
        assert isinstance(data["created_at"], str)
        # Simple check for datetime format (contains T and Z or +)
        assert "T" in data["created_at"], "created_at must be ISO 8601 format with T separator"

    def test_upload_missing_credit_card_statement(self):
        """
        Test upload with missing creditCardStatement file.

        Expected: 400 status with error message
        """
        expense_report_pdf = io.BytesIO(b"%PDF-1.4 mock expense report")

        response = client.post(
            "/api/upload",
            files={
                "expenseReport": ("expense_report.pdf", expense_report_pdf, "application/pdf"),
            },
        )

        assert response.status_code == 400, f"Expected 400 for missing file, got {response.status_code}"

        data = response.json()
        assert "error" in data, "Error response must contain 'error' field"
        # Error message should mention missing or required files
        assert "required" in data["error"].lower() or "missing" in data["error"].lower()

    def test_upload_missing_expense_report(self):
        """
        Test upload with missing expenseReport file.

        Expected: 400 status with error message
        """
        credit_card_pdf = io.BytesIO(b"%PDF-1.4 mock credit card statement")

        response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("statement.pdf", credit_card_pdf, "application/pdf"),
            },
        )

        assert response.status_code == 400, f"Expected 400 for missing file, got {response.status_code}"

        data = response.json()
        assert "error" in data, "Error response must contain 'error' field"

    def test_upload_no_files(self):
        """
        Test upload with no files provided.

        Expected: 400 status with error message
        """
        response = client.post("/api/upload")

        assert response.status_code == 400 or response.status_code == 422, (
            f"Expected 400/422 for no files, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data or "detail" in data, (
            "Error response must contain 'error' or 'detail' field"
        )

    def test_upload_oversized_file(self):
        """
        Test upload with file exceeding size limit (10MB).

        Expected: 413 status with error message
        Note: This test creates a large mock file to trigger size limit
        """
        # Create a 11MB mock PDF (exceeds 10MB limit)
        large_pdf = io.BytesIO(b"%PDF-1.4" + b"x" * (11 * 1024 * 1024))
        expense_report_pdf = io.BytesIO(b"%PDF-1.4 mock expense report")

        response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("large_statement.pdf", large_pdf, "application/pdf"),
                "expenseReport": ("expense_report.pdf", expense_report_pdf, "application/pdf"),
            },
        )

        # Note: Size limit might be enforced at different layers (FastAPI, nginx, etc.)
        # Accept either 413 (Payload Too Large) or 400 (Bad Request)
        assert response.status_code in [400, 413], (
            f"Expected 400 or 413 for oversized file, got {response.status_code}"
        )

        data = response.json()
        assert "error" in data, "Error response must contain 'error' field"

    def test_upload_invalid_file_type(self):
        """
        Test upload with non-PDF file.

        Expected: 400 status with error about invalid file type
        """
        # Upload a text file instead of PDF
        text_file = io.BytesIO(b"This is not a PDF file")
        expense_report_pdf = io.BytesIO(b"%PDF-1.4 mock expense report")

        response = client.post(
            "/api/upload",
            files={
                "creditCardStatement": ("statement.txt", text_file, "text/plain"),
                "expenseReport": ("expense_report.pdf", expense_report_pdf, "application/pdf"),
            },
        )

        # Should reject non-PDF files
        assert response.status_code == 400, f"Expected 400 for invalid file type, got {response.status_code}"

        data = response.json()
        assert "error" in data, "Error response must contain 'error' field"
