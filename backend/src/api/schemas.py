"""
Pydantic schemas for API requests and responses.

This module defines data models for FastAPI endpoints.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Session schemas
class SessionBase(BaseModel):
    """Base session schema."""
    status: str
    upload_count: int
    total_transactions: int
    total_receipts: int
    matched_count: int
    current_phase: Optional[str] = None
    overall_percentage: Optional[Decimal] = None
    processing_progress: Optional[dict] = None
    summary: Optional[str] = None  # Summary text for frontend display


class SessionResponse(SessionBase):
    """Session response schema."""
    id: UUID
    created_at: datetime
    expires_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Employee schemas
class EmployeeResponse(BaseModel):
    """Employee response schema."""
    id: UUID
    employee_number: str
    name: str
    department: Optional[str] = None
    cost_center: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Transaction schemas
class TransactionResponse(BaseModel):
    """Transaction response schema."""
    id: UUID
    transaction_date: date
    post_date: Optional[date] = None
    amount: Decimal
    currency: str
    merchant_name: str
    merchant_category: Optional[str] = None
    description: Optional[str] = None
    card_last_four: Optional[str] = None
    reference_number: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Receipt schemas
class ReceiptResponse(BaseModel):
    """Receipt response schema."""
    id: UUID
    receipt_date: date
    amount: Decimal
    currency: str
    vendor_name: str
    file_name: str
    file_size: int
    mime_type: str
    ocr_confidence: Optional[Decimal] = None
    processing_status: str
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# MatchResult schemas
class MatchResultResponse(BaseModel):
    """Match result response schema."""
    id: UUID
    confidence_score: Decimal
    match_status: str
    match_reason: Optional[str] = None
    amount_difference: Optional[Decimal] = None
    date_difference_days: Optional[int] = None
    merchant_similarity: Optional[Decimal] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# Session detail (with nested relationships)
class SessionDetailResponse(SessionBase):
    """Detailed session response with all related data."""
    id: UUID
    created_at: datetime
    expires_at: datetime
    updated_at: datetime
    employees: List[EmployeeResponse] = []
    transactions: List[TransactionResponse] = []
    receipts: List[ReceiptResponse] = []
    match_results: List[MatchResultResponse] = []

    model_config = {"from_attributes": True}


# Pagination
class PaginatedSessionsResponse(BaseModel):
    """Paginated sessions response."""
    items: List[SessionResponse]
    total: int
    page: int
    page_size: int
    has_next: bool

    @staticmethod
    def create(sessions: List, total: int, page: int, page_size: int):
        """Helper to create paginated response."""
        has_next = (page * page_size) < total
        return PaginatedSessionsResponse(
            items=sessions,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next
        )


# Error response
class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    error_code: Optional[str] = None
