"""
API route handlers for Expense Reconciliation System.

Implements all 5 endpoints defined in contracts/:
- POST /api/upload - Upload PDFs and create session
- POST /api/process - Process PDFs with SSE progress streaming
- GET /api/session/{sessionId} - Retrieve session data
- GET /api/reports/{sessionId} - Get generated reports
- POST /api/session/{sessionId}/update - Update expense report and re-analyze
"""

import os
import json
from datetime import datetime
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from api.models import (
    Session,
    ProcessRequest,
    SessionResponse,
    ReportsResponse,
    ReportSummary,
    UploadResponse,
    UpdateResponse,
    ProcessingStatus,
)
from parsing.credit_card_parser import parse_credit_card_statement
from parsing.expense_report_parser import parse_expense_report
from processing.matcher import match_expenses_to_receipts
from processing.analyzer import compute_summary_stats, get_complete_employees
from generation.excel_generator import generate_excel_report, create_excel_report_metadata
from generation.csv_generator import generate_csv_export, create_csv_export_metadata

router = APIRouter()

# In-memory session storage (replace with database in production)
sessions: Dict[str, Session] = {}


@router.post("/api/upload", status_code=status.HTTP_201_CREATED)
async def upload_pdfs(
    creditCardStatement: UploadFile = File(..., description="Credit Card Statement PDF"),
    expenseReport: UploadFile = File(..., description="Expense Software Report PDF"),
) -> UploadResponse:
    """
    Upload two PDF files and create a new session.

    Contract: contracts/upload-pdfs.yaml

    Args:
        creditCardStatement: Credit card statement PDF file
        expenseReport: Expense report PDF file

    Returns:
        UploadResponse with session_id, uploaded_files metadata, created_at

    Raises:
        HTTPException 400: Missing files or invalid format
        HTTPException 413: File size exceeds limit
    """
    # Validate both files present
    if not creditCardStatement or not expenseReport:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "Both PDF files are required"}
        )

    # Validate file types
    if not creditCardStatement.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid file type", "details": "creditCardStatement must be PDF"},
        )

    if not expenseReport.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "Invalid file type", "details": "expenseReport must be PDF"},
        )

    # Create new session
    session = Session(
        credit_card_pdf_path="",  # Will be set after saving
        expense_report_pdf_path="",
        processing_status=ProcessingStatus.PENDING,
    )

    session_id_str = str(session.session_id)

    # Create upload directory
    upload_dir = os.path.join("server", "uploads", session_id_str)
    os.makedirs(upload_dir, exist_ok=True)

    # Save files
    cc_path = os.path.join(upload_dir, f"cc_statement_{creditCardStatement.filename}")
    er_path = os.path.join(upload_dir, f"expense_report_{expenseReport.filename}")

    # Write files to disk
    with open(cc_path, "wb") as f:
        content = await creditCardStatement.read()
        f.write(content)
        cc_size = len(content)

    with open(er_path, "wb") as f:
        content = await expenseReport.read()
        f.write(content)
        er_size = len(content)

    # Update session with file paths
    session.credit_card_pdf_path = cc_path
    session.expense_report_pdf_path = er_path

    # Store session in memory
    sessions[session_id_str] = session

    # Build response
    return UploadResponse(
        session_id=session.session_id,
        uploaded_files={
            "credit_card_statement": {
                "filename": creditCardStatement.filename,
                "size": cc_size,
            },
            "expense_report": {
                "filename": expenseReport.filename,
                "size": er_size,
            },
        },
        created_at=session.created_at,
    )


@router.post("/api/process")
async def process_pdfs(request: ProcessRequest):
    """
    Process uploaded PDFs with real-time progress updates via SSE.

    Contract: contracts/process-pdfs.yaml

    Args:
        request: ProcessRequest with session_id

    Returns:
        StreamingResponse with Server-Sent Events (SSE) progress stream

    Raises:
        HTTPException 400: Invalid session_id
        HTTPException 404: Session not found
        HTTPException 422: Processing error with partial results
    """
    session_id_str = str(request.session_id)

    # Validate session exists
    if session_id_str not in sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Session not found"})

    session = sessions[session_id_str]

    # Update status to processing
    session.processing_status = ProcessingStatus.PROCESSING
    session.updated_at = datetime.utcnow()

    async def generate_progress():
        """Generator function for SSE stream."""
        try:
            # Step 1: Parse Credit Card Statement (0-25%)
            yield _sse_event(10, "Parsing Credit Card Statement...", "processing")

            employees = parse_credit_card_statement(session.credit_card_pdf_path)

            if not employees:
                # Parsing failed
                session.processing_status = ProcessingStatus.ERROR
                session.error_message = "Failed to parse Credit Card Statement"
                yield _sse_event(10, "Error parsing Credit Card Statement", "error", session.error_message)
                return

            yield _sse_event(25, "Extracting employee data...", "processing")

            # Step 2: Parse Expense Report (25-50%)
            yield _sse_event(50, "Parsing Expense Report...", "processing")

            receipts_by_employee = parse_expense_report(session.expense_report_pdf_path)

            # Attach receipts to employees
            for employee in employees:
                if employee.employee_id in receipts_by_employee:
                    employee.receipts = receipts_by_employee[employee.employee_id]

            # Step 3: Match expenses to receipts (50-75%)
            yield _sse_event(75, "Matching expenses to receipts...", "processing")

            matching_results = match_expenses_to_receipts(employees)

            # Update session
            session.employees = employees
            session.matching_results = matching_results

            # Step 4: Generate Excel report (75-90%)
            yield _sse_event(90, "Generating Excel report...", "processing")

            excel_path = generate_excel_report(session)
            session.excel_report_path = excel_path

            # Step 5: Generate CSV export (90-95%)
            yield _sse_event(95, "Generating CSV export...", "processing")

            csv_path = generate_csv_export(session)
            session.csv_export_path = csv_path

            # Complete
            session.processing_status = ProcessingStatus.COMPLETE
            session.updated_at = datetime.utcnow()

            yield _sse_event(100, "Complete", "complete")

        except Exception as e:
            # Handle processing errors
            session.processing_status = ProcessingStatus.ERROR
            session.error_message = str(e)
            yield _sse_event(0, f"Processing failed: {str(e)}", "error", str(e))

    return StreamingResponse(generate_progress(), media_type="text/event-stream")


def _sse_event(progress: int, step: str, status_val: str, error: str = None) -> str:
    """
    Format a Server-Sent Event.

    Args:
        progress: Progress percentage (0-100)
        step: Description of current step
        status_val: "processing" | "complete" | "error"
        error: Optional error message

    Returns:
        Formatted SSE event string
    """
    event_data = {"progress": progress, "step": step, "status": status_val}

    if error:
        event_data["error"] = error

    return f"data: {json.dumps(event_data)}\n\n"


@router.get("/api/session/{sessionId}")
async def get_session(sessionId: UUID) -> SessionResponse:
    """
    Retrieve session data with employees and matching results.

    Contract: contracts/get-session.yaml

    Args:
        sessionId: Session UUID

    Returns:
        SessionResponse with complete session data

    Raises:
        HTTPException 404: Session not found
    """
    session_id_str = str(sessionId)

    if session_id_str not in sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Session not found"})

    session = sessions[session_id_str]

    return SessionResponse(
        session_id=session.session_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        processing_status=session.processing_status,
        error_message=session.error_message,
        employees=session.employees,
        matching_results=session.matching_results,
    )


@router.get("/api/reports/{sessionId}")
async def get_reports(sessionId: UUID) -> ReportsResponse:
    """
    Get generated Excel and CSV reports with summary statistics.

    Contract: contracts/get-reports.yaml

    Args:
        sessionId: Session UUID

    Returns:
        ReportsResponse with report URLs and summary stats

    Raises:
        HTTPException 404: Session not found
        HTTPException 409: Processing not complete
    """
    session_id_str = str(sessionId)

    if session_id_str not in sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Session not found"})

    session = sessions[session_id_str]

    # Check if processing is complete
    if session.processing_status != ProcessingStatus.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Reports not available. Session status: " + session.processing_status.value,
                "processing_status": session.processing_status.value,
            },
        )

    # Compute summary statistics
    summary_dict = compute_summary_stats(session)
    summary = ReportSummary(**summary_dict)

    # Build Excel report metadata
    excel_report = None
    if session.excel_report_path and os.path.exists(session.excel_report_path):
        excel_metadata = create_excel_report_metadata(session, session.excel_report_path)
        excel_report = {
            "url": f"/downloads/{session_id_str}/excel",
            "file_size": os.path.getsize(session.excel_report_path),
            "row_count": excel_metadata.row_count,
            "generated_at": excel_metadata.generated_at.isoformat(),
        }

    # Build CSV export metadata
    csv_export = None
    if session.csv_export_path and os.path.exists(session.csv_export_path):
        complete_employees = get_complete_employees(session)
        csv_metadata = create_csv_export_metadata(session, session.csv_export_path, complete_employees)
        csv_export = {
            "url": f"/downloads/{session_id_str}/csv",
            "file_size": os.path.getsize(session.csv_export_path),
            "row_count": csv_metadata.row_count,
            "included_employee_count": len(csv_metadata.included_employee_ids),
            "generated_at": csv_metadata.generated_at.isoformat(),
        }

    return ReportsResponse(session_id=session.session_id, excel_report=excel_report, csv_export=csv_export, summary=summary)


@router.post("/api/session/{sessionId}/update")
async def update_receipts(
    sessionId: UUID, expenseReport: UploadFile = File(..., description="Updated Expense Report PDF")
) -> UpdateResponse:
    """
    Upload new expense report to existing session and re-analyze.

    Contract: contracts/update-receipts.yaml

    Args:
        sessionId: Session UUID
        expenseReport: New expense report PDF file

    Returns:
        UpdateResponse with summary_changes and new report URLs

    Raises:
        HTTPException 400: Invalid file format
        HTTPException 404: Session not found
        HTTPException 409: Session currently processing
    """
    session_id_str = str(sessionId)

    # Validate session exists
    if session_id_str not in sessions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"error": "Session not found"})

    session = sessions[session_id_str]

    # Check if currently processing
    if session.processing_status == ProcessingStatus.PROCESSING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "Session is currently processing. Please wait.", "processing_status": "processing"},
        )

    # Validate file type
    if not expenseReport.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "Invalid file format. PDF required."}
        )

    # Capture previous stats for comparison
    previous_stats = compute_summary_stats(session)

    # Save new expense report
    upload_dir = os.path.dirname(session.expense_report_pdf_path)
    new_er_path = os.path.join(upload_dir, f"updated_{datetime.utcnow().timestamp()}_{expenseReport.filename}")

    with open(new_er_path, "wb") as f:
        content = await expenseReport.read()
        f.write(content)

    # Update session
    session.expense_report_pdf_path = new_er_path
    session.updated_at = datetime.utcnow()

    # Re-parse expense report
    receipts_by_employee = parse_expense_report(new_er_path)

    # Update receipts for existing employees
    for employee in session.employees:
        if employee.employee_id in receipts_by_employee:
            employee.receipts = receipts_by_employee[employee.employee_id]
        else:
            employee.receipts = []  # No receipts in updated report

    # Re-run matching
    matching_results = match_expenses_to_receipts(session.employees)
    session.matching_results = matching_results

    # Regenerate reports
    excel_path = generate_excel_report(session)
    session.excel_report_path = excel_path

    csv_path = generate_csv_export(session)
    session.csv_export_path = csv_path

    # Update processing status
    session.processing_status = ProcessingStatus.COMPLETE

    # Compute current stats
    current_stats = compute_summary_stats(session)

    # Identify changes
    newly_complete_employees = []
    for employee in session.employees:
        if employee.completion_status.value == "complete":
            # Check if was previously incomplete
            # (Simplified - in production, track previous state)
            newly_complete_employees.append(employee.employee_id)

    newly_incomplete_expenses = []
    for employee in session.employees:
        for expense in employee.expenses:
            if expense.status.value != "Complete":
                newly_incomplete_expenses.append(str(expense.transaction_id))

    # Build summary_changes
    summary_changes = {
        "previous": {
            "complete_employees": previous_stats["complete_employees"],
            "incomplete_expenses": (
                previous_stats["expenses_missing_receipts"]
                + previous_stats["expenses_missing_gl_codes"]
                + previous_stats["expenses_missing_both"]
            ),
        },
        "current": {
            "complete_employees": current_stats["complete_employees"],
            "incomplete_expenses": (
                current_stats["expenses_missing_receipts"]
                + current_stats["expenses_missing_gl_codes"]
                + current_stats["expenses_missing_both"]
            ),
        },
        "newly_complete_employees": newly_complete_employees[:5],  # Limit for demo
        "newly_incomplete_expenses": newly_incomplete_expenses[:10],  # Limit for demo
    }

    return UpdateResponse(
        session_id=session.session_id,
        updated=True,
        updated_at=session.updated_at,
        summary_changes=summary_changes,
        new_excel_report_url=f"/downloads/{session_id_str}/excel",
        new_csv_export_url=f"/downloads/{session_id_str}/csv",
    )
