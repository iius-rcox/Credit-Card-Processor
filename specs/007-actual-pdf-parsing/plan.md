# Implementation Plan: Actual PDF Parsing

**Branch**: `007-actual-pdf-parsing` | **Date**: 2025-10-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-actual-pdf-parsing/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → ✓ Loaded from C:/Users/rcox/.../specs/007-actual-pdf-parsing/spec.md
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Project Type: web (frontend + backend detected)
   → Structure Decision: Web application with FastAPI backend + Next.js frontend
3. Fill the Constitution Check section
   → Constitution template is empty/placeholder - skipping formal checks
4. Evaluate Constitution Check section
   → No violations (constitution is template-only)
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → Generate research on PDF parsing, regex patterns, employee alias management
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, CLAUDE.md
   → Design API contracts for extraction endpoints
   → Update data models for aliases and incomplete flags
7. Re-evaluate Constitution Check section
   → No new violations
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 9. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Replace placeholder PDF extraction logic in `extraction_service.py` with actual regex-based parsing that extracts employee names, dates, amounts, merchant details, and expense types from text-based credit card statement PDFs. Includes employee alias mapping for name resolution and robust error handling for incomplete extractions.

## Technical Context
**Language/Version**: Python 3.11 (backend), TypeScript/Next.js 15 (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy, PyPDF2/pdfplumber for text extraction, PostgreSQL
**Storage**: PostgreSQL (existing tables: transactions, employees, receipts; new: employee_aliases)
**Testing**: pytest, pytest-asyncio, httpx for API tests
**Target Platform**: Linux server (Docker), web browser clients
**Project Type**: web - FastAPI backend + Next.js frontend
**Performance Goals**: Process up to 10,000 transactions per PDF without performance degradation
**Constraints**: Text-based PDFs only (no OCR), must preserve partial extractions with flags
**Scale/Scope**: Single feature enhancement to existing reconciliation system

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: The constitution file is a template placeholder with no specific principles defined for this project. Proceeding with standard best practices:
- ✓ Test-first approach (contract tests before implementation)
- ✓ Clear separation: models → services → API
- ✓ Minimal complexity (regex-based parsing, not ML)
- ✓ Observable (preserve raw_data for debugging)

**Status**: PASS (no constitutional violations - template only)

## Project Structure

### Documentation (this feature)
```
specs/007-actual-pdf-parsing/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
backend/
├── src/
│   ├── models/
│   │   ├── employee_alias.py          # NEW: Employee alias mapping model
│   │   └── transaction.py             # MODIFY: Add incomplete_flag, is_credit fields
│   ├── services/
│   │   ├── extraction_service.py      # MODIFY: Replace placeholders with real parsing
│   │   └── alias_service.py           # NEW: Manage employee alias CRUD operations
│   ├── api/
│   │   ├── routes/
│   │   │   └── aliases.py             # NEW: Alias management endpoints
│   │   └── schemas.py                 # MODIFY: Add alias DTOs
│   └── repositories/
│       └── alias_repository.py        # NEW: Employee alias data access
└── tests/
    ├── contract/
    │   ├── test_extraction_contract.py      # NEW: Extraction API contract tests
    │   └── test_alias_contract.py           # NEW: Alias API contract tests
    ├── integration/
    │   ├── test_extraction_integration.py   # NEW: End-to-end extraction tests
    │   └── test_alias_integration.py        # NEW: Alias mapping workflow tests
    └── unit/
        ├── test_extraction_patterns.py      # NEW: Regex pattern unit tests
        └── test_alias_service.py            # NEW: Alias service unit tests

frontend/
├── src/
│   ├── components/
│   │   └── AliasManager.tsx           # NEW: UI for creating employee aliases
│   ├── pages/
│   │   └── reconciliation/
│   │       └── aliases.tsx            # NEW: Alias management page
│   └── services/
│       └── aliasService.ts            # NEW: Frontend alias API client
└── tests/
    └── components/
        └── AliasManager.test.tsx      # NEW: Alias UI component tests
```

**Structure Decision**: Web application structure (Option 2 from template). Backend handles PDF parsing and data persistence; frontend provides alias management UI. Modifies existing extraction_service.py and adds new alias management subsystem.

## Phase 0: Outline & Research

### Research Tasks

1. **PDF Text Extraction Libraries**
   - **Decision**: Use PyPDF2 or pdfplumber for text extraction
   - **Rationale**: Both are mature, well-documented Python libraries for extracting text from PDFs
   - **Alternatives**: pypdf (newer but less mature), PDFMiner (more complex API)
   - **Recommendation**: pdfplumber (better handling of table structures, simpler API)

2. **Regex Patterns for Transaction Parsing**
   - **Decision**: Design regex patterns for tabular credit card statement format
   - **Key patterns needed**:
     - Employee name: `^([A-Z]+(?:\s+[A-Z]+)*)`  (all-caps names at line start)
     - Date: `(\d{1,2}/\d{1,2}/\d{4})`  (MM/DD/YYYY format)
     - Amount: `([-]?\$?\d{1,3}(?:,\d{3})*(?:\.\d{2})?)`  (with commas, optional negative)
     - Merchant: Capture text between date and amount, trim whitespace
     - Expense type: Pattern depends on PDF layout (may be column-based)
   - **Rationale**: Regex provides fast, deterministic parsing without ML overhead
   - **Alternatives**: NLP/ML models (rejected: out of scope per spec clarifications)

3. **Employee Alias Data Model**
   - **Decision**: New table `employee_aliases` with columns:
     - `id` (UUID, primary key)
     - `extracted_name` (VARCHAR, unique) - name as it appears in PDF
     - `employee_id` (UUID, foreign key to employees table)
     - `created_at` (timestamp)
   - **Rationale**: Simple lookup table for name normalization
   - **Alternatives**: Fuzzy matching algorithm (rejected: spec clarified exact alias mapping)

4. **Incomplete Transaction Flagging**
   - **Decision**: Add `incomplete_flag` (boolean) and `is_credit` (boolean) to transactions table
   - **Rationale**: Allows filtering/reporting on data quality, distinguishes credits/refunds
   - **Alternatives**: Separate "incomplete_transactions" table (rejected: adds complexity)

5. **Multi-Page PDF Handling**
   - **Decision**: Iterate through all PDF pages, concatenate text, apply regex globally
   - **Rationale**: pdfplumber provides page iteration, simple to aggregate
   - **Edge case**: Page breaks mid-transaction - handle with lookahead/lookbehind patterns

6. **Performance for 10,000 Transactions**
   - **Decision**: Batch database inserts (use `bulk_insert_mappings`)
   - **Rationale**: Reduces database round-trips, maintains atomicity
   - **Target**: < 30 seconds for 10k transaction PDF

**Output**: research.md (to be generated)

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

### Data Model Updates (`data-model.md`)

**New Entity: EmployeeAlias**
```python
class EmployeeAlias:
    id: UUID
    extracted_name: str  # Unique, as appears in PDF
    employee_id: UUID    # FK to employees.id
    created_at: datetime
```

**Modified Entity: Transaction**
```python
class Transaction:
    # Existing fields...
    incomplete_flag: bool = False     # NEW: True when required fields missing
    is_credit: bool = False           # NEW: True when amount < 0
    # amount field now allows negative values
```

### API Contracts (`contracts/`)

**1. POST /api/aliases** - Create employee alias
```yaml
Request:
  extractedName: string  # Name from PDF
  employeeId: string     # UUID of existing employee

Response 201:
  id: string
  extractedName: string
  employeeId: string
  createdAt: string

Errors:
  400: Alias already exists
  404: Employee not found
```

**2. GET /api/aliases** - List all aliases
```yaml
Response 200:
  aliases: [
    { id, extractedName, employeeId, employee: { name, email } }
  ]
```

**3. DELETE /api/aliases/:id** - Remove alias
```yaml
Response 204: No content
Errors:
  404: Alias not found
```

**4. Modify POST /api/upload** - Enhanced extraction response
```yaml
Response 202 (unchanged structure, enhanced data):
  sessionId: string
  status: "processing"
  # Backend now populates transactions with real data from PDF
  # Sets incomplete_flag=true when fields missing
  # Sets is_credit=true when amount negative
```

### Contract Tests

1. `test_extraction_contract.py`:
   - Assert transaction has all expected fields (including new flags)
   - Assert amount can be negative
   - Assert raw_data preserved

2. `test_alias_contract.py`:
   - Assert POST /aliases creates alias with valid employee_id
   - Assert GET /aliases returns array of alias objects
   - Assert DELETE /aliases/:id removes alias
   - Assert duplicate extracted_name returns 400

### Integration Test Scenarios (`quickstart.md`)

**Scenario 1: Extract transactions with complete data**
1. Upload PDF with 50 complete transactions
2. Assert all 50 transactions created
3. Assert no incomplete_flag set
4. Assert employee names match existing records or use aliases

**Scenario 2: Handle incomplete transactions**
1. Upload PDF with malformed transaction (missing date)
2. Assert transaction created with null date
3. Assert incomplete_flag=true

**Scenario 3: Handle credit/refund**
1. Upload PDF with negative amount transaction
2. Assert transaction.amount < 0
3. Assert is_credit=true

**Scenario 4: Create and use employee alias**
1. Upload PDF with unknown employee name "JOHNSMITH"
2. POST /aliases with extractedName="JOHNSMITH", employeeId={existing}
3. Re-upload same PDF
4. Assert transactions now linked to correct employee_id

**Scenario 5: Process large PDF**
1. Upload PDF with 10,000 transactions
2. Assert all 10,000 extracted within 60 seconds
3. Assert no memory errors

### Agent File Update

Run: `.specify/scripts/bash/update-agent-context.sh claude`
- Add: PyPDF2/pdfplumber, regex patterns for transaction parsing
- Add: Employee alias table and API endpoints
- Update recent changes: "007-actual-pdf-parsing: Real PDF extraction with regex patterns"

**Output**: data-model.md, /contracts/*, contract tests (failing), quickstart.md, CLAUDE.md updated

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
1. Load `.specify/templates/tasks-template.md` as base
2. Generate tasks from Phase 1 design docs:
   - Database migration: Add employee_aliases table, modify transactions table
   - Contract tests for extraction and alias endpoints (must fail initially)
   - Implement ExtractionService regex parsing logic
   - Implement AliasService CRUD operations
   - Implement alias API endpoints
   - Implement frontend AliasManager component
   - Integration tests for extraction workflows
   - Update existing upload flow to use new extraction logic

**Ordering Strategy** (TDD + dependency order):
1. [P] Database migration (add tables/columns)
2. [P] Write extraction contract tests (will fail)
3. [P] Write alias contract tests (will fail)
4. Implement EmployeeAlias model
5. Implement AliasRepository
6. Implement AliasService
7. Make alias contract tests pass
8. Update extraction_service.py with real PDF parsing
9. Make extraction contract tests pass
10. [P] Write integration tests (will fail)
11. Implement alias API endpoints
12. Implement frontend AliasManager component
13. Make integration tests pass
14. Performance test with 10k transaction PDF
15. [P] Update CLAUDE.md

**Estimated Output**: 18-22 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)
**Phase 4**: Implementation (execute tasks.md following TDD principles)
**Phase 5**: Validation (run tests, execute quickstart.md scenarios, performance validation)

## Complexity Tracking
*No constitutional violations detected - constitution is template-only*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS (template-only)
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (via /clarify session)
- [x] Complexity deviations documented (N/A)

---
*Based on Feature Spec 007-actual-pdf-parsing - See `spec.md`*
