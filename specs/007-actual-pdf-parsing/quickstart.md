# Quickstart: Actual PDF Parsing

This document provides step-by-step integration test scenarios for the actual PDF parsing feature.

## Prerequisites

1. Backend server running with database migrated
2. Sample PDF files available (see `expected_results_detail`)
3. At least one employee record in database

## Scenario 1: Extract Transactions with Complete Data

**Objective**: Verify all transactions are extracted from a well-formed PDF

### Steps

1. Create test PDF with 50 complete transactions
   ```bash
   # Use existing test data
   cp expected_results_detail test_50_transactions.txt
   # Convert to PDF (or use existing credit card statement PDF)
   ```

2. Upload PDF via API
   ```bash
   curl -X POST http://localhost:8000/api/upload \
     -F "files=@test_50_transactions.pdf"
   ```

3. Wait for processing to complete (check session status)
   ```bash
   SESSION_ID="<from step 2>"
   curl http://localhost:8000/api/sessions/$SESSION_ID
   # Wait until status != "processing"
   ```

4. Query transactions
   ```bash
   curl http://localhost:8000/api/sessions/$SESSION_ID/transactions
   ```

### Expected Results

- ✅ Response contains 50 transactions
- ✅ All transactions have `incomplete_flag = false`
- ✅ Employee names match existing records or are null (need aliases)
- ✅ All dates are parsed correctly (format: YYYY-MM-DD)
- ✅ All amounts are numeric with 2 decimal places
- ✅ All merchant names are non-empty strings
- ✅ `raw_data` contains original PDF line for each transaction

### Validation Query

```sql
SELECT
  COUNT(*) as total_count,
  SUM(CASE WHEN incomplete_flag = false THEN 1 ELSE 0 END) as complete_count,
  SUM(CASE WHEN employee_id IS NOT NULL THEN 1 ELSE 0 END) as with_employee_count
FROM transactions
WHERE session_id = '<session_id>';

-- Expected: total_count=50, complete_count=50
```

---

## Scenario 2: Handle Incomplete Transactions

**Objective**: Verify system gracefully handles malformed transactions

### Steps

1. Create PDF with one transaction missing the date field
   ```
   JOHNSMITH	Meals	77.37	RESTAURANT	123 MAIN ST	Missing Coding
   ```

2. Upload PDF

3. Query transactions and check for incomplete flag

### Expected Results

- ✅ Transaction is created (not skipped)
- ✅ `transaction_date = NULL`
- ✅ `incomplete_flag = true`
- ✅ Other fields populated correctly
- ✅ `raw_data.raw_text` contains the malformed line

### Validation Query

```sql
SELECT * FROM transactions
WHERE session_id = '<session_id>' AND incomplete_flag = true;

-- Expect 1 row with transaction_date IS NULL
```

---

## Scenario 3: Handle Credits/Refunds

**Objective**: Verify negative amounts are handled correctly

### Steps

1. Create PDF with negative amount transaction
   ```
   JOHNSMITH	General Expense	03/28/2025	-15.50	AMAZON	REFUND	Complete
   ```

2. Upload PDF

3. Query transactions

### Expected Results

- ✅ `amount = -15.50` (negative value preserved)
- ✅ `is_credit = true`
- ✅ `incomplete_flag = false` (all required fields present)

### Validation Query

```sql
SELECT amount, is_credit FROM transactions
WHERE session_id = '<session_id>' AND is_credit = true;

-- Expect: amount < 0, is_credit = true
```

---

## Scenario 4: Create and Use Employee Alias

**Objective**: Verify alias mapping resolves employee names

### Steps

1. Upload PDF with unknown employee name "JOHNSMITH"
   ```bash
   curl -X POST http://localhost:8000/api/upload \
     -F "files=@pdf_with_johnsmith.pdf"
   ```

2. Verify transactions have `employee_id = NULL`
   ```sql
   SELECT employee_id FROM transactions WHERE session_id = '<session_id>';
   -- Expect: NULL
   ```

3. Create employee alias
   ```bash
   curl -X POST http://localhost:8000/api/aliases \
     -H "Content-Type: application/json" \
     -d '{
       "extractedName": "JOHNSMITH",
       "employeeId": "123e4567-e89b-12d3-a456-426614174000"
     }'
   ```

4. Re-upload same PDF

5. Verify transactions now have `employee_id` set
   ```sql
   SELECT employee_id FROM transactions WHERE session_id = '<new_session_id>';
   -- Expect: 123e4567-e89b-12d3-a456-426614174000
   ```

### Expected Results

- ✅ After step 2: `employee_id = NULL`, `incomplete_flag = true`
- ✅ After step 3: Alias created successfully
- ✅ After step 5: `employee_id` populated via alias, `incomplete_flag = false`

---

## Scenario 5: Process Large PDF (Performance Test)

**Objective**: Verify system can handle 10,000 transactions within 60 seconds

### Steps

1. Generate PDF with 10,000 transaction lines
   ```python
   # Script to generate large test PDF
   with open("large_statement.txt", "w") as f:
       for i in range(10000):
           f.write(f"TESTUSER\tFuel\t03/{i%28+1:02d}/2025\t{50+i%50}.{i%100:02d}\tMERCHANT{i}\tADDRESS{i}\tComplete\n")
   # Convert to PDF
   ```

2. Start timer and upload PDF
   ```bash
   START=$(date +%s)
   curl -X POST http://localhost:8000/api/upload \
     -F "files=@large_statement.pdf"
   ```

3. Poll session status until complete
   ```bash
   while true; do
     STATUS=$(curl -s http://localhost:8000/api/sessions/$SESSION_ID | jq -r '.status')
     if [ "$STATUS" != "processing" ]; then
       break
     fi
     sleep 2
   done
   END=$(date +%s)
   ELAPSED=$((END - START))
   echo "Processing took $ELAPSED seconds"
   ```

4. Verify transaction count
   ```sql
   SELECT COUNT(*) FROM transactions WHERE session_id = '<session_id>';
   -- Expect: 10000
   ```

### Expected Results

- ✅ All 10,000 transactions extracted
- ✅ Processing completes in < 60 seconds
- ✅ No memory errors or crashes
- ✅ Database contains all 10,000 records

### Performance Benchmarks

| Metric | Target | Actual |
|--------|--------|--------|
| Total time | < 60s | ___ |
| Transactions/sec | > 166 | ___ |
| Peak memory | < 500MB | ___ |

---

## Running All Scenarios

```bash
# From backend directory
pytest tests/integration/test_pdf_extraction_quickstart.py -v

# Or run specific scenario
pytest tests/integration/test_pdf_extraction_quickstart.py::test_scenario_1_complete_extraction
```

## Cleanup

```bash
# Delete test sessions
curl -X DELETE http://localhost:8000/api/sessions/$SESSION_ID
```

## Troubleshooting

**Issue**: Transactions not appearing
- Check Celery worker is running: `celery -A src.tasks worker --loglevel=info`
- Check session status: `GET /api/sessions/{id}`

**Issue**: Extraction errors
- Check logs: `tail -f backend/logs/extraction.log`
- Verify PDF is text-based (not scanned image)

**Issue**: Performance too slow
- Check database indexes exist (see data-model.md migrations)
- Verify bulk insert is being used (not individual INSERTs)
