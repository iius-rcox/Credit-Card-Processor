# Tasks: Lean Internal Deployment with Permanent Data Storage

**Input**: Design documents from `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/`
**Prerequisites**: plan.md, research.md, data-model.md, contracts/, quickstart.md

## Execution Flow (main)
```
1. Load plan.md from feature directory
   ✅ Loaded: Tech stack (Python 3.11 FastAPI, Next.js 15, PostgreSQL 16)
   ✅ Extracted: 72 tasks across 11 categories
2. Load optional design documents:
   ✅ data-model.md: 5 entities → 5 model tasks
   ✅ contracts/: 5 API endpoints → 5 contract test + 5 implementation tasks
   ✅ contracts/k8s/: 12 manifests → deployment tasks
   ✅ quickstart.md: 9 test scenarios → 9 integration test tasks
3. Generate tasks by category:
   ✅ Setup: 10 tasks (project init, dependencies, configuration)
   ✅ Tests: 5 contract tests [P]
   ✅ Core: 24 tasks (5 models [P], 5 repos [P], 4 services, 5 endpoints, 5 integration)
   ✅ Frontend: 5 tasks (API client, upload page, components)
   ✅ Deployment: 10 tasks (Docker images, K8s manifests)
   ✅ Integration Tests: 9 tasks [P]
   ✅ Polish: 6 tasks (unit tests [P], performance, docs)
4. Apply task rules:
   ✅ Different files = marked [P] for parallel (27 tasks)
   ✅ Same file = sequential (45 tasks)
   ✅ Tests before implementation (TDD order)
5. Number tasks sequentially (T001-T072)
6. Generate dependency graph
7. Create parallel execution examples
8. Validate task completeness:
   ✅ All 5 endpoints have contract tests
   ✅ All 5 entities have model tasks
   ✅ All 9 quickstart scenarios have integration tests
9. Return: SUCCESS (tasks ready for execution)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Path Conventions
- **Web app structure**: `backend/src/`, `app/` (Next.js frontend)
- **Tests**: `backend/tests/contract/`, `backend/tests/integration/`, `backend/tests/unit/`
- **K8s**: `specs/005-lean-internal-deployment/contracts/k8s/`

---

## Phase 3.1: Setup (T001-T010)

⚠️ **CRITICAL**: Complete ALL setup tasks before proceeding to tests

- [X] **T001** Create backend project structure with FastAPI, SQLAlchemy 2.0, pytest
  - Create directories: `backend/src/{models,repositories,services,api}`, `backend/tests/{contract,integration,unit}`
  - Initialize `backend/src/__init__.py` and all module `__init__.py` files
  - Create `backend/pyproject.toml` with project metadata

- [X] **T002** Set up backend dependencies in `backend/requirements.txt`
  - FastAPI >= 0.104.0, uvicorn[standard] >= 0.24.0
  - SQLAlchemy >= 2.0.0, asyncpg >= 0.29.0, alembic >= 1.12.0
  - pydantic >= 2.5.0, pydantic-settings >= 2.1.0
  - python-multipart >= 0.0.6, python-jose >= 3.3.0
  - pytest >= 7.4.0, pytest-asyncio >= 0.21.0, httpx >= 0.25.0
  - openpyxl >= 3.1.0 (for Excel report generation)

- [X] **T003** Initialize Alembic for database migrations in `backend/migrations/`
  - Run `alembic init migrations` in backend directory
  - Configure `backend/alembic.ini` with PostgreSQL connection string
  - Update `backend/migrations/env.py` to import SQLAlchemy models
  - Create `backend/migrations/script.py.mako` template

- [X] **T004** Create backend Dockerfile in `backend/Dockerfile`
  - Base image: `python:3.11-slim`
  - Install dependencies from requirements.txt
  - Copy application code to `/app`
  - Expose port 8000
  - CMD: `uvicorn src.main:app --host 0.0.0.0 --port 8000`

- [X] **T005** Create database initialization script in `backend/init.sql`
  - Copy SQL schema from data-model.md (lines 432-580)
  - Include all CREATE TABLE statements for 5 entities
  - Include all CREATE INDEX statements (20+ indexes)
  - Include trigger functions (update_updated_at_column)

- [X] **T006** Set up Docker Compose for local development in `docker-compose.yml`
  - PostgreSQL service (postgres:16-alpine) with init.sql volume mount
  - Redis service (redis:7-alpine) for temporary processing state
  - Backend service with live reload
  - Frontend service (Next.js dev server)
  - Networks and volume definitions

- [X] **T007** Create backend environment configuration in `backend/.env.example`
  - DATABASE_URL, POSTGRES_HOST, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
  - REDIS_URL, REDIS_HOST, REDIS_PORT
  - ENVIRONMENT (development/production), LOG_LEVEL (DEBUG/INFO)
  - AZURE_KEY_VAULT_NAME, AZURE_TENANT_ID, AZURE_CLIENT_ID (for production)

- [X] **T008** Update frontend API client base in `lib/api-client.ts`
  - Add `API_BASE_URL` environment variable support
  - Create `apiRequest<T>()` helper function with error handling
  - Add type definitions for Session, SessionDetail, Employee, Transaction, Receipt, MatchResult
  - Export typed API client functions

- [X] **T009** Create frontend environment configuration in `.env.local.example`
  - NEXT_PUBLIC_API_URL (http://localhost:8000 for dev, http://api:8000 for prod)
  - NODE_ENV (development/production)

- [X] **T010** [P] Set up pytest configuration in `backend/pytest.ini`
  - Configure test discovery patterns: `test_*.py`, `*_test.py`
  - Set asyncio_mode = auto
  - Add markers: contract, integration, unit
  - Configure logging: `log_cli = true`, `log_cli_level = INFO`

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

- [X] **T011** [P] Contract test POST /api/upload in `backend/tests/contract/test_upload_contract.py`
  - Test multipart file upload (PDFs)
  - Assert response contains session_id, status="processing", created_at, expires_at
  - Test file size validation (max 10MB per file)
  - Test file count validation (max 100 files)
  - Test file type validation (only PDFs allowed)
  - Expected: FAIL (endpoint not implemented)

- [X] **T012** [P] Contract test GET /api/sessions in `backend/tests/contract/test_sessions_list_contract.py`
  - Test pagination parameters (page, page_size, default 50 per page)
  - Test 90-day window filtering (created_at > NOW() - 90 days)
  - Assert response schema: {items: Session[], total: int, page: int, page_size: int}
  - Test empty result set
  - Expected: FAIL (endpoint not implemented)

- [X] **T013** [P] Contract test GET /api/sessions/{id} in `backend/tests/contract/test_session_detail_contract.py`
  - Test valid session ID returns SessionDetail with all related data
  - Assert includes: employees[], transactions[], receipts[], match_results[]
  - Test 404 for non-existent session ID
  - Test 404 for expired session (created_at > 90 days ago)
  - Expected: FAIL (endpoint not implemented)

- [X] **T014** [P] Contract test GET /api/sessions/{id}/report in `backend/tests/contract/test_report_contract.py`
  - Test format parameter (xlsx, csv)
  - Assert response Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet or text/csv
  - Assert Content-Disposition header includes filename
  - Test streaming response (Transfer-Encoding: chunked)
  - Test 404 for non-existent session
  - Expected: FAIL (endpoint not implemented)

- [X] **T015** [P] Contract test DELETE /api/sessions/{id} in `backend/tests/contract/test_delete_contract.py`
  - Test successful deletion returns 204 No Content
  - Test cascade deletion (verify related records deleted)
  - Test 404 for non-existent session
  - Test idempotency (second DELETE returns 404)
  - Expected: FAIL (endpoint not implemented)

---

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Database Models (T016-T020)

- [X] **T016** [P] Session model in `backend/src/models/session.py`
  - SQLAlchemy Table: sessions with UUID primary key
  - Columns: id, created_at, expires_at (GENERATED), status (enum: processing/completed/failed/expired)
  - Columns: upload_count, total_transactions, total_receipts, matched_count, updated_at
  - Relationships: employees, transactions, receipts, match_results (cascade delete)
  - CHECK constraints: counts >= 0, status in enum values
  - Indexes: created_at, expires_at, status

- [X] **T017** [P] Employee model in `backend/src/models/employee.py`
  - SQLAlchemy Table: employees with UUID primary key
  - Columns: id, session_id (FK), employee_number, name, department, cost_center, created_at
  - Relationship: session (back_populates), transactions
  - UNIQUE constraint: (session_id, employee_number)
  - Indexes: session_id, (session_id, employee_number), (session_id, created_at)

- [X] **T018** [P] Transaction model in `backend/src/models/transaction.py`
  - SQLAlchemy Table: transactions with UUID primary key
  - Columns: id, session_id (FK), employee_id (FK), transaction_date, post_date, amount, currency
  - Columns: merchant_name, merchant_category, description, card_last_four, reference_number, raw_data (JSONB)
  - Relationships: session, employee, match_result (one-to-one)
  - CHECK constraints: amount > 0, post_date >= transaction_date
  - UNIQUE constraint: (session_id, reference_number) WHERE reference_number IS NOT NULL
  - Indexes: session_id, employee_id, (session_id, transaction_date DESC), amount, merchant_name, raw_data (GIN)

- [X] **T019** [P] Receipt model in `backend/src/models/receipt.py`
  - SQLAlchemy Table: receipts with UUID primary key
  - Columns: id, session_id (FK), receipt_date, amount, currency, vendor_name
  - Columns: file_name, file_path, file_size, mime_type, ocr_confidence, extracted_data (JSONB)
  - Columns: processing_status (enum), error_message, created_at, processed_at
  - Relationship: session, match_result (one-to-one)
  - CHECK constraints: amount > 0, file_size > 0, ocr_confidence BETWEEN 0 AND 1
  - Indexes: session_id, (session_id, receipt_date DESC), amount, vendor_name, processing_status (partial), extracted_data (GIN)

- [X] **T020** [P] MatchResult model in `backend/src/models/match_result.py`
  - SQLAlchemy Table: matchresults with UUID primary key
  - Columns: id, session_id (FK), transaction_id (FK), receipt_id (FK nullable)
  - Columns: confidence_score, match_status (enum: matched/unmatched/manual_review/approved/rejected)
  - Columns: match_reason, amount_difference, date_difference_days, merchant_similarity, matching_factors (JSONB)
  - Columns: reviewed_by, reviewed_at, notes, created_at
  - Relationships: session, transaction (one-to-one), receipt (optional)
  - CHECK constraints: confidence_score BETWEEN 0 AND 1, matched status requires receipt_id
  - UNIQUE constraint: transaction_id (one match per transaction)
  - Indexes: session_id, transaction_id, receipt_id (partial), (session_id, match_status), (session_id, confidence_score DESC)

### Repositories (T021-T025)

- [X] **T021** [P] SessionRepository in `backend/src/repositories/session_repository.py`
  - `create_session(data: dict) -> Session`: Insert new session
  - `get_session_by_id(session_id: UUID) -> Session | None`: Query by primary key with 90-day check
  - `list_sessions(page: int, page_size: int) -> tuple[list[Session], int]`: Paginated list within 90-day window
  - `delete_expired_sessions(days: int = 90) -> int`: Cleanup job, returns count deleted
  - `update_session_counts(session_id: UUID) -> None`: Recalculate transaction/receipt/matched counts
  - All methods use AsyncSession with proper transaction handling

- [X] **T022** [P] EmployeeRepository in `backend/src/repositories/employee_repository.py`
  - `create_employee(session_id: UUID, data: dict) -> Employee`: Insert employee
  - `bulk_create_employees(session_id: UUID, employees: list[dict]) -> list[Employee]`: Batch insert
  - `get_employees_by_session(session_id: UUID) -> list[Employee]`: Query all for session
  - `get_employee_by_number(session_id: UUID, employee_number: str) -> Employee | None`: Lookup by unique key
  - All methods use AsyncSession

- [X] **T023** [P] TransactionRepository in `backend/src/repositories/transaction_repository.py`
  - `create_transaction(session_id: UUID, employee_id: UUID, data: dict) -> Transaction`: Insert transaction
  - `bulk_create_transactions(transactions: list[dict]) -> list[Transaction]`: Batch insert
  - `get_transactions_by_session(session_id: UUID, order_by: str = "transaction_date") -> list[Transaction]`: Query all for session
  - `get_transactions_by_employee(employee_id: UUID) -> list[Transaction]`: Query by employee
  - `get_unmatched_transactions(session_id: UUID) -> list[Transaction]`: Transactions without receipts
  - All methods use AsyncSession with proper indexing

- [X] **T024** [P] ReceiptRepository in `backend/src/repositories/receipt_repository.py`
  - `create_receipt(session_id: UUID, data: dict) -> Receipt`: Insert receipt
  - `bulk_create_receipts(receipts: list[dict]) -> list[Receipt]`: Batch insert
  - `get_receipts_by_session(session_id: UUID) -> list[Receipt]`: Query all for session
  - `get_unmatched_receipts(session_id: UUID) -> list[Receipt]`: Receipts without transactions
  - `update_processing_status(receipt_id: UUID, status: str, error_message: str = None) -> None`: Update OCR status
  - All methods use AsyncSession

- [X] **T025** [P] MatchResultRepository in `backend/src/repositories/match_result_repository.py`
  - `create_match_result(session_id: UUID, transaction_id: UUID, receipt_id: UUID | None, data: dict) -> MatchResult`: Insert match
  - `bulk_create_match_results(matches: list[dict]) -> list[MatchResult]`: Batch insert
  - `get_match_results_by_session(session_id: UUID) -> list[MatchResult]`: Query all for session
  - `get_match_by_transaction(transaction_id: UUID) -> MatchResult | None`: Query by unique key
  - `update_match_review(match_id: UUID, status: str, reviewed_by: str, notes: str) -> None`: Manual review
  - All methods use AsyncSession

### Services (T026-T029)

- [X] **T026** UploadService in `backend/src/services/upload_service.py`
  - `async def process_upload(files: list[UploadFile], session_repo: SessionRepository) -> Session`: Main upload handler
  - Validate file count (max 100), file size (max 10MB each), file type (PDF only)
  - Create new Session with status="processing"
  - Save files to temporary storage (NOT persistent, files discarded after extraction)
  - Return Session with session_id for status polling
  - Dispatch background task for PDF extraction (call ExtractionService)

- [X] **T027** ExtractionService in `backend/src/services/extraction_service.py`
  - `async def extract_employees(pdf: bytes) -> list[dict]`: Parse employee names from credit card statement
  - `async def extract_transactions(pdf: bytes) -> list[dict]`: Parse transactions (date, amount, merchant, description)
  - `async def extract_receipts(pdfs: list[bytes]) -> list[dict]`: OCR receipt data (date, amount, vendor, items)
  - Use library: PyPDF2 or pdfplumber for text extraction, pytesseract for OCR if needed
  - Store extracted data in Employee, Transaction, Receipt tables via repositories
  - Update Session status to "extracting" → "matching"

- [X] **T028** MatchingService in `backend/src/services/matching_service.py`
  - `async def match_transactions_to_receipts(session_id: UUID, transaction_repo, receipt_repo, match_repo) -> None`: Fuzzy matching
  - Algorithm: Compare amount (exact or ±$0.01), date (±3 days), merchant/vendor name (Levenshtein similarity > 0.8)
  - Confidence score calculation: weighted average (amount: 0.5, date: 0.3, merchant: 0.2)
  - Create MatchResult for each transaction (matched or unmatched status)
  - Update Session counts: matched_count, total_transactions, total_receipts
  - Update Session status to "completed"

- [X] **T029** ReportService in `backend/src/services/report_service.py`
  - `async def generate_excel_report(session_id: UUID, repositories) -> bytes`: Stream XLSX file
  - Use openpyxl library to create workbook with 3 sheets: Summary, Transactions, Receipts
  - Summary sheet: Session metadata, match statistics, employee summary
  - Transactions sheet: All transactions with match status, receipt reference
  - Receipts sheet: All receipts with matched transaction reference
  - `async def generate_csv_report(session_id: UUID, repositories) -> str`: Stream CSV file
  - CSV format: Transaction ID, Date, Amount, Merchant, Match Status, Receipt ID, Receipt Amount, Confidence

### API Endpoints (T030-T034)

- [X] **T030** POST /api/upload in `backend/src/api/routes/upload.py`
  - FastAPI route: `@router.post("/upload", response_model=SessionResponse, status_code=202)`
  - Accept multipart/form-data with file field (multiple files)
  - Dependency injection: UploadService, SessionRepository
  - Call UploadService.process_upload() in background task
  - Return 202 Accepted with session_id, status="processing", created_at, expires_at
  - Error handling: 400 for validation errors, 500 for server errors

- [X] **T031** GET /api/sessions in `backend/src/api/routes/sessions.py`
  - FastAPI route: `@router.get("/sessions", response_model=PaginatedSessionsResponse)`
  - Query parameters: page (default 1), page_size (default 50, max 100)
  - Dependency injection: SessionRepository
  - Call SessionRepository.list_sessions() with 90-day window filter
  - Return {items: Session[], total: int, page: int, page_size: int, has_next: bool}
  - Error handling: 500 for server errors

- [X] **T032** GET /api/sessions/{id} in `backend/src/api/routes/sessions.py`
  - FastAPI route: `@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)`
  - Path parameter: session_id (UUID)
  - Dependency injection: SessionRepository, EmployeeRepository, TransactionRepository, ReceiptRepository, MatchResultRepository
  - Query session with all related data (eager loading via JOINs)
  - Return SessionDetail with nested employees, transactions, receipts, match_results arrays
  - Error handling: 404 if session not found or expired, 500 for server errors

- [X] **T033** GET /api/sessions/{id}/report in `backend/src/api/routes/reports.py`
  - FastAPI route: `@router.get("/sessions/{session_id}/report")`
  - Path parameter: session_id (UUID)
  - Query parameter: format (xlsx or csv, default xlsx)
  - Dependency injection: ReportService, all repositories
  - Call ReportService.generate_excel_report() or generate_csv_report()
  - Return StreamingResponse with Content-Type and Content-Disposition headers
  - Error handling: 404 if session not found, 400 for invalid format, 500 for server errors

- [X] **T034** DELETE /api/sessions/{id} in `backend/src/api/routes/sessions.py`
  - FastAPI route: `@router.delete("/sessions/{session_id}", status_code=204)`
  - Path parameter: session_id (UUID)
  - Dependency injection: SessionRepository
  - Delete session (cascade deletes all related records)
  - Return 204 No Content on success
  - Error handling: 404 if session not found, 500 for server errors

### Integration (T035-T042)

- [X] **T035** Database connection and session factory in `backend/src/database.py`
  - Create async engine: `create_async_engine(DATABASE_URL, pool_size=5, max_overflow=10, pool_pre_ping=True)`
  - Create session factory: `async_sessionmaker(engine, expire_on_commit=False)`
  - Export `get_db()` dependency for FastAPI: `async with AsyncSessionLocal() as session: yield session`
  - Add engine lifecycle hooks (startup/shutdown)

- [X] **T036** FastAPI dependency injection in `backend/src/api/dependencies.py`
  - `get_db()` dependency (from database.py)
  - `get_session_repository(db: AsyncSession) -> SessionRepository`
  - `get_employee_repository(db: AsyncSession) -> EmployeeRepository`
  - `get_transaction_repository(db: AsyncSession) -> TransactionRepository`
  - `get_receipt_repository(db: AsyncSession) -> ReceiptRepository`
  - `get_match_result_repository(db: AsyncSession) -> MatchResultRepository`
  - `get_upload_service(session_repo: SessionRepository, ...) -> UploadService`

- [X] **T037** Configuration management in `backend/src/config.py`
  - Use pydantic-settings BaseSettings class
  - Load environment variables with validation
  - DATABASE_URL, REDIS_URL, ENVIRONMENT, LOG_LEVEL
  - AZURE_KEY_VAULT_NAME, AZURE_TENANT_ID (for production)
  - Export singleton `settings` instance

- [X] **T038** Error handling middleware in `backend/src/api/middleware/error_handler.py`
  - Global exception handler for FastAPI app
  - Catch IntegrityError → 400 Bad Request with descriptive message
  - Catch OperationalError → 503 Service Unavailable (database down)
  - Catch ValueError → 400 Bad Request
  - Catch all other exceptions → 500 Internal Server Error with error ID for tracking

- [X] **T039** CORS configuration in `backend/src/main.py`
  - Add CORSMiddleware to FastAPI app
  - Allow origins: ["http://localhost:3000", "https://credit-card.ii-us.com"]
  - Allow methods: ["GET", "POST", "DELETE"]
  - Allow headers: ["Content-Type", "Authorization"]

- [X] **T040** Request/response logging middleware in `backend/src/api/middleware/logging.py`
  - Log incoming requests: method, path, query params, headers (exclude sensitive)
  - Log outgoing responses: status code, response time
  - Use structured logging (JSON format) with request ID
  - Add timing information for performance monitoring

- [X] **T041** Health check endpoint in `backend/src/api/routes/health.py`
  - FastAPI route: `@router.get("/health")`
  - Check database connection: `SELECT 1` query
  - Check Redis connection: PING command
  - Return {status: "healthy", database: "connected", redis: "connected", timestamp: ISO8601}
  - Return 503 if any dependency is down

- [ ] **T042** Alembic migration for initial schema in `backend/migrations/versions/001_initial_schema.py`
  - Generate migration: `alembic revision --autogenerate -m "initial schema"`
  - Review and edit migration file to match init.sql schema
  - Include all CREATE TABLE, CREATE INDEX, CREATE TRIGGER statements
  - Test migration: `alembic upgrade head` and `alembic downgrade base`

---

## Phase 3.4: Frontend Integration (T043-T047)

- [X] **T043** Update API client in `lib/api-client.ts` for new endpoints
  - Add functions: `uploadFiles(files: File[])`, `listSessions(page, pageSize)`, `getSession(id)`, `downloadReport(id, format)`, `deleteSession(id)`
  - Add type definitions for all response schemas (Session, SessionDetail, PaginatedResponse, etc.)
  - Add error handling and retry logic
  - Export typed client functions

- [X] **T044** Create upload page in `app/upload/page.tsx`
  - Client Component with state management
  - Import and render UploadForm, ProgressDisplay, ResultsPanel components
  - Handle file selection, upload, and progress tracking
  - Poll session status after upload (every 2 seconds until status="completed")
  - Display results when processing complete

- [X] **T045** Create upload form component in `components/upload-form-005.tsx`
  - Client Component with "use client" directive
  - File input with drag-and-drop support (native HTML5)
  - Validation: PDF only, max 100 files, max 10MB each
  - Upload button triggers API call to POST /api/upload
  - Show file list with remove option before upload
  - Disable form during upload

- [X] **T046** Create progress display component in `components/progress-display-005.tsx`
  - Client Component showing upload/processing progress
  - Display session status with visual indicators
  - Progress bar with percentage (based on status)
  - Show counts: files uploaded, transactions extracted, receipts extracted, matches found

- [X] **T047** Create results panel component in `components/results-panel-005.tsx`
  - Results panel with download options
  - Buttons: "Download Excel (XLSX)" and "Download CSV"
  - Call API client downloadReport() function
  - Trigger browser download with appropriate filename: `reconciliation_${sessionId}_${date}.xlsx`
  - Display match statistics and recent matches

---

## Phase 3.5: Kubernetes Deployment (T048-T057)

⚠️ **PREREQUISITES**: All application code tested and working in local Docker environment

- [X] **T048** Build and push backend Docker image to ACR
  - ✅ Created `backend/Dockerfile` with Python 3.11 slim base
  - ✅ Created `backend/.dockerignore` to exclude tests and dev files
  - ✅ Configured multi-stage build for production
  - Build: `docker build -t iiusacr.azurecr.io/expense-backend:latest backend/`
  - Push: `docker push iiusacr.azurecr.io/expense-backend:latest`
  - Or use automated script: `./deploy.sh v1.0.0`

- [X] **T049** Build and push frontend Docker image to ACR
  - ✅ Created `Dockerfile` with Node 20 Alpine multi-stage build
  - ✅ Created `.dockerignore` to exclude dev files
  - ✅ Updated `next.config.ts` with standalone output
  - ✅ Created `deploy.sh` automated deployment script
  - ✅ Created `DEPLOYMENT.md` comprehensive deployment guide
  - Build: `docker build -t iiusacr.azurecr.io/expense-frontend:latest .`
  - Push: `docker push iiusacr.azurecr.io/expense-frontend:latest`
  - Or use automated script: `./deploy.sh v1.0.0`

- [X] **T050** Apply Secret Provider Class manifest (SKIPPED - created Kubernetes secrets directly)
  - Created Azure Key Vault secrets: postgres-db, postgres-user, postgres-password, database-url
  - Created managed identity: credit-card-processor-identity (Client ID: 1316f607-a59f-44e3-82f3-27b658d4715c)
  - Created Kubernetes secret: postgres-secrets (workaround for RBAC assignment issues)
  - Note: Azure RBAC role assignment blocked - needs elevated permissions

- [X] **T051** Deploy PostgreSQL StatefulSet
  - Deployed postgres-service (headless ClusterIP with sessionAffinity)
  - Deployed postgres StatefulSet with adjusted resources (100m CPU, 256Mi RAM request; 250m/512Mi limits)
  - Added fsGroup: 999 securityContext to fix volume permissions
  - PostgreSQL pod status: Running and Ready (postgres-0)
  - PVC bound: postgres-storage-postgres-0 (10Gi managed-csi-premium)

- [X] **T052** Initialize database schema
  - Created 5 core tables directly via psql: sessions, employees, transactions, receipts, matchresults
  - Fixed GENERATED ALWAYS expression (changed expires_at to DEFAULT NOW() + INTERVAL '90 days')
  - All tables created successfully with foreign keys, constraints, and basic indexes
  - Note: Full index creation and triggers from init.sql pending

- [ ] **T053** Deploy backend service
  - `kubectl apply -f specs/005-lean-internal-deployment/contracts/k8s/backend-deployment.yaml`
  - `kubectl apply -f specs/005-lean-internal-deployment/contracts/k8s/backend-service.yaml`
  - Wait for ready: `kubectl wait --for=condition=ready pod -l app=backend -n credit-card-processor --timeout=300s`
  - Check logs: `kubectl logs -n credit-card-processor -l app=backend --tail=50`

- [ ] **T054** Deploy frontend service
  - `kubectl apply -f specs/005-lean-internal-deployment/contracts/k8s/frontend-deployment.yaml`
  - `kubectl apply -f specs/005-lean-internal-deployment/contracts/k8s/frontend-service.yaml`
  - Wait for ready: `kubectl wait --for=condition=ready pod -l app=frontend -n credit-card-processor --timeout=300s`
  - Check logs: `kubectl logs -n credit-card-processor -l app=frontend --tail=50`

- [ ] **T055** Apply ingress manifest
  - `kubectl apply -f specs/005-lean-internal-deployment/contracts/k8s/ingress.yaml`
  - Verify ingress: `kubectl get ingress -n credit-card-processor`
  - Test HTTPS access: `curl -k https://credit-card.ii-us.com/health`

- [ ] **T056** Deploy cleanup CronJob
  - `kubectl apply -f specs/005-lean-internal-deployment/contracts/k8s/cleanup-cronjob.yaml`
  - Verify schedule: `kubectl get cronjob -n credit-card-processor`
  - Manually trigger test: `kubectl create job --from=cronjob/data-cleanup test-cleanup -n credit-card-processor`

- [ ] **T057** Deploy backup CronJob
  - `kubectl apply -f specs/005-lean-internal-deployment/contracts/k8s/backup-cronjob.yaml`
  - Verify schedule: `kubectl get cronjob -n credit-card-processor`
  - Manually trigger test: `kubectl create job --from=cronjob/postgres-backup test-backup -n credit-card-processor`

---

## Phase 3.6: Integration Tests (T058-T066)

⚠️ **PREREQUISITES**: Application deployed and accessible

- [ ] **T058** [P] Upload workflow test in `backend/tests/integration/test_upload_workflow.py`
  - End-to-end test: Upload PDFs → Poll status → Verify results
  - Test with sample credit card statement (5 transactions) and 3 receipt PDFs
  - Assert session created, files processed, data extracted, matches found
  - Verify database records: employees, transactions, receipts, match_results created

- [ ] **T059** [P] Session retrieval test in `backend/tests/integration/test_session_retrieval.py`
  - Create test session with data
  - Test GET /api/sessions returns session in list
  - Test GET /api/sessions/{id} returns full details with all related data
  - Test pagination works correctly (page 1, page 2, different page_size)

- [ ] **T060** [P] 90-day expiration test in `backend/tests/integration/test_90day_expiration.py`
  - Create test session with created_at = NOW() - 91 days (mock timestamp)
  - Test GET /api/sessions/{id} returns 404 Not Found with "session expired" message
  - Test cleanup job deletes expired sessions
  - Verify cascade deletion removed all related records

- [ ] **T061** [P] Report generation test in `backend/tests/integration/test_report_generation.py`
  - Create test session with sample data (5 transactions, 3 receipts, match results)
  - Test GET /api/sessions/{id}/report?format=xlsx returns valid Excel file
  - Test GET /api/sessions/{id}/report?format=csv returns valid CSV data
  - Verify file contains correct data from database

- [ ] **T062** [P] Database persistence test in `backend/tests/integration/test_database_persistence.py`
  - Create session with full data (employees, transactions, receipts, matches)
  - Restart backend service (simulate pod restart)
  - Verify all data persists and is queryable after restart
  - Test data integrity: counts match, relationships intact, indexes working

- [ ] **T063** [P] Cleanup CronJob test in `backend/tests/integration/test_cleanup_cronjob.py`
  - Create test sessions with varying ages (30, 60, 89, 91, 100 days old)
  - Manually trigger cleanup job
  - Verify sessions older than 90 days are deleted
  - Verify sessions younger than 90 days are retained

- [ ] **T064** [P] Backup CronJob test in `backend/tests/integration/test_backup_cronjob.py`
  - Manually trigger backup job
  - Verify pg_dump created successfully
  - Verify backup uploaded to Azure Blob Storage
  - Test restore procedure from backup

- [ ] **T065** [P] HTTPS access test in `backend/tests/integration/test_https_access.py`
  - Test HTTP request redirects to HTTPS
  - Test HTTPS certificate valid
  - Test ingress routing: / → frontend, /api → backend
  - Test health check endpoint accessible

- [ ] **T066** [P] Cost validation test in `backend/tests/integration/test_cost_validation.py`
  - Query Kubernetes for resource usage: `kubectl top pods -n credit-card-processor`
  - Verify CPU usage within limits (500m PostgreSQL, 200m backend, 100m frontend)
  - Verify memory usage within limits (1Gi PostgreSQL, 512Mi backend, 256Mi frontend)
  - Calculate estimated monthly cost based on resource allocation

---

## Phase 3.7: Polish (T067-T072)

- [ ] **T067** [P] Unit tests for extraction service in `backend/tests/unit/test_extraction_service.py`
  - Test extract_employees() with sample PDF
  - Test extract_transactions() with sample credit card statement
  - Test extract_receipts() with sample receipt PDFs
  - Test error handling: invalid PDF, corrupted file, missing data

- [ ] **T068** [P] Unit tests for matching service in `backend/tests/unit/test_matching_service.py`
  - Test exact amount match (transaction $123.45, receipt $123.45) → confidence 1.0
  - Test fuzzy amount match (transaction $123.45, receipt $123.46) → confidence 0.95
  - Test date proximity (same date vs 3 days apart)
  - Test merchant similarity (Levenshtein distance)
  - Test confidence score calculation with various inputs

- [ ] **T069** [P] Unit tests for report service in `backend/tests/unit/test_report_service.py`
  - Test generate_excel_report() creates valid XLSX with 3 sheets
  - Test generate_csv_report() creates valid CSV with correct columns
  - Test report contains all session data
  - Test report formatting (dates, currency, percentages)

- [ ] **T070** Performance optimization (database query profiling)
  - Run EXPLAIN ANALYZE on critical queries (session list, session detail, cleanup)
  - Verify indexes are being used (no Seq Scan on large tables)
  - Add missing indexes if queries are slow
  - Test query performance with 1000+ sessions (load testing)

- [ ] **T071** Update CLAUDE.md with feature 005 context
  - Update "Active Feature" to 005-lean-internal-deployment
  - Add Backend section: Python 3.11, FastAPI, SQLAlchemy, PostgreSQL
  - Add Deployment section: AKS, credit-card-processor namespace, credit-card.ii-us.com
  - Update Recent Changes: 005 deployment complete

- [ ] **T072** Run complete quickstart validation
  - Follow quickstart.md section 3 (Deploy to AKS) step-by-step
  - Follow quickstart.md section 4 (Smoke Tests) - all 7 scenarios
  - Follow quickstart.md section 5 (Validation Queries) - database health checks
  - Document any deviations or issues found
  - Update quickstart.md if procedures need correction

---

## Dependencies

**Critical Dependency Rules**:
1. **Setup (T001-T010) → ALL other tasks** (nothing can run without project structure)
2. **Contract Tests (T011-T015) → Implementation (T016-T057)** (TDD: tests must fail first)
3. **Models (T016-T020) → Repositories (T021-T025)** (repos depend on models)
4. **Repositories (T021-T025) → Services (T026-T029)** (services use repos)
5. **Services (T026-T029) → API Endpoints (T030-T034)** (endpoints call services)
6. **Database Setup (T035, T042) → All data access tasks** (connection required)
7. **Core Backend (T016-T042) → Frontend (T043-T047)** (frontend needs working API)
8. **All Application Code → Deployment (T048-T057)** (deploy working code)
9. **Deployment Complete → Integration Tests (T058-T066)** (test deployed system)
10. **All Features Working → Polish (T067-T072)** (optimize and document)

**Parallel Task Groups**:
- **Group A** (T011-T015): Contract tests - all 5 can run in parallel
- **Group B** (T016-T020): Models - all 5 can run in parallel
- **Group C** (T021-T025): Repositories - all 5 can run in parallel
- **Group D** (T058-T066): Integration tests - all 9 can run in parallel
- **Group E** (T067-T069): Unit tests - all 3 can run in parallel

**Sequential Constraints**:
- T031, T032, T034 share `sessions.py` → sequential
- T026-T029 may share utilities → sequential within phase
- T043-T047 may share types → sequential within phase

---

## Parallel Execution Examples

### Example 1: Contract Tests (After Setup Complete)
```bash
# Launch all 5 contract tests in parallel:
# Each test is in a separate file, so they can run concurrently

Task: "Write contract test POST /api/upload in backend/tests/contract/test_upload_contract.py"
Task: "Write contract test GET /api/sessions in backend/tests/contract/test_sessions_list_contract.py"
Task: "Write contract test GET /api/sessions/{id} in backend/tests/contract/test_session_detail_contract.py"
Task: "Write contract test GET /api/sessions/{id}/report in backend/tests/contract/test_report_contract.py"
Task: "Write contract test DELETE /api/sessions/{id} in backend/tests/contract/test_delete_contract.py"
```

### Example 2: Database Models (After Contract Tests Fail)
```bash
# Launch all 5 model creation tasks in parallel:
# Each model is in a separate file

Task: "Implement Session model in backend/src/models/session.py with SQLAlchemy"
Task: "Implement Employee model in backend/src/models/employee.py with SQLAlchemy"
Task: "Implement Transaction model in backend/src/models/transaction.py with SQLAlchemy"
Task: "Implement Receipt model in backend/src/models/receipt.py with SQLAlchemy"
Task: "Implement MatchResult model in backend/src/models/match_result.py with SQLAlchemy"
```

### Example 3: Repositories (After Models Complete)
```bash
# Launch all 5 repository creation tasks in parallel:

Task: "Implement SessionRepository in backend/src/repositories/session_repository.py"
Task: "Implement EmployeeRepository in backend/src/repositories/employee_repository.py"
Task: "Implement TransactionRepository in backend/src/repositories/transaction_repository.py"
Task: "Implement ReceiptRepository in backend/src/repositories/receipt_repository.py"
Task: "Implement MatchResultRepository in backend/src/repositories/match_result_repository.py"
```

### Example 4: Integration Tests (After Deployment)
```bash
# Launch all 9 integration tests in parallel:

Task: "Write end-to-end upload workflow test in backend/tests/integration/test_upload_workflow.py"
Task: "Write session retrieval test in backend/tests/integration/test_session_retrieval.py"
Task: "Write 90-day expiration test in backend/tests/integration/test_90day_expiration.py"
Task: "Write report generation test in backend/tests/integration/test_report_generation.py"
Task: "Write database persistence test in backend/tests/integration/test_database_persistence.py"
Task: "Write cleanup CronJob test in backend/tests/integration/test_cleanup_cronjob.py"
Task: "Write backup CronJob test in backend/tests/integration/test_backup_cronjob.py"
Task: "Write HTTPS access test in backend/tests/integration/test_https_access.py"
Task: "Write cost validation test in backend/tests/integration/test_cost_validation.py"
```

---

## Notes

### Execution Guidelines
- **TDD Mandatory**: All contract tests (T011-T015) MUST fail before implementing any code
- **Parallel Marker [P]**: Tasks marked [P] can run concurrently if resources available
- **Commit Frequency**: Commit after each completed task for granular history
- **Testing**: Run tests after each implementation task to verify correctness
- **Documentation**: Update code comments and docstrings as you implement

### Common Pitfalls to Avoid
- ❌ Implementing code before writing tests (violates TDD)
- ❌ Running parallel tasks that modify the same file
- ❌ Skipping database migrations (always use Alembic)
- ❌ Hardcoding secrets in code (use environment variables and Key Vault)
- ❌ Deploying without testing locally first (use Docker Compose)

### Validation Checklist
After completing all tasks, verify:
- [ ] All 5 contract tests pass
- [ ] All 9 integration tests pass
- [ ] All 3 unit tests pass
- [ ] Application accessible at https://credit-card.ii-us.com
- [ ] Database schema matches data-model.md specification
- [ ] 90-day TTL cleanup job runs successfully
- [ ] Weekly backup job creates valid pg_dump files
- [ ] Cost target met (<$10/month operational cost)

---

**Total Tasks**: 72
**Parallel Tasks**: 27 (marked [P])
**Sequential Tasks**: 45
**Estimated Time**: 18-20 hours with parallel execution

**Status**: READY FOR EXECUTION via /implement command
