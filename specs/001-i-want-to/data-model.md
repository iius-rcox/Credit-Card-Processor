# Data Model: Expense Reconciliation System

**Feature**: Expense Reconciliation System
**Date**: 2025-10-03
**Status**: Complete

## Overview

This document defines the data entities, their attributes, relationships, and validation rules for the Expense Reconciliation System.

---

## Entity Definitions

### 1. Employee

Represents a person with credit card expenses that need reconciliation.

**Attributes:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| employee_id | string | Yes | 4-6 chars, alphanumeric + hyphens/underscores | Unique employee identifier |
| name | string | Yes | Non-empty | Employee full name |
| card_number | string | Yes | 16-digit OR 4-4-4-4 format OR masked (**** **** **** 1234) | Credit card number |
| expenses | ExpenseTransaction[] | Yes | Array (may be empty) | List of all expense transactions |
| receipts | ReceiptRecord[] | Yes | Array (may be empty) | List of all receipt records |
| completion_status | enum | Yes | "complete" \| "incomplete" | Eligibility for CSV export |

**Validation Rules:**
- `employee_id` matches pattern: `/^[A-Z0-9_-]{4,6}$/i`
- `name` cannot be empty string
- `card_number` must match one of three formats:
  - 16 consecutive digits: `/^\d{16}$/`
  - 4-4-4-4 format: `/^\d{4}-\d{4}-\d{4}-\d{4}$/`
  - Masked format: `/^\*{12}\d{4}$/`
- `completion_status = "complete"` if and only if all expenses have `has_receipt=true` AND `has_gl_code=true`

**State Transitions:**
```
Initial State: completion_status = "incomplete"

On all expenses complete:
  "incomplete" → "complete" (eligible for CSV export)

On any expense becomes incomplete:
  "complete" → "incomplete" (excluded from CSV export)
```

**Relationships:**
- Has many `ExpenseTransaction` (1:N)
- Has many `ReceiptRecord` (1:N)
- Belongs to one `Session` (N:1)

---

### 2. ExpenseTransaction

Represents a single credit card charge from the Credit Card Statement PDF.

**Attributes:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| transaction_id | string (UUID) | Yes | UUID v4 format | Unique transaction identifier |
| employee_id | string | Yes | Foreign key to Employee | Owner of this expense |
| transaction_date | date | Yes | ISO 8601 format (YYYY-MM-DD) | Date of transaction |
| transaction_amount | decimal | Yes | Positive number, 2 decimal places | Dollar amount |
| transaction_name | string | Yes | Non-empty | Transaction description/merchant |
| vendor_invoice_number | string | No | - | Invoice number if available |
| invoice_date | date | No | ISO 8601 format | Invoice date if available |
| header_description | string | No | - | Additional description |
| job | string | No | - | Job code from receipt |
| phase | string | No | - | Phase code from receipt |
| cost_type | string | No | - | Cost type from receipt |
| gl_account | string | No | - | GL account code from receipt |
| item_description | string | No | - | Item description from receipt |
| um | string | No | - | Unit of measure |
| tax | decimal | No | Positive, 2 decimals | Tax amount |
| pay_type | string | No | - | Payment type |
| has_receipt | boolean | Yes | Computed field | True if matching receipt exists |
| has_gl_code | boolean | Yes | Computed field | True if gl_account OR project_code exists |
| status | enum | Yes | Computed field | "Missing Receipt" \| "Missing GL Code" \| "Missing Both" \| "Complete" |

**Validation Rules:**
- `transaction_id` matches UUID v4 pattern: `/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i`
- `transaction_amount > 0` and has exactly 2 decimal places
- `transaction_date` is valid ISO 8601 date
- `status` derivation logic:
  ```
  if NOT has_receipt AND NOT has_gl_code: status = "Missing Both"
  if NOT has_receipt AND has_gl_code: status = "Missing Receipt"
  if has_receipt AND NOT has_gl_code: status = "Missing GL Code"
  if has_receipt AND has_gl_code: status = "Complete"
  ```

**Computed Fields:**
- `has_receipt`: Set to `true` if a `ReceiptRecord` exists with matching `employee_id` and `amount`
- `has_gl_code`: Set to `true` if `gl_account` is not null/empty
- `status`: Derived from `has_receipt` and `has_gl_code` using logic above

**Relationships:**
- Belongs to one `Employee` (N:1)
- May match to one `ReceiptRecord` (1:1 optional)
- Belongs to one `Session` (N:1)

---

### 3. ReceiptRecord

Represents a receipt entry from the Expense Software Report PDF.

**Attributes:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| receipt_id | string | Yes | Non-empty, unique | Receipt identifier from PDF |
| employee_id | string | Yes | Foreign key to Employee | Owner of this receipt |
| amount | decimal | Yes | Positive, 2 decimals | Receipt amount |
| gl_code | string | No | - | GL account code |
| project_code | string | No | - | Project code |

**Validation Rules:**
- `amount > 0` and has exactly 2 decimal places
- At least one of `gl_code` or `project_code` should be present (warning if both missing)

**Relationships:**
- Belongs to one `Employee` (N:1)
- May match to one `ExpenseTransaction` (1:1 optional)
- Belongs to one `Session` (N:1)

---

### 4. Session

Represents a user's work session containing uploaded PDFs and analysis results.

**Attributes:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| session_id | string (UUID) | Yes | UUID v4 format | Unique session identifier |
| created_at | timestamp | Yes | ISO 8601 datetime | Session creation time |
| updated_at | timestamp | Yes | ISO 8601 datetime | Last update time |
| credit_card_pdf_path | string | Yes | Valid file path | Path to uploaded CC statement |
| expense_report_pdf_path | string | Yes | Valid file path | Path to uploaded expense report |
| employees | Employee[] | Yes | Array (may be empty) | All employees in this session |
| matching_results | MatchingResult[] | Yes | Array (may be empty) | All matching results |
| excel_report_path | string | No | Valid file path | Path to generated Excel report |
| csv_export_path | string | No | Valid file path | Path to generated CSV export |
| processing_status | enum | Yes | "pending" \| "processing" \| "complete" \| "error" | Current processing state |
| error_message | string | No | - | Error details if status = "error" |

**Validation Rules:**
- `session_id` matches UUID v4 pattern
- `created_at <= updated_at`
- PDF paths must point to existing .pdf files
- `processing_status` determines allowed operations

**State Transitions:**
```
"pending" → "processing" (user initiates processing)
"processing" → "complete" (processing succeeds)
"processing" → "error" (processing fails, partial results may exist)
"error" → "processing" (user retries)
"complete" → "processing" (user uploads new expense report)
```

**Relationships:**
- Has many `Employee` (1:N)
- Has many `MatchingResult` (1:N)
- Has one `ExcelReport` (1:1 optional)
- Has one `CSVExport` (1:1 optional)

---

### 5. MatchingResult

Represents the outcome of matching an expense to a receipt.

**Attributes:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| expense_transaction_id | string (UUID) | Yes | Foreign key | Reference to ExpenseTransaction |
| matched_receipt_id | string | No | Foreign key or null | Reference to ReceiptRecord if matched |
| has_gl_code | boolean | Yes | - | True if GL/project code exists |
| match_reason | enum | Yes | "exact_match" \| "no_receipt_found" \| "multiple_matches" | Why this match result occurred |

**Validation Rules:**
- If `matched_receipt_id` is null, `match_reason` must be "no_receipt_found" or "multiple_matches"
- If `matched_receipt_id` is not null, `match_reason` must be "exact_match"

**Matching Algorithm:**
```
FOR EACH expense IN expenses:
  matching_receipts = receipts WHERE
    receipt.employee_id = expense.employee_id AND
    receipt.amount = expense.transaction_amount

  IF matching_receipts.count = 1:
    matched_receipt_id = matching_receipts[0].receipt_id
    match_reason = "exact_match"
    has_gl_code = (matching_receipts[0].gl_code IS NOT NULL OR
                    matching_receipts[0].project_code IS NOT NULL)

  ELSE IF matching_receipts.count = 0:
    matched_receipt_id = NULL
    match_reason = "no_receipt_found"
    has_gl_code = FALSE

  ELSE IF matching_receipts.count > 1:
    matched_receipt_id = NULL  # Ambiguous, cannot auto-match
    match_reason = "multiple_matches"
    has_gl_code = FALSE
```

**Relationships:**
- Belongs to one `ExpenseTransaction` (1:1)
- References one `ReceiptRecord` (N:1 optional)
- Belongs to one `Session` (N:1)

---

### 6. ExcelReport

Represents the generated Excel file listing incomplete expenses.

**Attributes:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| report_id | string (UUID) | Yes | UUID v4 format | Unique report identifier |
| session_id | string (UUID) | Yes | Foreign key to Session | Parent session |
| file_path | string | Yes | Valid .xlsx file path | Path to Excel file |
| generated_at | timestamp | Yes | ISO 8601 datetime | Generation timestamp |
| row_count | integer | Yes | >= 0 | Number of data rows (excluding header) |

**Excel File Structure:**
| Column | Data Type | Example | Description |
|--------|-----------|---------|-------------|
| Employee ID | Text | EMP123 | Employee identifier |
| Employee Name | Text | John Doe | Full name |
| Card Number | Text | **** **** **** 1234 | Masked card number |
| Transaction Date | Date | 2025-09-15 | Date of expense |
| Transaction Amount | Currency | $125.50 | Dollar amount |
| Transaction Name | Text | Amazon Purchase | Merchant/description |
| Status | Text | Missing Receipt \| Missing GL Code \| Missing Both | Issue type |

**Excel Formatting:**
- Header row: Bold font, light gray background
- Status column conditional formatting:
  - "Missing Both": Red background (#FFC7CE)
  - "Missing Receipt": Yellow background (#FFEB9C)
  - "Missing GL Code": Orange background (#FFD966)
- All columns auto-width
- Freeze top row for scrolling

**Validation Rules:**
- Only includes expenses where `status != "Complete"`
- Sorted by Employee ID, then Transaction Date

**Relationships:**
- Belongs to one `Session` (1:1)

---

### 7. CSVExport (pvault format)

Represents the generated CSV file for import into pvault system.

**Attributes:**
| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| export_id | string (UUID) | Yes | UUID v4 format | Unique export identifier |
| session_id | string (UUID) | Yes | Foreign key to Session | Parent session |
| file_path | string | Yes | Valid .csv file path | Path to CSV file |
| generated_at | timestamp | Yes | ISO 8601 datetime | Generation timestamp |
| row_count | integer | Yes | >= 0 | Number of data rows (excluding header) |
| included_employee_ids | string[] | Yes | Array of employee IDs | Employees in this export |

**CSV File Structure (18 columns):**
| Column # | Column Name | Data Type | Example | Required |
|----------|-------------|-----------|---------|----------|
| 1 | Transaction ID | UUID | 550e8400-e29b-41d4-a716-446655440000 | Yes |
| 2 | Transaction Date | Date (YYYY-MM-DD) | 2025-09-15 | Yes |
| 3 | Transaction Amount | Decimal | 125.50 | Yes |
| 4 | Transaction Name | Text | Amazon Purchase | Yes |
| 5 | Vendor Invoice # | Text | INV-2025-001 | No |
| 6 | Invoice Date | Date (YYYY-MM-DD) | 2025-09-14 | No |
| 7 | Header Description | Text | Office Supplies | No |
| 8 | Job | Text | JOB-2025-045 | No |
| 9 | Phase | Text | Phase 1 | No |
| 10 | Cost Type | Text | Materials | No |
| 11 | GL Account | Text | 5000-100 | No |
| 12 | Item Description | Text | Printer Paper | No |
| 13 | UM | Text | EA | No |
| 14 | Tax | Decimal | 10.50 | No |
| 15 | Pay Type | Text | Credit | No |
| 16 | Card Holder | Text | John Doe | Yes |
| 17 | Credit Card Number | Text | **** **** **** 1234 | Yes |
| 18 | Credit Card Vendor | Text | Visa | Yes |

**Validation Rules:**
- **CRITICAL**: Only includes employees where `completion_status = "complete"`
- Only includes transactions where `status = "Complete"`
- All amounts formatted with 2 decimal places, no currency symbols
- Dates in YYYY-MM-DD format
- UTF-8 encoding
- CRLF line endings
- QUOTE_MINIMAL quoting strategy

**Exclusion Logic:**
```
FOR EACH employee IN session.employees:
  IF employee.completion_status = "incomplete":
    EXCLUDE all of employee's transactions from CSV
  ELSE:
    INCLUDE all of employee's transactions in CSV
```

**Relationships:**
- Belongs to one `Session` (1:1)
- Includes subset of `ExpenseTransaction` (only complete ones)

---

## Entity Relationship Diagram

```
Session (1) ──────────────────────── (N) Employee
   │                                     │
   │                                     ├─ (N) ExpenseTransaction
   │                                     └─ (N) ReceiptRecord
   │
   ├─ (N) MatchingResult
   │       └─ (1) ExpenseTransaction
   │       └─ (0..1) ReceiptRecord
   │
   ├─ (0..1) ExcelReport
   └─ (0..1) CSVExport
```

---

## Validation Summary

| Entity | Primary Key | Required Fields | Unique Constraints |
|--------|-------------|-----------------|-------------------|
| Employee | employee_id | employee_id, name, card_number, completion_status | employee_id per session |
| ExpenseTransaction | transaction_id | transaction_id, employee_id, transaction_date, transaction_amount, transaction_name, has_receipt, has_gl_code, status | transaction_id globally |
| ReceiptRecord | receipt_id | receipt_id, employee_id, amount | receipt_id per session |
| Session | session_id | session_id, created_at, updated_at, credit_card_pdf_path, expense_report_pdf_path, processing_status | session_id globally |
| MatchingResult | (expense_transaction_id) | expense_transaction_id, has_gl_code, match_reason | expense_transaction_id per session |
| ExcelReport | report_id | report_id, session_id, file_path, generated_at, row_count | report_id globally, session_id (1:1) |
| CSVExport | export_id | export_id, session_id, file_path, generated_at, row_count, included_employee_ids | export_id globally, session_id (1:1) |

---

## Next Steps

- Create OpenAPI contracts in `/contracts` directory
- Generate contract tests for all 5 API endpoints
- Create quickstart.md with test scenarios
- Update .cursorrules agent context file

---

*Data model complete: 2025-10-03*
