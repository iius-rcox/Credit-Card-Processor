# Implementation Plan: Expense Reconciliation System

**Branch**: `001-i-want-to` | **Date**: 2025-10-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `C:\Users\rcox\OneDrive - INSULATIONS, INC\Documents\Cursor Projects\Credit-Card-Processor\specs\001-i-want-to\spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✓ Feature spec loaded successfully
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → ✓ Project Type detected: Web application (Next.js + Python backend)
   → ✓ Structure Decision: Frontend + Backend separation
3. Fill the Constitution Check section
   → ✓ Constitution v1.0.0 loaded
4. Evaluate Constitution Check section
   → ✓ PASS - No violations detected
   → ✓ Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → ✓ COMPLETE - research.md created with 7 technology decisions
6. Execute Phase 1 → contracts, data-model.md, quickstart.md
   → ✓ COMPLETE - All artifacts generated
   → ✓ data-model.md: 7 entities with full schemas
   → ✓ contracts/: 5 OpenAPI YAML contracts
   → ✓ quickstart.md: 10 test scenarios
7. Re-evaluate Constitution Check section
   → ✓ PASS - No new violations, all principles satisfied
   → ✓ Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach
   → ✓ COMPLETE - Described in Phase 2 section below
9. STOP - Ready for /tasks command
   → ✓ SUCCESS - All /plan phases complete
```

**IMPORTANT**: The /plan command STOPS at step 8. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary

This feature implements a web-based expense reconciliation system that processes two PDF documents (Credit Card Statements and Expense Software Reports), matches expenses to receipts using employee ID and amount comparison, and generates Excel reports for missing items plus CSV exports in pvault format for complete records. The system uses Next.js 15 for the frontend UI with Shad.CN components, and a Python backend service for all heavy PDF processing, regex extraction, and file generation tasks. Session data persists in browser local storage to enable returning users to upload updated receipt files and regenerate reports.

## Technical Context

**Language/Version**: TypeScript/JavaScript (Next.js 15), Python 3.11+
**Primary Dependencies**:
- Frontend: Next.js 15, React 18+, Shad.CN components, TypeScript
- Backend: Python 3.11+, PyPDF2 (PDF parsing), pandas (data processing), openpyxl (Excel generation), FastAPI (REST API)
**Storage**: Browser Local Storage (session persistence), no database
**Testing**:
- Frontend: Jest, React Testing Library, Vitest
- Backend: pytest, pytest-cov
**Target Platform**: Web browsers (Chrome, Firefox, Safari, Edge), Python backend (Linux/Windows server)
**Project Type**: Web (frontend + backend separation per constitution)
**Performance Goals**:
- PDF processing: <30 seconds for typical statement (50-100 transactions)
- Progress updates: Real-time percentage + status messages
- UI responsiveness: <200ms for user interactions
**Constraints**:
- No user authentication (single-user personal tool)
- No persistent database (local storage only)
- PDF parsing must handle multi-page tables
- Exact amount matching only (no fuzzy matching)
**Scale/Scope**:
- Single user per session
- Processing 2 PDF files per session (100-500 KB each)
- Handling 10-50 employees per statement
- 50-200 transactions per statement
- Excel reports: 10-100 rows
- CSV exports: 18 columns, variable rows

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Next.js 15 Frontend Architecture
✅ **COMPLIANT** - Plan specifies Next.js 15 with App Router, Route Handlers, Server Actions, and Shad.CN components

### Principle II: Python Backend for Heavy Processing
✅ **COMPLIANT** - All PDF parsing, regex extraction, and file generation handled by Python backend service. Frontend only handles UI and API calls

### Principle III: Local Storage for Session Management
✅ **COMPLIANT** - Session data persisted in browser local storage, no authentication or database required

### Principle IV: Python Backend Organization
✅ **COMPLIANT** - Backend organized in `/server` directory with modular structure: parsing/, processing/, generation/

### Principle V: Test-Driven Development
✅ **COMPLIANT** - TDD enforced: Contract tests written first, then implementation. Pytest for backend, Jest/RTL for frontend

### Principle VI: Next.js 15 Best Practices
✅ **COMPLIANT** - Server Components default, proper TypeScript types, error boundaries, loading states

### Principle VII: Modular Python Services
✅ **COMPLIANT** - Services organized by function with clear interfaces, type hints, docstrings

### Principle VIII: Documentation Standards
✅ **COMPLIANT** - API contracts, usage examples, test coverage in design phase

### Principle IX: Git Feature Branch Workflow
✅ **COMPLIANT** - Feature branch `001-i-want-to` created by SpecKit

**Initial Constitution Check: PASS** ✅

## Project Structure

### Documentation (this feature)
```
specs/001-i-want-to/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
│   ├── upload-pdfs.yaml        # POST /api/upload endpoint
│   ├── process-pdfs.yaml       # POST /api/process endpoint
│   ├── get-session.yaml        # GET /api/session/:id endpoint
│   ├── get-reports.yaml        # GET /api/reports/:sessionId endpoint
│   └── update-receipts.yaml    # POST /api/session/:id/update endpoint
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
server/
├── parsing/
│   ├── __init__.py
│   ├── pdf_parser.py           # PDF text extraction
│   ├── credit_card_parser.py   # Credit card statement parsing
│   └── expense_report_parser.py # Expense report parsing
├── processing/
│   ├── __init__.py
│   ├── matcher.py              # Expense-to-receipt matching logic
│   ├── validator.py            # Employee ID, UUID validation
│   └── analyzer.py             # Completion analysis
├── generation/
│   ├── __init__.py
│   ├── excel_generator.py      # Excel report generation
│   └── csv_generator.py        # pvault CSV generation
├── api/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── routes.py               # API route handlers
│   └── models.py               # Pydantic models
└── tests/
    ├── contract/               # Contract tests
    ├── integration/            # Integration tests
    └── unit/                   # Unit tests

app/
├── layout.tsx                  # Root layout (Server Component)
├── page.tsx                    # Home page with upload UI
├── api/
│   └── proxy/                  # Next.js route handlers (proxy to Python)
│       ├── upload/route.ts
│       ├── process/route.ts
│       ├── session/route.ts
│       └── reports/route.ts
├── components/
│   ├── ui/                     # Shad.CN components
│   ├── upload-form.tsx         # PDF upload form (Client Component)
│   ├── progress-display.tsx    # Progress indicator (Client Component)
│   ├── results-panel.tsx       # Results display (Server Component)
│   └── error-boundary.tsx      # Error boundary component
├── lib/
│   ├── session-storage.ts      # Local storage utilities
│   ├── api-client.ts           # API call utilities
│   └── types.ts                # TypeScript types
└── __tests__/
    ├── components/             # Component tests
    └── integration/            # Integration tests

public/
└── assets/                     # Static assets

.specify/
└── [existing spec files]
```

**Structure Decision**: Web application structure selected based on constitution requirements. Frontend uses Next.js 15 App Router with `/app` directory. Backend uses `/server` directory with modular Python services. Separation ensures frontend handles UI/routing while Python backend performs all heavy processing (PDF parsing, matching, file generation).

## Phase 0: Outline & Research

No NEEDS CLARIFICATION items remain (all resolved via /clarify command). Research focuses on technology selection and best practices.

### Research Areas

1. **Python PDF Parsing Libraries**
   - Decision: PyPDF2 or pdfplumber
   - Research: Compare text extraction accuracy, multi-page table handling, performance
   - Output: Library selection with rationale

2. **Excel Generation in Python**
   - Decision: openpyxl vs xlsxwriter
   - Research: Feature comparison, column formatting, status column styling
   - Output: Library selection with examples

3. **CSV Generation Best Practices**
   - Decision: CSV module vs pandas to_csv
   - Research: pvault format compliance, encoding (UTF-8), delimiter handling
   - Output: Implementation approach

4. **Next.js 15 File Upload Patterns**
   - Research: Server Actions vs Route Handlers for file upload
   - Research: Multipart form data handling, file size limits
   - Output: Recommended upload pattern

5. **Python FastAPI + Next.js Integration**
   - Research: CORS configuration, proxy patterns, error handling
   - Research: Progress streaming (SSE or polling)
   - Output: API integration architecture

6. **Regex Pattern Implementation**
   - Research: Python regex best practices for PDF text
   - Research: Named capture groups for employee data
   - Output: Regex pattern implementations

7. **Browser Local Storage Best Practices**
   - Research: Storage limits, data serialization, expiration strategies
   - Output: Session management design

**Output**: research.md with all decisions documented

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

### 1. Extract Entities → data-model.md

**Key Entities:**

- **Employee**
  - employee_id: string (4-6 alphanumeric + hyphens/underscores)
  - name: string
  - card_number: string (16-digit, 4-4-4-4, or masked)
  - expenses: ExpenseTransaction[]
  - receipts: ReceiptRecord[]
  - completion_status: "complete" | "incomplete"

- **ExpenseTransaction**
  - transaction_id: string (UUID)
  - employee_id: string
  - transaction_date: date
  - transaction_amount: decimal
  - transaction_name: string
  - vendor_invoice_number: string (optional)
  - has_receipt: boolean
  - has_gl_code: boolean
  - status: "Missing Receipt" | "Missing GL Code" | "Missing Both" | "Complete"

- **ReceiptRecord**
  - receipt_id: string
  - employee_id: string
  - amount: decimal
  - gl_code: string (optional)
  - project_code: string (optional)

- **Session**
  - session_id: string (UUID)
  - created_at: timestamp
  - credit_card_pdf: File
  - expense_report_pdf: File
  - employees: Employee[]
  - matching_results: MatchingResult[]
  - excel_report_path: string (optional)
  - csv_export_path: string (optional)

- **MatchingResult**
  - expense_transaction: ExpenseTransaction
  - matched_receipt: ReceiptRecord | null
  - has_gl_code: boolean

- **ExcelReport**
  - session_id: string
  - rows: ExcelRow[]
  - generated_at: timestamp

- **CSVExport (pvault format)**
  - Columns: [Transaction ID, Transaction Date, Transaction Amount, Transaction Name, Vendor Invoice #, Invoice Date, Header Description, Job, Phase, Cost Type, GL Account, Item Description, UM, Tax, Pay Type, Card Holder, Credit Card Number, Credit Card Vendor]

### 2. Generate API Contracts → /contracts/

**Endpoint: POST /api/upload**
- Request: multipart/form-data with 2 PDF files
- Response: { session_id, uploaded_files }

**Endpoint: POST /api/process**
- Request: { session_id }
- Response: { progress_percentage, current_step, status }

**Endpoint: GET /api/session/:id**
- Request: session_id path parameter
- Response: { session_id, employees, matching_results }

**Endpoint: GET /api/reports/:sessionId**
- Request: sessionId path parameter
- Response: { excel_url, csv_url, summary }

**Endpoint: POST /api/session/:id/update**
- Request: { session_id }, multipart with new expense_report PDF
- Response: { updated, new_matching_results }

### 3. Generate Contract Tests

- tests/contract/test_upload_endpoint.py
- tests/contract/test_process_endpoint.py
- tests/contract/test_session_endpoint.py
- tests/contract/test_reports_endpoint.py
- tests/contract/test_update_endpoint.py

Each test validates request/response schemas, must fail initially.

### 4. Extract Test Scenarios → quickstart.md

**Quickstart Test Scenarios:**

1. Upload two valid PDFs → verify session created
2. Process PDFs → verify progress updates stream correctly
3. View results → verify matching results accurate
4. Check Excel report → verify Status column contains correct values
5. Check CSV export → verify only complete employees included
6. Upload new expense report → verify re-analysis works
7. Handle corrupted PDF → verify error message + partial results

### 5. Update Agent Context File

Run: `.specify/scripts/powershell/update-agent-context.ps1 -AgentType cursor`

This creates/updates `.cursorrules` with:
- Tech stack: Next.js 15, Python 3.11+, FastAPI, PyPDF2, openpyxl
- Project structure reference
- Constitution compliance reminders
- Recent changes (this feature)

**Output**: data-model.md, /contracts/*, contract tests (failing), quickstart.md, .cursorrules

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy:**

The /tasks command will load `data-model.md` and `/contracts/*` to generate:

1. **Setup Tasks (T001-T005)**
   - Initialize Next.js 15 project with TypeScript
   - Install Shad.CN components
   - Setup Python backend with FastAPI
   - Install Python dependencies (PyPDF2, pandas, openpyxl, pytest)
   - Configure CORS and API proxy

2. **Contract Test Tasks (T006-T010)** [P]
   - Write contract test for POST /api/upload
   - Write contract test for POST /api/process
   - Write contract test for GET /api/session/:id
   - Write contract test for GET /api/reports/:sessionId
   - Write contract test for POST /api/session/:id/update

3. **Backend Model Tasks (T011-T015)** [P]
   - Create Employee model (server/api/models.py)
   - Create ExpenseTransaction model
   - Create ReceiptRecord model
   - Create Session model
   - Create MatchingResult model

4. **Parser Implementation (T016-T018)**
   - Implement PDF text extraction (server/parsing/pdf_parser.py)
   - Implement credit card statement parser with regex patterns
   - Implement expense report parser with regex patterns

5. **Processing Logic (T019-T021)**
   - Implement expense-to-receipt matcher (by employee_id + amount)
   - Implement validators (Employee ID, UUID patterns)
   - Implement completion analyzer

6. **File Generation (T022-T023)** [P]
   - Implement Excel report generator with Status column
   - Implement pvault CSV generator (18 columns)

7. **API Endpoints (T024-T028)**
   - Implement POST /api/upload endpoint
   - Implement POST /api/process with progress streaming
   - Implement GET /api/session/:id
   - Implement GET /api/reports/:sessionId
   - Implement POST /api/session/:id/update

8. **Frontend Components (T029-T033)** [P]
   - Create upload-form.tsx with Shad.CN components
   - Create progress-display.tsx with percentage + step messages
   - Create results-panel.tsx with employee results
   - Create error-boundary.tsx
   - Implement session storage utilities

9. **Integration Tests (T034-T038)** [P]
   - Test full upload-to-report workflow
   - Test partial PDF parsing error handling
   - Test session persistence in local storage
   - Test update workflow with new expense report
   - Test Excel Status column accuracy

10. **Quickstart Validation (T039)**
    - Execute all quickstart scenarios
    - Verify all acceptance criteria met

**Ordering Strategy:**
- Setup (T001-T005) → Contract Tests (T006-T010) → Models (T011-T015) → Parsers (T016-T018) → Processing (T019-T021) → Generation (T022-T023) → Endpoints (T024-T028) → Frontend (T029-T033) → Integration (T034-T038) → Quickstart (T039)
- [P] marks indicate parallelizable tasks (independent files)
- TDD order: All contract/integration tests before corresponding implementations

**Estimated Output**: 39 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following constitutional principles)
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

No violations detected. All constitutional principles satisfied:
- Next.js 15 + Shad.CN for frontend ✅
- Python backend for heavy processing ✅
- Local storage for sessions ✅
- `/server` directory organization ✅
- TDD enforced ✅
- Best practices followed ✅
- Modular services ✅
- Documentation standards met ✅
- Feature branch workflow ✅

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command) ✅
- [x] Phase 1: Design complete (/plan command) ✅
- [x] Phase 2: Task planning complete (/plan command - describe approach only) ✅
- [x] Phase 3: Tasks generated (/tasks command) ✅ - **55 tasks ready**
- [ ] Phase 4: Implementation complete - **NEXT STEP**
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS ✅
- [x] Post-Design Constitution Check: PASS ✅
- [x] All NEEDS CLARIFICATION resolved ✅
- [x] Complexity deviations documented (none) ✅

**Artifacts Generated**:
- [x] plan.md (this file)
- [x] research.md (7 technology decisions)
- [x] data-model.md (7 entities with schemas and relationships)
- [x] contracts/ directory (5 OpenAPI YAML contracts)
- [x] quickstart.md (10 test scenarios)
- [x] tasks.md (55 tasks generated by /tasks command) ✅

---
*Based on Constitution v1.0.0 - See `.specify/memory/constitution.md`*
