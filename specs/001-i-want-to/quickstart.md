# Quickstart Test Scenarios: Expense Reconciliation System

**Feature**: Expense Reconciliation System
**Date**: 2025-10-03
**Purpose**: Manual validation scenarios to verify acceptance criteria

---

## Prerequisites

1. **Python Backend Running**
   ```bash
   cd server
   python -m uvicorn api.main:app --reload --port 8000
   ```

2. **Next.js Frontend Running**
   ```bash
   npm run dev
   # Accessible at http://localhost:3000
   ```

3. **Test PDF Files Prepared**
   - `test_credit_card_statement.pdf` - Valid credit card statement with 10+ employees
   - `test_expense_report.pdf` - Valid expense report with matching receipts
   - `test_corrupted.pdf` - Intentionally corrupted PDF for error testing
   - `test_updated_receipts.pdf` - Updated expense report with additional receipts

---

## Scenario 1: Upload Two Valid PDFs

**Objective**: Verify session creation and file upload handling

**Steps**:
1. Navigate to `http://localhost:3000`
2. Click "Upload PDFs" button
3. Select `test_credit_card_statement.pdf` for Credit Card Statement
4. Select `test_expense_report.pdf` for Expense Report
5. Click "Upload" button

**Expected Results**:
- ✅ Upload completes without errors
- ✅ Session ID displayed on screen (UUID format)
- ✅ Success message: "Files uploaded successfully"
- ✅ Session ID stored in browser local storage (check DevTools → Application → Local Storage)
- ✅ "Process PDFs" button becomes enabled

**Verification**:
```bash
# Check backend logs for upload confirmation
# Verify files saved to server/uploads/{session_id}/
```

---

## Scenario 2: Process PDFs with Progress Updates

**Objective**: Verify PDF processing and real-time progress feedback

**Steps**:
1. From previous scenario, click "Process PDFs" button
2. Observe progress indicator

**Expected Results**:
- ✅ Progress bar appears showing 0-100% completion
- ✅ Step descriptions update in real-time:
  - "Parsing Credit Card Statement..." (0-25%)
  - "Extracting employee data..." (25-50%)
  - "Parsing Expense Report..." (50-75%)
  - "Matching expenses to receipts..." (75-90%)
  - "Generating Excel report..." (90-95%)
  - "Generating CSV export..." (95-100%)
  - "Complete" (100%)
- ✅ Processing completes with 100% progress
- ✅ "View Results" button becomes enabled

**Verification**:
```bash
# Check backend logs for each processing step
# Verify server/reports/{session_id}/report.xlsx exists
# Verify server/reports/{session_id}/export.csv exists
```

---

## Scenario 3: View Matching Results

**Objective**: Verify accuracy of expense-to-receipt matching

**Steps**:
1. From previous scenario, click "View Results" button
2. Review displayed data

**Expected Results**:
- ✅ Employee list displayed with completion status badges:
  - Green badge for "Complete" employees (100% receipted and coded)
  - Red badge for "Incomplete" employees
- ✅ For each employee, expense list shows:
  - Transaction date, amount, description
  - Status column with one of: "Complete", "Missing Receipt", "Missing GL Code", "Missing Both"
  - Visual indicators (icons or colors) matching Status values
- ✅ Summary statistics displayed:
  - Total employees
  - Complete employees count
  - Incomplete employees count
  - Total expenses
  - Breakdown by status

**Verification**:
- Manually verify at least 3 employee+amount matches are correct
- Check that employee with all receipts shows "Complete" status
- Check that employee missing receipts shows "Incomplete" status

---

## Scenario 4: Check Excel Report Format

**Objective**: Verify Excel report structure and Status column

**Steps**:
1. From results page, click "Download Excel Report" button
2. Open downloaded `report.xlsx` file in Microsoft Excel or LibreOffice

**Expected Results**:
- ✅ Excel file opens without errors
- ✅ Header row contains: Employee ID, Employee Name, Card Number, Transaction Date, Transaction Amount, Transaction Name, Status
- ✅ Header row is bold with gray background
- ✅ **Status column formatting**:
  - "Missing Both" rows have RED background (#FFC7CE)
  - "Missing Receipt" rows have YELLOW background (#FFEB9C)
  - "Missing GL Code" rows have ORANGE background (#FFD966)
- ✅ All data rows contain expenses that are NOT "Complete" (only incomplete items)
- ✅ Card numbers are masked (e.g., `**** **** **** 1234`)
- ✅ Amounts formatted as currency with 2 decimal places
- ✅ Dates formatted as YYYY-MM-DD
- ✅ Top row is frozen for scrolling
- ✅ No duplicate entries

**Verification**:
```bash
# Count rows in Excel
# Verify count matches "incomplete expenses" in summary
```

---

## Scenario 5: Check CSV Export (pvault format)

**Objective**: Verify CSV structure, column order, and employee exclusion logic

**Steps**:
1. From results page, click "Download CSV Export" button
2. Open downloaded `export.csv` file in a text editor or spreadsheet app

**Expected Results**:
- ✅ CSV file opens without errors
- ✅ **Exactly 18 columns** in this order:
  1. Transaction ID
  2. Transaction Date
  3. Transaction Amount
  4. Transaction Name
  5. Vendor Invoice #
  6. Invoice Date
  7. Header Description
  8. Job
  9. Phase
  10. Cost Type
  11. GL Account
  12. Item Description
  13. UM
  14. Tax
  15. Pay Type
  16. Card Holder
  17. Credit Card Number
  18. Credit Card Vendor
- ✅ **Only includes employees with 100% complete status** (all expenses have receipts AND GL codes)
- ✅ **Excludes all expenses from employees with even one incomplete item**
- ✅ UTF-8 encoding
- ✅ CRLF line endings
- ✅ No extra quotes around fields (unless field contains comma or newline)
- ✅ All amounts have 2 decimal places, no $ symbols
- ✅ All dates in YYYY-MM-DD format

**Verification**:
```bash
# Count CSV rows (excluding header)
# Verify matches "complete expenses" count from summary
# Verify NO rows for employees marked "Incomplete"
# Example: If Employee EMP001 has 9 complete + 1 incomplete expense,
# ALL 10 expenses from EMP001 should be ABSENT from CSV
```

---

## Scenario 6: Upload New Expense Report (Update Workflow)

**Objective**: Verify session persistence and re-analysis with updated receipts

**Steps**:
1. From results page, click "Upload New Receipts" button
2. Select `test_updated_receipts.pdf` (contains additional receipts)
3. Click "Re-analyze" button
4. Wait for processing to complete
5. View updated results

**Expected Results**:
- ✅ Session ID remains the same (not a new session)
- ✅ Processing re-runs with progress updates
- ✅ Updated matching results displayed
- ✅ Summary shows changes:
  - "Newly complete: 2 employees" (example)
  - "Remaining incomplete: 6 employees" (example)
- ✅ New Excel report generated with fewer incomplete items
- ✅ New CSV export generated with additional complete employees
- ✅ Old reports remain accessible (historical)

**Verification**:
```bash
# Check server/reports/{session_id}/ for multiple timestamped reports
# Verify updated CSV includes newly completed employees
# Verify Excel report excludes newly matched expenses
```

---

## Scenario 7: Handle Corrupted PDF

**Objective**: Verify error handling and partial results display

**Steps**:
1. Start a new session (refresh page or clear local storage)
2. Upload `test_credit_card_statement.pdf` (valid) and `test_corrupted.pdf` (invalid)
3. Click "Process PDFs"
4. Observe error handling

**Expected Results**:
- ✅ Processing stops with error message displayed
- ✅ Error message is specific: "Failed to parse Expense Report PDF"
- ✅ **Partial results ARE displayed**:
  - Expenses from Credit Card Statement shown
  - All expenses marked as "Missing Receipt" (since Expense Report failed)
  - Employee list populated from Credit Card Statement only
- ✅ "Download Excel Report" button enabled (shows all expenses as incomplete)
- ✅ "Download CSV Export" button disabled (no complete employees)
- ✅ Error banner allows user to retry by uploading a new Expense Report

**Verification**:
```bash
# Verify partial data is viewable
# Verify backend logs contain parsing error details
# Verify user can recover by uploading valid Expense Report
```

---

## Scenario 8: Edge Case - Multiple Expenses with Same Amount

**Objective**: Verify matching behavior when employee has duplicate amounts

**Setup**: Use test data where Employee EMP002 has two $50.00 transactions

**Steps**:
1. Upload test PDFs containing duplicate amounts
2. Process and view results
3. Check matching for EMP002

**Expected Results**:
- ✅ If Expense Report has only ONE $50.00 receipt for EMP002:
  - Matching is ambiguous → both $50.00 expenses marked "Missing Receipt"
  - Match reason: "multiple_matches" (cannot auto-match)
- ✅ If Expense Report has TWO $50.00 receipts for EMP002:
  - Each expense matched to one receipt
  - Both expenses show "Complete" status (or "Missing GL Code" if codes absent)

**Verification**:
- Manually inspect matching_results in session data
- Verify Status column accuracy for duplicate amounts

---

## Scenario 9: Session Persistence Across Page Refresh

**Objective**: Verify local storage session management

**Steps**:
1. Complete Scenario 1-3 (upload, process, view results)
2. Note the session ID
3. Refresh the page (F5 or Ctrl+R)
4. Observe behavior

**Expected Results**:
- ✅ Page detects existing session from local storage
- ✅ Message displayed: "Resuming session {session_id}"
- ✅ Previous results still accessible
- ✅ "Upload New Receipts" option available
- ✅ Reports downloadable without re-processing

**Verification**:
```javascript
// In browser DevTools console:
const session = localStorage.getItem('expense_session')
console.log(JSON.parse(session))
// Verify sessionId, createdAt, expiresAt fields
```

---

## Scenario 10: Session Expiration (24 Hour TTL)

**Objective**: Verify automatic session cleanup

**Steps**:
1. (Simulate) Manually edit local storage to set expiresAt to past timestamp
2. Refresh page

**Expected Results**:
- ✅ Session detected as expired
- ✅ Local storage cleared
- ✅ User prompted to start new session
- ✅ Upload form displayed (clean state)

**Simulation Command**:
```javascript
// In browser DevTools console:
const session = JSON.parse(localStorage.getItem('expense_session'))
session.expiresAt = Date.now() - 1000 // 1 second ago
localStorage.setItem('expense_session', JSON.stringify(session))
// Now refresh page
```

---

## Acceptance Criteria Validation

After completing all scenarios, verify the following acceptance criteria from the feature spec:

### ✅ Functional Requirements
- [x] FR-001: Web interface accepts two PDF files
- [x] FR-004: Employee information extracted correctly (ID, name, card number)
- [x] FR-010: Expenses matched by employee_id + amount
- [x] FR-012: Excel report generated with incomplete expenses
- [x] FR-013: CSV export has 18 columns in pvault format
- [x] FR-014: CSV includes ONLY 100% complete employees
- [x] FR-015: CSV excludes employees with any incomplete expenses
- [x] FR-016: Session persists in local storage
- [x] FR-017: New expense report can be uploaded to existing session
- [x] FR-018: Re-analysis occurs when new expense report uploaded
- [x] FR-021: Detailed progress (percentage + step descriptions)
- [x] FR-022: Errors display specific message + partial results viewable
- [x] FR-023: Excel Status column identifies issue type clearly

### ✅ Constitutional Compliance
- [x] Next.js 15 frontend with Shad.CN components
- [x] Python backend handles PDF processing
- [x] Local storage for sessions (no database)
- [x] TDD: All tests written before implementation
- [x] Modular Python services (parsing/, processing/, generation/)

---

## Performance Benchmarks

Record performance metrics during testing:

| Metric | Target | Actual | Pass/Fail |
|--------|--------|--------|-----------|
| PDF Processing Time (50 transactions) | < 30s | _____ | _____ |
| Progress Update Latency | < 500ms | _____ | _____ |
| UI Interaction Response | < 200ms | _____ | _____ |
| Excel Report Generation | < 5s | _____ | _____ |
| CSV Export Generation | < 3s | _____ | _____ |
| Page Load Time | < 2s | _____ | _____ |

---

## Sign-Off

**Tester**: _____________________
**Date**: _____________________
**All Scenarios Passed**: ☐ Yes ☐ No
**Issues Found**: _____________________
**Ready for Production**: ☐ Yes ☐ No

---

*Quickstart validation complete when all scenarios pass and acceptance criteria verified.*
