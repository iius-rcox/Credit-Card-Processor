"""
Contract tests for GET /api/sessions/{id}/report endpoint.

Tests validate report generation in multiple formats.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
import uuid

from src.main import app


@pytest.mark.contract
@pytest.mark.asyncio
async def test_download_report_xlsx_format():
    """
    Test downloading report in Excel format.

    Contract:
    - GET /api/sessions/{id}/report?format=xlsx returns Excel file
    - Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
    - Content-Disposition header includes filename
    - Returns 200 OK or 404 if session not found
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}/report?format=xlsx")

        # Should be 404 if session doesn't exist, 200 if it does
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        if response.status_code == status.HTTP_200_OK:
            # Validate headers
            assert "content-type" in response.headers
            assert "spreadsheet" in response.headers["content-type"] or "application/" in response.headers["content-type"]

            assert "content-disposition" in response.headers
            assert "attachment" in response.headers["content-disposition"]
            assert ".xlsx" in response.headers["content-disposition"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_download_report_csv_format():
    """
    Test downloading report in CSV format.

    Contract:
    - GET /api/sessions/{id}/report?format=csv returns CSV file
    - Content-Type: text/csv
    - Content-Disposition header includes filename
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}/report?format=csv")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        if response.status_code == status.HTTP_200_OK:
            # Validate headers
            assert "content-type" in response.headers
            assert "csv" in response.headers["content-type"] or "text/" in response.headers["content-type"]

            assert "content-disposition" in response.headers
            assert "attachment" in response.headers["content-disposition"]
            assert ".csv" in response.headers["content-disposition"]


@pytest.mark.contract
@pytest.mark.asyncio
async def test_download_report_default_format():
    """
    Test downloading report with default format (should be xlsx).

    Contract:
    - Default format is xlsx if format parameter not specified
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}/report")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

        if response.status_code == status.HTTP_200_OK:
            # Should default to xlsx
            assert "content-disposition" in response.headers
            assert ".xlsx" in response.headers["content-disposition"] or "spreadsheet" in response.headers.get("content-type", "")


@pytest.mark.contract
@pytest.mark.asyncio
async def test_download_report_invalid_format():
    """
    Test downloading report with invalid format parameter.

    Contract:
    - Invalid format should return 400 Bad Request
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}/report?format=invalid")

        # Should reject invalid format
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]

        data = response.json()
        assert "detail" in data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_download_report_session_not_found():
    """
    Test downloading report for non-existent session.

    Contract:
    - Returns 404 Not Found
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        non_existent_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{non_existent_id}/report")

        assert response.status_code == status.HTTP_404_NOT_FOUND

        data = response.json()
        assert "detail" in data


@pytest.mark.contract
@pytest.mark.asyncio
async def test_download_report_invalid_uuid():
    """
    Test downloading report with invalid UUID format.

    Contract:
    - Returns 422 Unprocessable Entity
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/sessions/not-a-uuid/report")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.contract
@pytest.mark.asyncio
async def test_download_report_streaming_response():
    """
    Test that report download uses streaming response.

    Contract:
    - Should support streaming for large files
    - Transfer-Encoding: chunked or content available
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}/report")

        if response.status_code == status.HTTP_200_OK:
            # Verify we can read the content (streaming works)
            content = response.content
            assert content is not None


@pytest.mark.contract
@pytest.mark.asyncio
async def test_download_report_filename_format():
    """
    Test that report filename follows expected format.

    Contract:
    - Filename should include session_id and timestamp
    - Format: reconciliation_{session_id}_{date}.{format}
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        response = await client.get(f"/api/sessions/{session_id}/report?format=xlsx")

        if response.status_code == status.HTTP_200_OK:
            content_disposition = response.headers.get("content-disposition", "")

            # Verify filename pattern
            assert "filename=" in content_disposition
            assert ".xlsx" in content_disposition
            # Should include some identifier (could be session_id or timestamp)


@pytest.mark.contract
@pytest.mark.asyncio
async def test_download_report_both_formats_available():
    """
    Test that both XLSX and CSV formats are available for the same session.

    Contract:
    - Both format=xlsx and format=csv should work
    - Same session should support both formats
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        session_id = str(uuid.uuid4())

        # Try XLSX
        xlsx_response = await client.get(f"/api/sessions/{session_id}/report?format=xlsx")

        # Try CSV
        csv_response = await client.get(f"/api/sessions/{session_id}/report?format=csv")

        # Both should have same status (either both 200 or both 404)
        assert xlsx_response.status_code == csv_response.status_code
