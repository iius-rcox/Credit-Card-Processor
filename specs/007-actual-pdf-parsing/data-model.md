# Data Model: Actual PDF Parsing

## New Tables

### employee_aliases

**Purpose**: Maps extracted employee names from PDFs to existing employee records

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Unique identifier |
| extracted_name | VARCHAR(255) | UNIQUE, NOT NULL | Employee name as it appears in PDF |
| employee_id | UUID | NOT NULL, FK → employees(id) ON DELETE CASCADE | Reference to actual employee |
| created_at | TIMESTAMP WITH TIME ZONE | DEFAULT NOW() | Creation timestamp |

**Indexes**:
- `idx_employee_aliases_extracted_name` on `extracted_name` (for fast lookups)
- `idx_employee_aliases_employee_id` on `employee_id` (for employee queries)

**Relationships**:
- `employee_id` → `employees.id` (many-to-one)

## Modified Tables

### transactions

**Added Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| incomplete_flag | BOOLEAN | DEFAULT FALSE | True when required fields (date, amount, employee_name, merchant_name) are missing |
| is_credit | BOOLEAN | DEFAULT FALSE | True when amount is negative (refund/credit) |

**Modified Constraints**:
- **REMOVE** check constraint `amount > 0` (now allows negative values for credits)
- **ADD** index `idx_transactions_incomplete` on `incomplete_flag` WHERE `incomplete_flag = TRUE`

**Existing Columns (relevant for this feature)**:
- `amount`: NUMERIC(12, 2) - Now allows negative values
- `raw_data`: JSONB - Stores original extracted text for debugging

## Entity Relationships

```
Employee (existing)
    │
    ├──< employee_aliases.employee_id (NEW)
    │
    └──< transactions.employee_id (existing)

Transaction (modified)
    ├── incomplete_flag (NEW FIELD)
    ├── is_credit (NEW FIELD)
    └── raw_data (existing, now populated with actual PDF text)
```

## Data Flow

1. **PDF Upload** → Extract text with pdfplumber
2. **Text Extraction** → Apply regex patterns to identify transactions
3. **Employee Resolution**:
   - Try exact match on `employees.name`
   - If not found, try `employee_aliases.extracted_name`
   - If still not found, set `employee_id = NULL` and flag as incomplete
4. **Transaction Creation**:
   - Set `incomplete_flag = TRUE` if any required field is NULL
   - Set `is_credit = TRUE` if `amount < 0`
   - Store original PDF line in `raw_data.raw_text`

## Migration Script

```sql
-- Add employee_aliases table
CREATE TABLE employee_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extracted_name VARCHAR(255) UNIQUE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_employee_aliases_extracted_name ON employee_aliases(extracted_name);
CREATE INDEX idx_employee_aliases_employee_id ON employee_aliases(employee_id);

-- Modify transactions table
ALTER TABLE transactions
ADD COLUMN incomplete_flag BOOLEAN DEFAULT FALSE,
ADD COLUMN is_credit BOOLEAN DEFAULT FALSE;

CREATE INDEX idx_transactions_incomplete ON transactions(incomplete_flag) WHERE incomplete_flag = TRUE;

-- Remove positive-only constraint on amount (allow negatives)
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS chk_transactions_amount;
```

## Validation Rules

1. **EmployeeAlias**:
   - `extracted_name` must be unique (enforced by DB)
   - `employee_id` must reference existing employee (enforced by FK)

2. **Transaction**:
   - `incomplete_flag` set to TRUE if ANY of these are NULL:
     - `transaction_date`
     - `amount`
     - `employee_id`
     - `merchant_name`
   - `is_credit` set to TRUE if `amount < 0`

## Example Data

**employee_aliases**:
```
id                                   | extracted_name     | employee_id                          | created_at
-------------------------------------|--------------------|------------------------------------|---------------------------
550e8400-e29b-41d4-a716-446655440001 | JOHNSMITH          | 123e4567-e89b-12d3-a456-426614174000 | 2025-10-10 12:00:00
550e8400-e29b-41d4-a716-446655440002 | RICHARDBREEDLOVE   | 123e4567-e89b-12d3-a456-426614174001 | 2025-10-10 12:01:00
```

**transactions** (with new fields):
```
id       | employee_id | date       | amount    | merchant_name  | incomplete_flag | is_credit | raw_data
---------|-------------|------------|-----------|----------------|-----------------|-----------|----------
tx_001   | emp_123     | 2025-03-24 | 77.37     | CHEVRON        | false           | false     | {"raw_text": "..."}
tx_002   | emp_123     | NULL       | 118.76    | ELSIES         | true            | false     | {"raw_text": "..."}
tx_003   | emp_456     | 2025-03-26 | -15.00    | AMAZON         | false           | true      | {"raw_text": "..."}
```
