# Tasks: Expense Reconciliation System

**Input**: Design documents from `C:\Users\rcox\OneDrive - INSULATIONS, INC\Documents\Cursor Projects\Credit-Card-Processor\specs\001-i-want-to\`
**Prerequisites**: plan.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓), quickstart.md (✓)

## Execution Flow (main)
```
1. Load plan.md from feature directory
   → ✓ Tech stack extracted: Next.js 15, Python 3.11+, FastAPI, pdfplumber, openpyxl
2. Load optional design documents:
   → ✓ data-model.md: 7 entities extracted
   → ✓ contracts/: 5 contract files found
   → ✓ research.md: 7 technology decisions loaded
   → ✓ quickstart.md: 10 test scenarios identified
3. Generate tasks by category:
   → Setup: 5 tasks
   → Tests: 15 tasks (contract + integration)
   → Core: 18 tasks (parsers, processors, generators)
   → Integration: 10 tasks (API endpoints, frontend components)
   → Polish: 7 tasks (unit tests, performance, quickstart)
4. Apply task rules:
   → Different files = [P] marked
   → Same file = sequential
   → Tests before implementation (TDD)
5. Number tasks sequentially: T001-T055
6. Generate dependency graph: ✓
7. Create parallel execution examples: ✓
8. Validate task completeness:
   → ✓ All 5 contracts have tests
   → ✓ All 7 entities have model tasks
   → ✓ All 5 endpoints implemented
9. Return: SUCCESS (55 tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Backend**: `server/` at repository root
- **Frontend**: `app/` at repository root (Next.js 15 App Router)
- **Tests**: `server/tests/` for backend, `app/__tests__/` for frontend

---

## Phase 3.1: Setup (T001-T005)

- [ ] **T001** Initialize Next.js 15 project with TypeScript and App Router in root directory
  - Run: `npx create-next-app@latest . --typescript --tailwind --app --no-src-dir`
  - Accept defaults for ESLint, import alias (@/*), Turbopack

- [ ] **T002** Install and configure Shad.CN components
  - Run: `npx shadcn-ui@latest init`
  - Install base components: `npx shadcn-ui@latest add button card form input label progress alert`
  - Verify `components/ui/` directory created

- [ ] **T003** [P] Initialize Python backend with FastAPI in `server/` directory
  - Create directory structure: `server/parsing/`, `server/processing/`, `server/generation/`, `server/api/`, `server/tests/`
  - Create `server/requirements.txt` with: fastapi, uvicorn, pdfplumber, pandas, openpyxl, pydantic, pytest, pytest-cov, pytest-asyncio
  - Create `server/api/main.py` with FastAPI app initialization and CORS middleware

- [ ] **T004** [P] Configure Python linting and formatting tools
  - Create `server/.flake8`, `server/pyproject.toml` with black/isort config
  - Add __init__.py files to all Python packages

- [ ] **T005** [P] Configure Next.js proxy to Python backend
  - Create `next.config.js` with rewrites for `/api/*` → `http://localhost:8000/api/*`
  - Set up environment variables in `.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8000`

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (T006-T010)

- [ ] **T006** [P] Contract test POST /api/upload in `server/tests/contract/test_upload_endpoint.py`
  - Test multipart/form-data upload with 2 PDF files
  - Assert response: 201 status, session_id (UUID), uploaded_files object, created_at timestamp
  - Assert error cases: 400 for missing files, 413 for oversized files

- [ ] **T007** [P] Contract test POST /api/process in `server/tests/contract/test_process_endpoint.py`
  - Test SSE stream with session_id in request body
  - Assert progress events: 0%, 10%, 25%, 50%, 75%, 90%, 95%, 100%
  - Assert each event has: progress (int), step (string), status (string)
  - Assert error cases: 400 for invalid session_id, 404 for missing session

- [ ] **T008** [P] Contract test GET /api/session/{sessionId} in `server/tests/contract/test_session_endpoint.py`
  - Test path parameter sessionId (UUID)
  - Assert response: 200 status, session object with employees array, matching_results array
  - Assert employee structure: employee_id, name, card_number, completion_status, expenses[], receipts[]
  - Assert error case: 404 for non-existent session

- [ ] **T009** [P] Contract test GET /api/reports/{sessionId} in `server/tests/contract/test_reports_endpoint.py`
  - Assert response: 200 status, excel_report object (url, file_size, row_count), csv_export object, summary stats
  - Assert summary includes: total_employees, complete_employees, total_expenses, expenses_missing_receipts, etc.
  - Assert error cases: 404 for missing session, 409 for incomplete processing

- [ ] **T010** [P] Contract test POST /api/session/{sessionId}/update in `server/tests/contract/test_update_endpoint.py`
  - Test multipart upload of new expenseReport PDF to existing session
  - Assert response: 200 status, updated: true, summary_changes object with previous/current stats
  - Assert error cases: 400 for invalid PDF, 404 for missing session, 409 for currently processing session

### Integration Tests (T011-T020)

- [ ] **T011** [P] Integration test: Full upload-to-report workflow in `server/tests/integration/test_full_workflow.py`
  - Scenario: Upload 2 PDFs → process → verify Excel + CSV generated
  - Use test fixtures: `test_credit_card_statement.pdf`, `test_expense_report.pdf`
  - Assert Excel report contains only incomplete expenses
  - Assert CSV export contains only complete employees

- [ ] **T012** [P] Integration test: PDF parsing error with partial results in `server/tests/integration/test_partial_results.py`
  - Scenario: Upload valid + corrupted PDF
  - Assert error message displayed
  - Assert partial data from valid PDF is accessible
  - Assert Excel report generated, CSV export disabled

- [ ] **T013** [P] Integration test: Session persistence in local storage in `app/__tests__/integration/test_session_persistence.test.tsx`
  - Scenario: Upload files → save session ID to localStorage → refresh page → verify session restored
  - Mock localStorage APIs
  - Assert session ID retrieved correctly
  - Assert TTL (24 hours) checked and expired sessions cleared

- [ ] **T014** [P] Integration test: Update workflow with new expense report in `server/tests/integration/test_update_workflow.py`
  - Scenario: Create session → process → upload new expense report → re-analyze
  - Assert session_id remains same (not new session)
  - Assert summary_changes shows newly complete employees
  - Assert Excel report updated with fewer incomplete items
  - Assert CSV export includes newly complete employees

- [ ] **T015** [P] Integration test: Excel Status column accuracy in `server/tests/integration/test_excel_status_column.py`
  - Scenario: Create expenses with known missing items → generate Excel
  - Assert Status column = "Missing Receipt" for expense without receipt
  - Assert Status column = "Missing GL Code" for expense without GL code
  - Assert Status column = "Missing Both" for expense missing both
  - Assert conditional formatting applied (red, yellow, orange backgrounds)

- [ ] **T016** [P] Integration test: Multiple expenses with identical amounts in `server/tests/integration/test_duplicate_amounts.py`
  - Scenario: Employee has 2 expenses both $50.00, only 1 receipt for $50.00
  - Assert both expenses marked "Missing Receipt" (ambiguous match)
  - Assert match_reason = "multiple_matches"

- [ ] **T017** [P] Integration test: pvault CSV format compliance in `server/tests/integration/test_pvault_csv.py`
  - Assert exactly 18 columns in correct order
  - Assert UTF-8 encoding
  - Assert CRLF line endings
  - Assert QUOTE_MINIMAL quoting
  - Assert amounts have 2 decimals, no $ symbols
  - Assert dates in YYYY-MM-DD format

- [ ] **T018** [P] Integration test: Employee exclusion from CSV in `server/tests/integration/test_csv_exclusion.py`
  - Scenario: Employee A has 10/10 complete, Employee B has 9/10 complete
  - Assert ALL 10 of Employee A's expenses in CSV
  - Assert NONE of Employee B's 10 expenses in CSV (even the 9 complete ones)

- [ ] **T019** [P] Integration test: Session expiration (24 hour TTL) in `app/__tests__/integration/test_session_expiration.test.tsx`
  - Mock Date.now() to simulate expired session
  - Assert expired session cleared from localStorage
  - Assert user prompted to start new session

- [ ] **T020** [P] Integration test: Progress updates in real-time in `app/__tests__/integration/test_progress_updates.test.tsx`
  - Mock SSE stream from backend
  - Assert progress bar updates from 0-100%
  - Assert step messages display correctly
  - Assert "View Results" button enabled at 100%

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Backend Models (T021-T027)

- [ ] **T021** [P] Create Employee model in `server/api/models.py`
  - Pydantic model with fields: employee_id, name, card_number, expenses, receipts, completion_status
  - Validation: employee_id pattern, card_number format (3 variants), name non-empty
  - Method: compute_completion_status() → "complete" if all expenses have receipt & GL code

- [ ] **T022** [P] Create ExpenseTransaction model in `server/api/models.py`
  - Pydantic model with 18+ fields (transaction_id, date, amount, name, vendor_invoice_number, etc.)
  - Validation: UUID format, amount > 0 with 2 decimals, date ISO 8601
  - Computed properties: has_receipt (bool), has_gl_code (bool), status (enum)

- [ ] **T023** [P] Create ReceiptRecord model in `server/api/models.py`
  - Pydantic model with fields: receipt_id, employee_id, amount, gl_code, project_code
  - Validation: amount > 0 with 2 decimals, at least one of gl_code or project_code

- [ ] **T024** [P] Create Session model in `server/api/models.py`
  - Pydantic model with fields: session_id, created_at, updated_at, pdf_paths, employees, matching_results, report_paths, processing_status, error_message
  - Validation: UUID format, created_at <= updated_at, processing_status enum

- [ ] **T025** [P] Create MatchingResult model in `server/api/models.py`
  - Pydantic model with fields: expense_transaction_id, matched_receipt_id, has_gl_code, match_reason
  - Validation: match_reason enum ("exact_match" | "no_receipt_found" | "multiple_matches")

- [ ] **T026** [P] Create ExcelReport model in `server/api/models.py`
  - Pydantic model with fields: report_id, session_id, file_path, generated_at, row_count

- [ ] **T027** [P] Create CSVExport model in `server/api/models.py`
  - Pydantic model with fields: export_id, session_id, file_path, generated_at, row_count, included_employee_ids (list)

### PDF Parsers (T028-T030)

- [ ] **T028** Implement PDF text extraction in `server/parsing/pdf_parser.py`
  - Use pdfplumber to extract text from all pages
  - Function: extract_text_from_pdf(pdf_path: str) → List[str] (list of page texts)
  - Handle multi-page PDFs, return empty list on error

- [ ] **T029** Implement Credit Card Statement parser in `server/parsing/credit_card_parser.py`
  - Regex patterns: EMPLOYEE_HEADER_PATTERN (4-6 digit ID, name, card number), TOTALS_MARKER_PATTERN, TRANSACTION_TOTALS_PATTERN
  - Function: parse_credit_card_statement(pdf_path: str) → List[Employee] with expenses
  - Extract employee info, transaction tables across multiple pages
  - Handle 16-digit, 4-4-4-4, masked card numbers

- [ ] **T030** Implement Expense Report parser in `server/parsing/expense_report_parser.py`
  - Function: parse_expense_report(pdf_path: str) → Dict[str, List[ReceiptRecord]] (keyed by employee_id)
  - Extract receipt_id, employee_id, amount, gl_code, project_code
  - Handle missing GL/project codes gracefully

### Processing Logic (T031-T033)

- [ ] **T031** Implement expense-to-receipt matcher in `server/processing/matcher.py`
  - Function: match_expenses_to_receipts(employees: List[Employee]) → List[MatchingResult]
  - Algorithm: For each expense, find receipts WHERE employee_id matches AND amount matches exactly
  - If 1 match: exact_match, set has_gl_code from receipt
  - If 0 matches: no_receipt_found
  - If 2+ matches: multiple_matches (ambiguous, cannot auto-match)

- [ ] **T032** [P] Implement validators in `server/processing/validator.py`
  - Function: validate_employee_id(employee_id: str) → bool (regex `/^[A-Z0-9_-]+$/i`)
  - Function: validate_uuid(uuid_str: str) → bool (regex 8-4-4-4-12 hex format)
  - Function: validate_card_number(card_number: str) → bool (3 format variants)

- [ ] **T033** [P] Implement completion analyzer in `server/processing/analyzer.py`
  - Function: analyze_employee_completion(employee: Employee) → str ("complete" | "incomplete")
  - Logic: "complete" IFF all expenses have has_receipt=True AND has_gl_code=True
  - Function: compute_summary_stats(session: Session) → dict (total_employees, complete_employees, etc.)

### File Generators (T034-T035)

- [ ] **T034** [P] Implement Excel report generator in `server/generation/excel_generator.py`
  - Use openpyxl to create .xlsx file
  - Columns: Employee ID, Employee Name, Card Number, Transaction Date, Transaction Amount, Transaction Name, Status
  - Only include expenses where status != "Complete"
  - Conditional formatting on Status column: "Missing Both" = red, "Missing Receipt" = yellow, "Missing GL Code" = orange
  - Header row: bold, gray background
  - Freeze top row, auto-width columns
  - Function: generate_excel_report(session: Session) → str (file path)

- [ ] **T035** [P] Implement pvault CSV generator in `server/generation/csv_generator.py`
  - Use Python csv module with QUOTE_MINIMAL
  - 18 columns: Transaction ID, Transaction Date, Transaction Amount, Transaction Name, Vendor Invoice #, Invoice Date, Header Description, Job, Phase, Cost Type, GL Account, Item Description, UM, Tax, Pay Type, Card Holder, Credit Card Number, Credit Card Vendor
  - **CRITICAL**: Only include employees where completion_status = "complete"
  - Exclude ALL expenses from incomplete employees (even their complete ones)
  - UTF-8 encoding, CRLF line endings
  - Amounts: 2 decimals, no $ symbols
  - Dates: YYYY-MM-DD format
  - Function: generate_csv_export(session: Session) → str (file path)

---

## Phase 3.4: Integration (API Endpoints + Frontend)

### Backend API Endpoints (T036-T040)

- [ ] **T036** Implement POST /api/upload endpoint in `server/api/routes.py`
  - Accept multipart/form-data with creditCardStatement and expenseReport files
  - Generate session_id (UUID)
  - Save files to `server/uploads/{session_id}/`
  - Create Session object with processing_status="pending"
  - Return 201 with session_id, uploaded_files metadata, created_at

- [ ] **T037** Implement POST /api/process endpoint in `server/api/routes.py`
  - Accept session_id in JSON body
  - Stream progress via Server-Sent Events (SSE)
  - Steps: Parse CC statement (10%), extract employees (25%), parse expense report (50%), match (75%), generate Excel (90%), generate CSV (95%), complete (100%)
  - On error: set processing_status="error", return partial results if available
  - Return SSE stream with progress, step, status fields

- [ ] **T038** Implement GET /api/session/{sessionId} endpoint in `server/api/routes.py`
  - Load session data from storage (in-memory or file-based)
  - Return session object with employees array, matching_results
  - Return 404 if session not found

- [ ] **T039** Implement GET /api/reports/{sessionId} endpoint in `server/api/routes.py`
  - Return Excel report URL, CSV export URL, summary stats
  - Return 409 if processing_status != "complete"
  - Return 404 if session not found

- [ ] **T040** Implement POST /api/session/{sessionId}/update endpoint in `server/api/routes.py`
  - Accept new expenseReport PDF via multipart/form-data
  - Keep existing Credit Card Statement
  - Re-run parsing, matching, report generation
  - Return summary_changes object: previous stats, current stats, newly_complete_employees, newly_incomplete_expenses
  - Return 409 if currently processing

### Frontend Components (T041-T048)

- [ ] **T041** [P] Create upload-form.tsx component in `app/components/upload-form.tsx`
  - Client Component with Shad.CN Button, Input, Card components
  - Two file inputs: Credit Card Statement (accept=".pdf"), Expense Report (accept=".pdf")
  - Form submission using Server Action or fetch to /api/upload
  - Display upload progress, success message with session ID

- [ ] **T042** [P] Create progress-display.tsx component in `app/components/progress-display.tsx`
  - Client Component with Shad.CN Progress bar
  - Subscribe to SSE stream from /api/process
  - Display percentage (0-100%) in progress bar
  - Display step descriptions below progress bar
  - Update in real-time as events arrive

- [ ] **T043** [P] Create results-panel.tsx component in `app/components/results-panel.tsx`
  - Server Component fetching data from /api/session/{sessionId}
  - Display employee list with completion status badges (green for complete, red for incomplete)
  - For each employee, show expense list with Status column
  - Visual indicators (icons/colors) for status: Complete, Missing Receipt, Missing GL Code, Missing Both
  - Summary statistics card at top

- [ ] **T044** [P] Create error-boundary.tsx component in `app/components/error-boundary.tsx`
  - Error boundary component for graceful error handling
  - Display specific error messages
  - Show partial results if available (via error state prop)
  - "Retry" button for upload errors

- [ ] **T045** [P] Implement session storage utilities in `app/lib/session-storage.ts`
  - Functions: saveSession(sessionId), getSession(), clearSession()
  - SessionData interface: sessionId, createdAt, expiresAt (24 hour TTL)
  - Auto-expire check on getSession()
  - Use localStorage API

- [ ] **T046** [P] Implement API client utilities in `app/lib/api-client.ts`
  - Functions: uploadPDFs(files), processSession(sessionId), getSession(sessionId), getReports(sessionId), updateReceipts(sessionId, file)
  - Use fetch API with proper error handling
  - Return typed responses based on Pydantic models

- [ ] **T047** [P] Define TypeScript types in `app/lib/types.ts`
  - Mirror Pydantic models: Employee, ExpenseTransaction, ReceiptRecord, Session, MatchingResult
  - API response types: UploadResponse, ProcessProgressEvent, SessionResponse, ReportsResponse, UpdateResponse

- [ ] **T048** Create main page in `app/page.tsx`
  - Server Component composition with Client islands
  - Step 1: Upload form (upload-form.tsx)
  - Step 2: Progress display (progress-display.tsx) - shown after upload
  - Step 3: Results panel (results-panel.tsx) - shown after processing
  - "Download Excel", "Download CSV", "Upload New Receipts" buttons
  - Session restoration on page load (check localStorage)

---

## Phase 3.5: Polish (T049-T055)

- [ ] **T049** [P] Unit tests for validators in `server/tests/unit/test_validators.py`
  - Test validate_employee_id with valid/invalid patterns
  - Test validate_uuid with valid/invalid UUIDs
  - Test validate_card_number with 16-digit, 4-4-4-4, masked formats

- [ ] **T050** [P] Unit tests for matcher logic in `server/tests/unit/test_matcher.py`
  - Test exact_match scenario (1 employee, 1 expense, 1 matching receipt)
  - Test no_receipt_found scenario (expense with no matching receipt)
  - Test multiple_matches scenario (2 receipts with same amount for same employee)
  - Test GL code detection from receipt

- [ ] **T051** [P] Unit tests for Excel generator in `server/tests/unit/test_excel_generator.py`
  - Test Excel file structure (7 columns)
  - Test only incomplete expenses included
  - Test Status column values correct
  - Test conditional formatting applied

- [ ] **T052** [P] Unit tests for CSV generator in `server/tests/unit/test_csv_generator.py`
  - Test exactly 18 columns in correct order
  - Test only complete employees included
  - Test incomplete employees fully excluded
  - Test UTF-8 encoding, CRLF line endings, QUOTE_MINIMAL

- [ ] **T053** [P] Frontend component tests in `app/__tests__/components/`
  - Test upload-form.test.tsx: file selection, submission, error handling
  - Test progress-display.test.tsx: SSE subscription, progress updates, step messages
  - Test results-panel.test.tsx: employee list rendering, status badges, summary stats
  - Use React Testing Library, mock API responses

- [ ] **T054** Performance testing in `server/tests/performance/test_processing_performance.py`
  - Benchmark PDF processing time with 50-100 transaction PDF
  - Assert < 30 seconds for typical statement
  - Benchmark Excel/CSV generation
  - Assert Excel generation < 5 seconds, CSV generation < 3 seconds

- [ ] **T055** Execute all quickstart scenarios in `specs/001-i-want-to/quickstart.md`
  - Run all 10 manual test scenarios
  - Verify Scenario 1: Upload two valid PDFs
  - Verify Scenario 2: Process PDFs with progress updates
  - Verify Scenario 3: View matching results
  - Verify Scenario 4: Excel report format (Status column, conditional formatting)
  - Verify Scenario 5: CSV export (18 columns, employee exclusion)
  - Verify Scenario 6: Upload new expense report (update workflow)
  - Verify Scenario 7: Handle corrupted PDF (error + partial results)
  - Verify Scenario 8: Multiple expenses with same amount
  - Verify Scenario 9: Session persistence across page refresh
  - Verify Scenario 10: Session expiration (24 hour TTL)
  - Record pass/fail for each scenario
  - All scenarios must pass for feature completion

---

## Dependencies

### Setup Dependencies
- T001 (Next.js init) must complete before T002 (Shad.CN)
- T003 (Python backend init) must complete before T004, T006-T010
- T005 (Next.js proxy) can run in parallel with T003, T004

### Test-to-Implementation Dependencies
- **Contract Tests (T006-T010)** must complete and FAIL before **API Endpoints (T036-T040)**
- **Integration Tests (T011-T020)** must complete and FAIL before **Core Implementation (T021-T048)**

### Core Dependencies
- **Models (T021-T027)** before **Parsers (T028-T030)** before **Processors (T031-T033)**
- **Parsers (T028-T030)** before **API Endpoints (T036-T040)**
- **Generators (T034-T035)** before **API Endpoints (T037, T039)**
- **API Endpoints (T036-T040)** before **Frontend Components (T041-T048)**

### Polish Dependencies
- **All Core (T021-T048)** must complete before **Polish (T049-T055)**
- **T055 (Quickstart)** is the final validation task

### Detailed Dependency Chain
```
T001 → T002 → T005 → T041-T048
T003 → T004 → T006-T010, T021-T027
T021-T027 (models) → T028-T030 (parsers) → T031-T033 (processors)
T028-T030, T031-T033, T034-T035 → T036-T040 (endpoints)
T036-T040 → T041-T048 (frontend components)
T011-T020 (integration tests) require T021-T048 (core) to fail first
T049-T054 (unit tests) require T021-T048 (core) to exist
T055 (quickstart) requires everything (T001-T054) complete
```

---

## Parallel Execution Examples

### Example 1: Contract Tests in Parallel
```bash
# After T003-T005 complete, launch all 5 contract tests together:
# These are independent files, no dependencies between them
Task: "Contract test POST /api/upload in server/tests/contract/test_upload_endpoint.py"
Task: "Contract test POST /api/process in server/tests/contract/test_process_endpoint.py"
Task: "Contract test GET /api/session/{sessionId} in server/tests/contract/test_session_endpoint.py"
Task: "Contract test GET /api/reports/{sessionId} in server/tests/contract/test_reports_endpoint.py"
Task: "Contract test POST /api/session/{sessionId}/update in server/tests/contract/test_update_endpoint.py"
```

### Example 2: Models in Parallel
```bash
# After contract tests written, create all 7 models together:
# Each model is independent, different classes in same file (but separable)
# Can be split into separate files if preferred for true parallelism
Task: "Create Employee model in server/api/models.py"
Task: "Create ExpenseTransaction model in server/api/models.py"
Task: "Create ReceiptRecord model in server/api/models.py"
Task: "Create Session model in server/api/models.py"
Task: "Create MatchingResult model in server/api/models.py"
Task: "Create ExcelReport model in server/api/models.py"
Task: "Create CSVExport model in server/api/models.py"
# Note: These modify same file, so mark as sequential OR split into separate files
```

### Example 3: Frontend Components in Parallel
```bash
# After API endpoints complete, build all frontend components together:
Task: "Create upload-form.tsx component in app/components/upload-form.tsx"
Task: "Create progress-display.tsx component in app/components/progress-display.tsx"
Task: "Create results-panel.tsx component in app/components/results-panel.tsx"
Task: "Create error-boundary.tsx component in app/components/error-boundary.tsx"
Task: "Implement session storage utilities in app/lib/session-storage.ts"
Task: "Implement API client utilities in app/lib/api-client.ts"
Task: "Define TypeScript types in app/lib/types.ts"
```

### Example 4: Unit Tests in Parallel
```bash
# After core implementation, run all unit tests together:
Task: "Unit tests for validators in server/tests/unit/test_validators.py"
Task: "Unit tests for matcher logic in server/tests/unit/test_matcher.py"
Task: "Unit tests for Excel generator in server/tests/unit/test_excel_generator.py"
Task: "Unit tests for CSV generator in server/tests/unit/test_csv_generator.py"
Task: "Frontend component tests in app/__tests__/components/"
```

---

## Notes

- **[P] tasks** = Different files with no dependencies, safe to parallelize
- **TDD enforcement**: All test tasks (T006-T020) MUST be completed and FAIL before starting implementation tasks (T021-T048)
- **Verify tests fail** before implementing corresponding features
- **Commit after each task** to maintain granular version history
- **Constitution compliance**: Adhere to Next.js 15 best practices, Python modular services, TDD principles

---

## Validation Checklist
*GATE: Verify before marking feature complete*

- [x] All 5 contracts have corresponding tests (T006-T010)
- [x] All 7 entities have model tasks (T021-T027)
- [x] All 5 API endpoints have implementation tasks (T036-T040)
- [x] All tests come before implementation (Phase 3.2 before 3.3)
- [x] Parallel tasks ([P]) are truly independent (different files)
- [x] Each task specifies exact file path
- [x] No task modifies same file as another [P] task (except models - note added)

---

## Task Execution Summary

**Total Tasks**: 55
**Estimated Duration**: 8-10 days (1 developer, 6-8 hours/day)

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| 3.1 Setup | T001-T005 | 2 hours |
| 3.2 Tests First (TDD) | T006-T020 | 1.5 days |
| 3.3 Core Implementation | T021-T035 | 3 days |
| 3.4 Integration | T036-T048 | 2.5 days |
| 3.5 Polish | T049-T055 | 1 day |

**Next Step**: Begin with T001 (Initialize Next.js 15 project)

**Ready for Execution**: ✅ All tasks defined, dependencies mapped, TDD enforced

---

*Generated: 2025-10-03 | Based on plan.md, data-model.md, contracts/, research.md, quickstart.md*
