"""
Pydantic models for Expense Reconciliation System API.

This module defines all data models used throughout the application,
including validation rules and computed properties.

Models:
- Employee: Person with credit card expenses
- ExpenseTransaction: Single credit card charge
- ReceiptRecord: Receipt entry from expense report
- Session: User work session with uploaded PDFs
- MatchingResult: Outcome of expense-to-receipt matching
- ExcelReport: Generated Excel file metadata
- CSVExport: Generated CSV file metadata (pvault format)
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, computed_field
import re


# Enums

class CompletionStatus(str, Enum):
    """Employee completion status for CSV export eligibility."""

    COMPLETE = "complete"
    INCOMPLETE = "incomplete"


class ExpenseStatus(str, Enum):
    """Status of expense transaction (missing items)."""

    MISSING_RECEIPT = "Missing Receipt"
    MISSING_GL_CODE = "Missing GL Code"
    MISSING_BOTH = "Missing Both"
    COMPLETE = "Complete"


class ProcessingStatus(str, Enum):
    """Session processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


class MatchReason(str, Enum):
    """Reason for matching result."""

    EXACT_MATCH = "exact_match"
    NO_RECEIPT_FOUND = "no_receipt_found"
    MULTIPLE_MATCHES = "multiple_matches"


# Models

class ReceiptRecord(BaseModel):
    """
    Receipt entry from Expense Software Report PDF.

    Represents documentation that can be matched to expense transactions.
    """

    receipt_id: str = Field(..., min_length=1, description="Unique receipt identifier")
    employee_id: str = Field(..., min_length=4, max_length=6, description="Employee who owns this receipt")
    amount: Decimal = Field(..., gt=0, decimal_places=2, description="Receipt amount")
    gl_code: Optional[str] = Field(None, description="GL account code")
    project_code: Optional[str] = Field(None, description="Project code")

    @field_validator("amount")
    @classmethod
    def validate_amount_precision(cls, v: Decimal) -> Decimal:
        """Ensure amount has exactly 2 decimal places."""
        # Convert to string to check decimal places
        amount_str = str(v)
        if "." in amount_str:
            decimal_part = amount_str.split(".")[1]
            if len(decimal_part) > 2:
                raise ValueError("Amount must have at most 2 decimal places")
        return round(v, 2)

    model_config = {"json_schema_extra": {"example": {
        "receipt_id": "RCP-2025-001",
        "employee_id": "EMP123",
        "amount": "125.50",
        "gl_code": "5000-100",
        "project_code": "PROJ-2025-045",
    }}}


class ExpenseTransaction(BaseModel):
    """
    Single credit card charge from Credit Card Statement PDF.

    Contains all transaction details and computed matching status.
    """

    transaction_id: UUID = Field(default_factory=uuid4, description="Unique transaction identifier")
    employee_id: str = Field(..., min_length=4, max_length=6)
    transaction_date: date = Field(..., description="Date of transaction (ISO 8601)")
    transaction_amount: Decimal = Field(..., gt=0, decimal_places=2)
    transaction_name: str = Field(..., min_length=1, description="Merchant/description")

    # Optional fields from pvault format
    vendor_invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    header_description: Optional[str] = None
    job: Optional[str] = None
    phase: Optional[str] = None
    cost_type: Optional[str] = None
    gl_account: Optional[str] = None
    item_description: Optional[str] = None
    um: Optional[str] = None  # Unit of measure
    tax: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    pay_type: Optional[str] = None

    # Computed fields (set during matching)
    has_receipt: bool = False
    has_gl_code: bool = False

    @field_validator("transaction_amount", "tax")
    @classmethod
    def validate_decimal_precision(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """Ensure decimal amounts have exactly 2 decimal places."""
        if v is None:
            return v
        return round(v, 2)

    @computed_field
    @property
    def status(self) -> ExpenseStatus:
        """
        Derive status from has_receipt and has_gl_code.

        Logic:
        - NOT has_receipt AND NOT has_gl_code: "Missing Both"
        - NOT has_receipt AND has_gl_code: "Missing Receipt"
        - has_receipt AND NOT has_gl_code: "Missing GL Code"
        - has_receipt AND has_gl_code: "Complete"
        """
        if not self.has_receipt and not self.has_gl_code:
            return ExpenseStatus.MISSING_BOTH
        elif not self.has_receipt and self.has_gl_code:
            return ExpenseStatus.MISSING_RECEIPT
        elif self.has_receipt and not self.has_gl_code:
            return ExpenseStatus.MISSING_GL_CODE
        else:
            return ExpenseStatus.COMPLETE


class Employee(BaseModel):
    """
    Person with credit card expenses that need reconciliation.

    Aggregates expenses and receipts for matching and completion analysis.
    """

    employee_id: str = Field(..., min_length=4, max_length=6, description="Unique employee identifier")
    name: str = Field(..., min_length=1, description="Employee full name")
    card_number: str = Field(..., description="Credit card number (16-digit, 4-4-4-4, or masked)")
    expenses: List[ExpenseTransaction] = Field(default_factory=list)
    receipts: List[ReceiptRecord] = Field(default_factory=list)

    @field_validator("employee_id")
    @classmethod
    def validate_employee_id(cls, v: str) -> str:
        """Validate employee_id matches pattern: alphanumeric + hyphens/underscores."""
        pattern = re.compile(r"^[A-Z0-9_-]{4,6}$", re.IGNORECASE)
        if not pattern.match(v):
            raise ValueError(
                "employee_id must be 4-6 alphanumeric characters with optional hyphens/underscores"
            )
        return v

    @field_validator("card_number")
    @classmethod
    def validate_card_number(cls, v: str) -> str:
        """
        Validate card number format.

        Accepts:
        - 16 consecutive digits
        - 4-4-4-4 format with hyphens
        - Masked format (12 asterisks + 4 digits)
        """
        patterns = [
            r"^\d{16}$",  # 16 digits
            r"^\d{4}-\d{4}-\d{4}-\d{4}$",  # 4-4-4-4 format
            r"^\*{12}\d{4}$",  # Masked format
        ]

        for pattern in patterns:
            if re.match(pattern, v):
                return v

        raise ValueError(
            "card_number must be 16 digits, 4-4-4-4 format, or masked (**** **** **** 1234)"
        )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not empty."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @computed_field
    @property
    def completion_status(self) -> CompletionStatus:
        """
        Compute completion status based on expenses.

        Returns "complete" if ALL expenses have has_receipt=True AND has_gl_code=True.
        Otherwise returns "incomplete".
        """
        if not self.expenses:
            return CompletionStatus.INCOMPLETE

        all_complete = all(
            expense.has_receipt and expense.has_gl_code for expense in self.expenses
        )

        return CompletionStatus.COMPLETE if all_complete else CompletionStatus.INCOMPLETE


class MatchingResult(BaseModel):
    """
    Outcome of matching an expense transaction to a receipt record.

    Tracks whether a receipt was found and the matching algorithm's decision.
    """

    expense_transaction_id: UUID = Field(..., description="Reference to ExpenseTransaction")
    matched_receipt_id: Optional[str] = Field(None, description="Reference to ReceiptRecord if matched")
    has_gl_code: bool = Field(..., description="True if GL/project code exists")
    match_reason: MatchReason = Field(..., description="Why this match result occurred")

    @field_validator("match_reason")
    @classmethod
    def validate_match_reason_consistency(cls, v: MatchReason, info) -> MatchReason:
        """
        Validate match_reason consistency with matched_receipt_id.

        Rules:
        - If matched_receipt_id is null, match_reason must be "no_receipt_found" or "multiple_matches"
        - If matched_receipt_id is not null, match_reason must be "exact_match"
        """
        values = info.data
        matched_receipt_id = values.get("matched_receipt_id")

        if matched_receipt_id is None:
            if v not in [MatchReason.NO_RECEIPT_FOUND, MatchReason.MULTIPLE_MATCHES]:
                raise ValueError(
                    "When matched_receipt_id is null, match_reason must be no_receipt_found or multiple_matches"
                )
        else:
            if v != MatchReason.EXACT_MATCH:
                raise ValueError("When matched_receipt_id exists, match_reason must be exact_match")

        return v


class ExcelReport(BaseModel):
    """
    Metadata for generated Excel report listing incomplete expenses.
    """

    report_id: UUID = Field(default_factory=uuid4)
    session_id: UUID = Field(..., description="Parent session")
    file_path: str = Field(..., min_length=1, description="Path to .xlsx file")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    row_count: int = Field(..., ge=0, description="Number of data rows (excluding header)")


class CSVExport(BaseModel):
    """
    Metadata for generated CSV export in pvault format.

    Only includes complete employees (100% receipted and coded).
    """

    export_id: UUID = Field(default_factory=uuid4)
    session_id: UUID = Field(..., description="Parent session")
    file_path: str = Field(..., min_length=1, description="Path to .csv file")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    row_count: int = Field(..., ge=0, description="Number of data rows (excluding header)")
    included_employee_ids: List[str] = Field(default_factory=list, description="Employee IDs in export")


class Session(BaseModel):
    """
    User work session containing uploaded PDFs and analysis results.

    Manages the complete lifecycle from upload through processing to report generation.
    """

    session_id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    credit_card_pdf_path: str = Field(..., min_length=1, description="Path to uploaded CC statement")
    expense_report_pdf_path: str = Field(..., min_length=1, description="Path to uploaded expense report")

    employees: List[Employee] = Field(default_factory=list)
    matching_results: List[MatchingResult] = Field(default_factory=list)

    excel_report_path: Optional[str] = None
    csv_export_path: Optional[str] = None

    processing_status: ProcessingStatus = Field(default=ProcessingStatus.PENDING)
    error_message: Optional[str] = None

    @field_validator("updated_at")
    @classmethod
    def validate_updated_at_after_created_at(cls, v: datetime, info) -> datetime:
        """Ensure updated_at >= created_at."""
        values = info.data
        created_at = values.get("created_at")

        if created_at and v < created_at:
            raise ValueError("updated_at must be >= created_at")

        return v

    model_config = {"json_schema_extra": {"example": {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_at": "2025-10-03T14:30:00Z",
        "updated_at": "2025-10-03T14:35:00Z",
        "credit_card_pdf_path": "uploads/550e8400/cc_statement.pdf",
        "expense_report_pdf_path": "uploads/550e8400/expense_report.pdf",
        "processing_status": "complete",
    }}}


# Request/Response Models for API endpoints

class UploadRequest(BaseModel):
    """Request model for file uploads (handled via multipart, not JSON)."""

    pass  # Files are handled via UploadFile parameters


class UploadResponse(BaseModel):
    """Response model for POST /api/upload."""

    session_id: UUID
    uploaded_files: dict
    created_at: datetime


class ProcessRequest(BaseModel):
    """Request model for POST /api/process."""

    session_id: UUID


class ProcessProgressEvent(BaseModel):
    """Single progress event in SSE stream."""

    progress: int = Field(..., ge=0, le=100)
    step: str
    status: str  # "processing" | "complete" | "error"
    error: Optional[str] = None


class SessionResponse(BaseModel):
    """Response model for GET /api/session/{sessionId}."""

    session_id: UUID
    created_at: datetime
    updated_at: datetime
    processing_status: ProcessingStatus
    error_message: Optional[str] = None
    employees: List[Employee]
    matching_results: List[MatchingResult]


class ReportSummary(BaseModel):
    """Summary statistics for reports."""

    total_employees: int = Field(..., ge=0)
    complete_employees: int = Field(..., ge=0)
    incomplete_employees: int = Field(..., ge=0)
    total_expenses: int = Field(..., ge=0)
    complete_expenses: int = Field(..., ge=0)
    expenses_missing_receipts: int = Field(..., ge=0)
    expenses_missing_gl_codes: int = Field(..., ge=0)
    expenses_missing_both: int = Field(..., ge=0)


class ReportsResponse(BaseModel):
    """Response model for GET /api/reports/{sessionId}."""

    session_id: UUID
    excel_report: Optional[dict] = None  # {url, file_size, row_count, generated_at}
    csv_export: Optional[dict] = None  # {url, file_size, row_count, included_employee_count, generated_at}
    summary: ReportSummary


class UpdateResponse(BaseModel):
    """Response model for POST /api/session/{sessionId}/update."""

    session_id: UUID
    updated: bool
    updated_at: datetime
    summary_changes: dict  # {previous, current, newly_complete_employees, newly_incomplete_expenses}
    new_excel_report_url: Optional[str] = None
    new_csv_export_url: Optional[str] = None
