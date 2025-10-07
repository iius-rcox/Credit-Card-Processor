"""
Contract tests for POST /api/upload endpoint.

These tests validate the API contract for file upload functionality.
Tests should verify request/response schemas, validation rules, and error handling.
"""

import io
import pytest
from httpx import AsyncClient
from fastapi import status

from src.main import app


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_valid_pdf_files():
    """
    Test uploading valid PDF files.

    Contract:
    - POST /api/upload accepts multipart/form-data
    - Response includes session_id, status="processing", created_at, expires_at
    - Returns 202 Accepted
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create mock PDF files
        files = [
            ("files", ("statement.pdf", io.BytesIO(b"%PDF-1.4 mock content"), "application/pdf")),
            ("files", ("receipt1.pdf", io.BytesIO(b"%PDF-1.4 mock content"), "application/pdf")),
        ]

        response = await client.post("/api/upload", files=files)

        # Assert response
        assert response.status_code == status.HTTP_202_ACCEPTED

        data = response.json()
        assert "id" in data
        assert "status" in data
        assert data["status"] == "processing"
        assert "created_at" in data
        assert "expires_at" in data
        assert "upload_count" in data
        assert data["upload_count"] == 2


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_file_size_validation():
    """
    Test file size validation (max 10MB per file).

    Contract:
    - Files larger than 10MB should be rejected
    - Returns 400 Bad Request with validation error
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create a file larger than 10MB (10 * 1024 * 1024 bytes)
        large_file_content = b"%PDF-1.4" + (b"x" * (11 * 1024 * 1024))
        files = [
            ("files", ("large.pdf", io.BytesIO(large_file_content), "application/pdf")),
        ]

        response = await client.post("/api/upload", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "size" in data["detail"].lower() or "10mb" in data["detail"].lower()


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_file_count_validation():
    """
    Test file count validation (max 100 files).

    Contract:
    - More than 100 files should be rejected
    - Returns 400 Bad Request
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create 101 files
        files = [
            ("files", (f"file{i}.pdf", io.BytesIO(b"%PDF-1.4 content"), "application/pdf"))
            for i in range(101)
        ]

        response = await client.post("/api/upload", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "100" in data["detail"] or "count" in data["detail"].lower()


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_file_type_validation():
    """
    Test file type validation (only PDFs allowed).

    Contract:
    - Non-PDF files should be rejected
    - Returns 400 Bad Request
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        files = [
            ("files", ("document.docx", io.BytesIO(b"not a pdf"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")),
        ]

        response = await client.post("/api/upload", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data
        assert "pdf" in data["detail"].lower() or "type" in data["detail"].lower()


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_no_files():
    """
    Test upload with no files.

    Contract:
    - Empty upload should be rejected
    - Returns 400 Bad Request
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/upload", files=[])

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "detail" in data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_upload_response_schema():
    """
    Test that upload response matches the expected schema.

    Contract:
    - Response must include all required fields
    - Field types must be correct
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        files = [
            ("files", ("test.pdf", io.BytesIO(b"%PDF-1.4 content"), "application/pdf")),
        ]

        response = await client.post("/api/upload", files=files)

        assert response.status_code == status.HTTP_202_ACCEPTED

        data = response.json()

        # Required fields
        required_fields = ["id", "created_at", "expires_at", "status", "upload_count"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Validate types
        assert isinstance(data["id"], str)
        assert isinstance(data["created_at"], str)
        assert isinstance(data["expires_at"], str)
        assert isinstance(data["status"], str)
        assert isinstance(data["upload_count"], int)

        # Validate status enum
        assert data["status"] in ["processing", "completed", "failed", "expired"]
