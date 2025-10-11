# Extraction API Enhancements

## Overview
This document describes the enhancements to the existing `POST /api/upload` endpoint to support real PDF extraction instead of placeholder data.

## Endpoint: POST /api/upload

**URL**: `/api/upload`
**Method**: POST
**Content-Type**: multipart/form-data

### Request (unchanged)
```
files: List[UploadFile]  # PDF files to upload
```

### Response (structure unchanged, data enhanced)

**Status**: 202 Accepted

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "upload_count": 2,
  "total_transactions": 0,
  "total_receipts": 0,
  "matched_count": 0,
  "created_at": "2025-10-10T12:00:00Z",
  "expires_at": "2025-10-17T12:00:00Z",
  "updated_at": "2025-10-10T12:00:00Z"
}
```

### Extraction Behavior Changes

**Old Behavior** (placeholder):
- Returns hardcoded dummy transaction: `{id: "cc_tx_1", date: "2024-01-15", amount: 150.00}`
- Always returns same data regardless of PDF content

**New Behavior** (actual extraction):
1. Extract text from PDF using pdfplumber
2. Apply regex patterns to identify transactions
3. For each transaction:
   - Extract: employee name, date, amount, merchant name, merchant address, expense type
   - Resolve employee via exact match or alias lookup
   - Flag as incomplete if required fields missing
   - Flag as credit if amount < 0
   - Store original PDF line in `raw_data`
4. Bulk insert all transactions into database
5. Return session with `status="processing"` (background Celery task continues)

### Transaction Schema Enhancements

New fields in transaction objects:

```json
{
  "id": "uuid",
  "employee_id": "uuid",
  "transaction_date": "2025-03-24",
  "amount": 77.37,
  "merchant_name": "CHEVRON 0308017",
  "merchant_address": "27952 WALKER SOUTH, WALKER, LA, 70785",
  "expense_type": "Fuel",
  "incomplete_flag": false,      // NEW: True when required fields missing
  "is_credit": false,            // NEW: True when amount < 0
  "raw_data": {                  // ENHANCED: Now contains actual PDF text
    "raw_text": "RICHARDBREEDLOVE\\tFuel\\t03/24/2025\\t77.37...",
    "extracted_fields": {
      "employee_name": "RICHARDBREEDLOVE",
      "expense_type": "Fuel"
    }
  }
}
```

### Error Responses

**400 Bad Request** - PDF Validation Failed
```json
{
  "detail": "Scanned image PDF not supported. Please upload text-based PDF."
}
```

**500 Internal Server Error** - Extraction Failed
```json
{
  "detail": "Failed to extract transactions from PDF"
}
```

### PDF Validation Rules

1. **Text-based check**: Must extract non-empty text from PDF
   - If `len(page.extract_text()) == 0` for all pages → reject with 400
2. **File type**: Must be valid PDF (already enforced by existing validation)
3. **Size limit**: Max 300MB per file (already enforced)

### Contract Test Requirements

`backend/tests/contract/test_extraction_contract.py`:

```python
def test_upload_extracts_real_transactions():
    """Verify transactions have actual data from PDF, not placeholders"""
    # Upload PDF with known transactions
    response = client.post("/api/upload", files=pdf_file)
    session_id = response.json()["id"]

    # Wait for processing to complete
    time.sleep(5)

    # Get transactions
    transactions = db.query(Transaction).filter_by(session_id=session_id).all()

    # Assert NOT placeholder data
    assert len(transactions) > 0
    assert transactions[0].merchant_name != "AMAZON MARKETPLACE"  # Old placeholder
    assert transactions[0].amount != 150.00  # Old placeholder

    # Assert actual extracted fields
    assert transactions[0].transaction_date is not None
    assert transactions[0].merchant_name is not None
    assert transactions[0].raw_data["raw_text"] is not None

def test_incomplete_flag_set_when_fields_missing():
    """Verify incomplete_flag is set for malformed transactions"""
    # Upload PDF with malformed transaction (missing date)
    response = client.post("/api/upload", files=malformed_pdf)
    session_id = response.json()["id"]

    time.sleep(5)

    transactions = db.query(Transaction).filter_by(session_id=session_id, incomplete_flag=True).all()
    assert len(transactions) > 0

def test_is_credit_flag_set_for_negative_amounts():
    """Verify is_credit flag is set for refunds/credits"""
    # Upload PDF with negative amount transaction
    response = client.post("/api/upload", files=credit_pdf)
    session_id = response.json()["id"]

    time.sleep(5)

    credits = db.query(Transaction).filter_by(session_id=session_id, is_credit=True).all()
    assert len(credits) > 0
    assert credits[0].amount < 0
```

## Backward Compatibility

**No breaking changes**:
- API contract (request/response format) remains unchanged
- Frontend continues to work as-is
- Only the extraction logic (backend service layer) changes
