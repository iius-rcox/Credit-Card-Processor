# Research: Actual PDF Parsing

## Overview
Research findings for implementing regex-based PDF text extraction to replace placeholder logic in the Credit Card Processor reconciliation system.

## PDF Text Extraction Library Selection

### Decision: pdfplumber

**Rationale**:
- **Table-aware**: Better at extracting tabular data (credit card statements are tabular)
- **Simple API**: `pdfplumber.open(pdf_path)` → iterate pages → `page.extract_text()`
- **Maintained**: Active development, good documentation
- **Performance**: Fast enough for 10k transactions (target < 30s)

**Installation**: `pdfplumber==0.10.3` (add to requirements.txt)

**Alternatives Considered**:
- **PyPDF2**: Older, less reliable with tables, but more lightweight
- **pypdf**: Newer fork of PyPDF2, but less mature ecosystem
- **PDFMiner**: More powerful but over-engineered for our needs

**Code Example**:
```python
import pdfplumber

with pdfplumber.open("statement.pdf") as pdf:
    text = ""
    for page in pdf.pages:
        text += page.extract_text() + "\n"
```

## Regex Patterns for Transaction Extraction

### Pattern Design

Based on credit card statement format (tab-separated columns):
```
EMPLOYEE_NAME    Expense_Type    Date        Amount    Merchant_Name    Merchant_Address    Status
```

**Master Pattern** (single line transaction):
```regex
^([A-Z][A-Z\s]+?)\s+  # Employee name (all caps, greedy)
(\w+(?: \w+)?)\s+     # Expense type (1-2 words)
(\d{1,2}/\d{1,2}/\d{4})\s+  # Date MM/DD/YYYY
([-]?\$?[\d,]+(?:\.\d{2})?)\s+  # Amount (optional negative, commas)
(.+?)\s{2,}           # Merchant name (non-greedy, until 2+ spaces)
(.+?)\s+              # Merchant address
([\w\s,]+)$           # Status (rest of line)
```

**Field-Specific Patterns**:

1. **Employee Name**: `^([A-Z][A-Z\s]+?(?=\s{2,}))`
   - Matches all-caps names at line start
   - Stops at double-space (column separator)

2. **Date**: `(\d{1,2}/\d{1,2}/\d{4})`
   - Matches MM/DD/YYYY or M/D/YYYY

3. **Amount**: `([-]?\$?[\d,]+(?:\.\d{2})?)`
   - Optional negative sign for credits
   - Optional dollar sign
   - Handles commas (e.g., "1,234.56")
   - Requires 2 decimal places

4. **Merchant Name**: Capture group between date/amount and address
   - Use lookahead to detect address pattern (street number + state)

5. **Expense Type**: `(Fuel|Meals|General Expense|Hotel|Legal|Maintenance|Misc\. Transportation|Business Services)`
   - Enum match for known categories

### Multi-Line Merchant Names

**Problem**: Merchant names may span 2 lines if long
**Solution**: Use `re.MULTILINE` and lookahead for next field:
```python
pattern = r'Merchant:\s*(.+?)(?=\s+\d{5})'  # Stop before ZIP code
```

### Page Breaks

**Problem**: Transaction may split across pages
**Solution**:
1. Concatenate all page text first
2. Use `re.findall()` to match complete transactions globally
3. No special handling needed if text concatenation preserves line breaks

## Employee Alias Data Model

### Database Schema

```sql
CREATE TABLE employee_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extracted_name VARCHAR(255) UNIQUE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_employee_aliases_extracted_name ON employee_aliases(extracted_name);
CREATE INDEX idx_employee_aliases_employee_id ON employee_aliases(employee_id);
```

### Lookup Algorithm

```python
def resolve_employee(extracted_name: str) -> Optional[UUID]:
    # 1. Try exact match on employees table
    employee = db.query(Employee).filter(Employee.name == extracted_name).first()
    if employee:
        return employee.id

    # 2. Try alias lookup
    alias = db.query(EmployeeAlias).filter(EmployeeAlias.extracted_name == extracted_name).first()
    if alias:
        return alias.employee_id

    # 3. Return None (user must create alias manually)
    return None
```

**Performance**: O(1) with index on `extracted_name`

## Incomplete Transaction Handling

### Database Changes

```sql
ALTER TABLE transactions
ADD COLUMN incomplete_flag BOOLEAN DEFAULT FALSE,
ADD COLUMN is_credit BOOLEAN DEFAULT FALSE;

CREATE INDEX idx_transactions_incomplete ON transactions(incomplete_flag) WHERE incomplete_flag = TRUE;
```

### Flagging Logic

```python
def create_transaction(extracted_data: dict) -> Transaction:
    required_fields = ['date', 'amount', 'employee_name', 'merchant_name']
    incomplete = any(extracted_data.get(field) is None for field in required_fields)

    is_credit = extracted_data.get('amount', 0) < 0

    return Transaction(
        **extracted_data,
        incomplete_flag=incomplete,
        is_credit=is_credit
    )
```

## Performance Optimization

### Batch Inserts for 10k Transactions

**Problem**: 10,000 individual INSERT statements → ~10 seconds just for DB roundtrips
**Solution**: Use SQLAlchemy bulk operations

```python
from sqlalchemy.orm import Session

def bulk_insert_transactions(session: Session, transactions: List[dict]):
    session.bulk_insert_mappings(Transaction, transactions)
    session.commit()
```

**Benchmark Target**:
- Text extraction: ~5 seconds (pdfplumber)
- Regex matching: ~2 seconds (compiled patterns)
- DB insert: ~3 seconds (bulk)
- **Total**: ~10 seconds (well under 30s goal)

### Regex Compilation

**Optimization**: Compile patterns once, reuse:
```python
class ExtractionService:
    def __init__(self):
        self.transaction_pattern = re.compile(r'^([A-Z][A-Z\s]+?)...', re.MULTILINE)

    def extract(self, text: str):
        matches = self.transaction_pattern.findall(text)  # Fast!
```

## Error Handling Strategy

### PDF Validation

1. **Check if text-based**: `len(page.extract_text()) > 0`
   - If empty → reject with "Scanned image PDF not supported"

2. **Check page count**: Reasonable limit (e.g., < 500 pages)

3. **Check file size**: Already handled by upload middleware (300MB limit)

### Extraction Error Recovery

**Principle**: Never fail entire PDF due to one bad transaction

```python
def extract_all_transactions(pdf_text: str) -> List[Transaction]:
    transactions = []
    for match in regex.finditer(pdf_text):
        try:
            tx = parse_transaction(match)
            transactions.append(tx)
        except Exception as e:
            logger.warning(f"Skipped malformed transaction: {e}")
            # Create incomplete transaction with raw_text only
            transactions.append(Transaction(
                raw_data={'error': str(e), 'raw_text': match.group(0)},
                incomplete_flag=True
            ))
    return transactions
```

## Integration with Existing System

### Modify `extraction_service.py`

**Current**:
```python
def _extract_credit_transactions(self, text: str) -> List[Dict]:
    return [{"id": "cc_tx_1", "date": "2024-01-15", "amount": 150.00}]  # Placeholder!
```

**New**:
```python
def _extract_credit_transactions(self, text: str) -> List[Dict]:
    pattern = self.credit_transaction_pattern  # Compiled regex
    transactions = []

    for match in pattern.finditer(text):
        employee_name, expense_type, date, amount, merchant, address, status = match.groups()

        transactions.append({
            "employee_name": employee_name.strip(),
            "expense_type": expense_type.strip(),
            "transaction_date": self._parse_date(date),
            "amount": self._parse_amount(amount),
            "merchant_name": merchant.strip(),
            "merchant_address": address.strip(),
            "raw_data": {"raw_text": match.group(0), "status": status}
        })

    return transactions
```

### No Changes to API Contract

**Key insight**: Existing `POST /api/upload` endpoint remains unchanged. Only the extraction service implementation changes. Frontend already handles transactions array in response.

## Testing Strategy

### Unit Tests

1. **Regex pattern tests** (`test_extraction_patterns.py`):
   - Test each field pattern independently
   - Test edge cases (negative amounts, multi-line merchants)
   - Test malformed data (missing fields)

2. **Date/amount parsing** (`test_parsing_utils.py`):
   - Test `_parse_date("03/24/2025")` → `datetime`
   - Test `_parse_amount("-1,234.56")` → `Decimal(-1234.56)`

### Integration Tests

1. **Sample PDF extraction** (`test_extraction_integration.py`):
   - Use actual PDF file from `expected_results_detail`
   - Assert count of transactions
   - Assert specific transaction values match expected

2. **Alias workflow** (`test_alias_integration.py`):
   - Create alias
   - Upload PDF with aliased name
   - Assert transaction linked to correct employee_id

### Performance Tests

```python
def test_10k_transaction_performance():
    # Generate 10k line PDF programmatically
    large_pdf = generate_test_pdf(transaction_count=10000)

    start = time.time()
    transactions = extraction_service.extract(large_pdf)
    elapsed = time.time() - start

    assert len(transactions) == 10000
    assert elapsed < 30  # Within performance target
```

## Dependencies to Add

```
# Add to backend/requirements.txt
pdfplumber==0.10.3
```

## Summary

**Decisions Made**:
1. ✅ pdfplumber for text extraction
2. ✅ Compiled regex patterns for parsing
3. ✅ employee_aliases table for name resolution
4. ✅ incomplete_flag + is_credit columns in transactions
5. ✅ Bulk insert for performance
6. ✅ Error recovery (never fail entire PDF)

**Deferred to Implementation**:
- Exact regex patterns (need real PDF samples to fine-tune)
- Date format variations (handle MM/DD/YYYY and MM/DD/YY)
- Merchant address parsing (may need geocoding later - out of scope for now)

**Risks**:
- **Low**: PDF format may vary by issuer → may need multiple regex patterns
- **Mitigation**: Start with one pattern, add variants as needed

**Next Phase**: Design data models and API contracts based on these research findings.
