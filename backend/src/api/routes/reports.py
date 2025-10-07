"""
Reports API endpoint.

GET /api/sessions/{id}/report - Generate and stream reconciliation report.
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from ..dependencies import get_report_service
from ...services.report_service import ReportService


router = APIRouter(tags=["reports"])


@router.get(
    "/sessions/{session_id}/report",
    summary="Download reconciliation report",
    description="""
    Generate and download reconciliation report in Excel or CSV format.

    **Formats:**
    - **xlsx** (default): Excel workbook with 3 sheets (Summary, Transactions, Receipts)
    - **csv**: CSV file with combined transaction/receipt data

    **Excel Report Contents:**
    - Summary sheet: Session metadata, statistics, employee list
    - Transactions sheet: All transactions with match status and confidence
    - Receipts sheet: All receipts with matched transaction references

    **CSV Report Contents:**
    - Combined view: One row per transaction with matched receipt data

    **Response:**
    - 200 OK: Report file stream
    - 400 Bad Request: Invalid format parameter
    - 404 Not Found: Session not found or expired
    - 500 Internal Server Error: Report generation error
    """
)
async def download_report(
    session_id: UUID,
    format: Literal["xlsx", "csv"] = Query(
        "xlsx",
        description="Report format (xlsx or csv)"
    ),
    report_service: ReportService = Depends(get_report_service)
):
    """
    Generate and download reconciliation report.

    Args:
        session_id: UUID of the session
        format: Report format (xlsx or csv)
        report_service: Injected ReportService

    Returns:
        StreamingResponse with report file

    Raises:
        HTTPException 400: If invalid format
        HTTPException 404: If session not found
        HTTPException 500: If report generation fails
    """
    try:
        if format == "xlsx":
            # Generate Excel report
            report_bytes = await report_service.generate_excel_report(session_id)

            return StreamingResponse(
                iter([report_bytes]),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=reconciliation_{session_id}.xlsx"
                }
            )

        elif format == "csv":
            # Generate CSV report
            report_csv = await report_service.generate_csv_report(session_id)

            return StreamingResponse(
                iter([report_csv]),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=reconciliation_{session_id}.csv"
                }
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format '{format}'. Must be 'xlsx' or 'csv'."
            )

    except ValueError as e:
        # Session not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )
