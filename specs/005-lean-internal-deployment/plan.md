# Implementation Plan: Lean Internal Deployment with Permanent Data Storage

**Branch**: `005-lean-internal-deployment` | **Date**: 2025-10-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/spec.md`

## Execution Flow (/plan command scope)
```
✅ 1. Load feature spec from Input path
✅ 2. Fill Technical Context (all clarifications resolved)
✅ 3. Fill Constitution Check section
✅ 4. Evaluate Constitution Check section
✅ 5. Execute Phase 0 → research.md (COMPLETE)
✅ 6. Execute Phase 1 → contracts, data-model.md, quickstart.md (COMPLETE)
✅ 7. Re-evaluate Constitution Check section
✅ 8. Plan Phase 2 → Task generation approach documented
✅ 9. STOP - Ready for /tasks command
```

**STATUS**: All planning phases complete. Ready for /tasks command to generate tasks.md

## Summary

Deploy the Expense Reconciliation System (Next.js 15 + FastAPI) to existing Azure Kubernetes Service (AKS) cluster with PostgreSQL StatefulSet for 90-day staging data retention. The system replaces the existing credit-card application at credit-card.ii-us.com and serves as middleware staging to pVault, maintaining reconciliation data for 90 days before automatic cleanup. Target operational cost: <$10/month.

## Technical Context

**Language/Version**:
- **Backend**: Python 3.11+ with FastAPI 0.104+
- **Frontend**: TypeScript 5.x with Next.js 15.5.4 (App Router)
- **Database**: PostgreSQL 16

**Primary Dependencies**:
- **Backend**: FastAPI, SQLAlchemy 2.0+ (async), asyncpg, Pydantic, python-multipart
- **Frontend**: React 19, shadcn/ui, Radix UI, Tailwind CSS 4.x
- **Infrastructure**: Kubernetes (AKS), Azure Key Vault, Azure Container Registry

**Storage**:
- **Database**: PostgreSQL StatefulSet with Azure Disk Premium LRS (10Gi PVC)
- **Backups**: Azure Blob Storage (weekly pg_dump, 30-day retention)
- **Cache**: Redis (existing service at redis.credit-card-processor.svc.cluster.local:6379)

**Testing**:
- **Backend**: pytest with async test support
- **Frontend**: Jest with React Testing Library
- **Integration**: Contract tests for API endpoints, E2E scenarios from quickstart.md

**Target Platform**:
- **Deployment**: Azure Kubernetes Service (dev-aks cluster, rg_prod)
- **Namespace**: credit-card-processor
- **Ingress**: webapprouting.kubernetes.azure.com with HTTPS (credit-card.ii-us.com)
- **Access**: Internal company intranet only (no public internet)

**Project Type**: Web application (frontend + backend + database + Kubernetes manifests)

**Performance Goals**:
- Session upload processing: <30 seconds for 10 files (5MB each)
- Database query latency: <50ms for session retrieval
- Report generation: <5 seconds streaming response
- Health check response: <100ms

**Constraints**:
- **Cost**: Total monthly operational cost <$10 (target ~$2-3)
- **Retention**: 90-day automatic data cleanup (middleware staging)
- **Scale**: Single-replica deployment for 1-2 concurrent users
- **Resources**: PostgreSQL (500m CPU, 1Gi RAM), Backend (200m CPU, 512Mi RAM), Frontend (100m CPU, 256Mi RAM)

**Scale/Scope**:
- **Users**: 1-2 internal employees
- **Usage Pattern**: Monthly reconciliation (not daily)
- **Data Volume**: ~10MB per session, ~12 sessions/year, 90-day retention = ~30MB active data
- **API Endpoints**: 5 (upload, list sessions, session detail, report download, manual delete)
- **Database Tables**: 5 core entities (Session, Employee, Transaction, Receipt, MatchResult)

## Constitution Check

**Status**: ✅ No constitution violations detected (constitution template not yet customized for this project)

The project follows standard web application architecture patterns:
- Clear separation of concerns (frontend, backend, database)
- Database-first approach with SQLAlchemy ORM
- API-driven communication between frontend and backend
- Infrastructure as code via Kubernetes manifests

**Re-evaluation after Phase 1 Design**: ✅ No new violations introduced

## Project Structure

### Documentation (this feature)
```
specs/005-lean-internal-deployment/
├── spec.md              # Feature specification with 8 clarifications resolved
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (deployment architecture, tech decisions)
├── data-model.md        # Phase 1 output (PostgreSQL schema, 5 entities)
├── quickstart.md        # Phase 1 output (deployment validation guide)
└── contracts/           # Phase 1 output (API spec, Kubernetes manifests)
    ├── api-openapi-ref.md           # OpenAPI 3.0 endpoint reference
    └── k8s/                         # Kubernetes deployment manifests
        ├── README.md                # Deployment order and instructions
        ├── secret-provider.yaml     # Azure Key Vault CSI driver config
        ├── postgres-statefulset.yaml
        ├── postgres-service.yaml
        ├── backend-deployment.yaml
        ├── backend-service.yaml
        ├── frontend-deployment.yaml
        ├── frontend-service.yaml
        ├── ingress.yaml
        ├── cleanup-cronjob.yaml     # 90-day data cleanup job
        └── backup-cronjob.yaml      # Weekly PostgreSQL backup
```

### Source Code (repository root)

**Web Application Structure** (frontend + backend detected):

```
# Backend (FastAPI + SQLAlchemy)
backend/
├── src/
│   ├── models/                # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── session.py        # Session entity with 90-day TTL
│   │   ├── employee.py       # Employee entity
│   │   ├── transaction.py    # Transaction entity
│   │   ├── receipt.py        # Receipt entity
│   │   └── match_result.py   # MatchResult entity
│   ├── repositories/          # Repository pattern for data access
│   │   ├── __init__.py
│   │   ├── session_repository.py
│   │   ├── employee_repository.py
│   │   ├── transaction_repository.py
│   │   ├── receipt_repository.py
│   │   └── match_result_repository.py
│   ├── services/              # Business logic services
│   │   ├── __init__.py
│   │   ├── upload_service.py      # PDF upload and processing
│   │   ├── extraction_service.py  # PDF data extraction
│   │   ├── matching_service.py    # Transaction-receipt matching
│   │   └── report_service.py      # Excel/CSV report generation
│   ├── api/                   # FastAPI endpoints
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── upload.py     # POST /api/upload
│   │   │   ├── sessions.py   # GET /api/sessions, GET /api/sessions/{id}
│   │   │   └── reports.py    # GET /api/sessions/{id}/report
│   │   └── dependencies.py   # FastAPI dependency injection
│   ├── database.py            # SQLAlchemy async engine and session factory
│   ├── config.py              # Configuration from environment/Key Vault
│   └── main.py                # FastAPI app initialization
├── tests/
│   ├── contract/              # Contract tests for API endpoints
│   │   ├── test_upload_contract.py
│   │   ├── test_sessions_list_contract.py
│   │   ├── test_session_detail_contract.py
│   │   ├── test_report_contract.py
│   │   └── test_delete_contract.py
│   ├── integration/           # Integration tests from quickstart scenarios
│   │   ├── test_upload_workflow.py
│   │   ├── test_session_retrieval.py
│   │   ├── test_90day_expiration.py
│   │   └── test_report_generation.py
│   └── unit/                  # Unit tests for services
│       ├── test_extraction_service.py
│       ├── test_matching_service.py
│       └── test_report_service.py
├── migrations/                # Alembic database migrations
│   ├── versions/
│   └── alembic.ini
├── Dockerfile
├── requirements.txt
└── pyproject.toml

# Frontend (Next.js 15 App Router)
frontend/  or  app/
├── app/                       # Next.js 15 App Router
│   ├── layout.tsx            # Root layout (existing)
│   ├── page.tsx              # Main dashboard (existing)
│   ├── upload/
│   │   └── page.tsx          # Upload workflow page
│   ├── sessions/
│   │   ├── page.tsx          # Session list page (existing)
│   │   └── [sessionId]/
│   │       ├── page.tsx      # Session detail page (existing)
│   │       └── report/
│   │           └── page.tsx  # Report download page
│   └── api/                   # Next.js API routes (proxies to backend)
│       └── [...proxy].ts     # Proxy all /api/* to backend
├── components/
│   ├── ui/                    # shadcn/ui components (existing)
│   ├── upload-form.tsx       # File upload component
│   ├── progress-display.tsx  # Processing progress
│   ├── results-panel.tsx     # Reconciliation results table
│   └── session-list.tsx      # Session list component
├── lib/
│   ├── api-client.ts         # Backend API client
│   ├── utils.ts              # Utility functions
│   └── theme-detection.ts    # Theme utilities (existing)
├── tests/                     # Frontend tests (existing structure)
├── Dockerfile
├── package.json
└── next.config.js

# Kubernetes Deployment (already documented in contracts/k8s/)
k8s/  or  deployment/          # Optional: Copy of K8s manifests for deployment
└── [See contracts/k8s/ for complete manifests]

# Database Migrations
database/
└── migrations/                # SQL migration scripts (if not using Alembic)
    ├── 001_initial_schema.sql
    └── 002_add_indexes.sql
```

**Structure Decision**:
This is a **web application** with separate frontend and backend services. The frontend directory may be named `app/` (as detected in the repository) or `frontend/` - both are valid Next.js conventions. The backend will be created in a new `backend/` directory. Kubernetes manifests are defined in `specs/005-lean-internal-deployment/contracts/k8s/` and will be copied to the repository root for deployment automation.

## Phase 0: Outline & Research ✅

**Status**: COMPLETE - research.md generated with 6 major research sections

**Research Areas Covered**:
1. ✅ PostgreSQL StatefulSet on AKS (decision: Premium LRS, 500m CPU, 1Gi RAM)
2. ✅ Azure Key Vault + AKS Workload Identity (decision: CSI driver with SecretProviderClass)
3. ✅ SQLAlchemy Async with FastAPI (decision: pool_size=5, asyncpg driver)
4. ✅ Next.js 15 App Router + FastAPI (decision: hybrid Server/Client Components)
5. ✅ webapprouting Ingress (AKS) (decision: Application Gateway Ingress Controller)
6. ✅ 90-Day TTL Data Lifecycle (decision: CronJob cleanup + weekly backups)

**Output**: `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/research.md` (1,390 lines)

**Key Decisions Documented**:
- Database: PostgreSQL StatefulSet with 10Gi Premium LRS storage ($2/month)
- Secrets: Azure Key Vault with Workload Identity federation
- Connection Pool: 5 persistent + 10 overflow connections
- Ingress: webapprouting.kubernetes.azure.com matching n8n pattern
- Backup: Weekly pg_dump to Azure Blob Storage (30-day retention)
- Cleanup: Daily CronJob deleting sessions older than 90 days

## Phase 1: Design & Contracts ✅

**Status**: COMPLETE - All Phase 1 artifacts generated

### 1. Data Model ✅

**Output**: `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/data-model.md` (795 lines)

**Entities Extracted** (5 core + 1 ephemeral):
1. **Session** - Primary entity with 90-day TTL (UUID, created_at, expires_at, status, counters)
2. **Employee** - Employee master data (UUID, session_id FK, employee_number, name)
3. **Transaction** - Credit card transactions (UUID, session_id FK, employee_id FK, date, amount, merchant)
4. **Receipt** - Uploaded receipt data (UUID, session_id FK, date, amount, vendor, file metadata)
5. **MatchResult** - Transaction-receipt matching outcome (UUID, session_id FK, transaction_id FK, receipt_id FK, confidence_score)
6. **ProcessingState** (ephemeral) - Temporary status in Redis (not persisted to database)

**Database Schema Highlights**:
- PostgreSQL-specific features: GENERATED ALWAYS AS for expires_at, JSONB for metadata
- Cascade deletion: All child entities deleted when Session expires
- Indexes: 20+ indexes for efficient querying (created_at, expires_at, session_id, etc.)
- Validation rules: CHECK constraints, UNIQUE constraints, FK constraints
- Migration scripts: Complete CREATE TABLE statements with triggers

### 2. API Contracts ✅

**Output**: `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/contracts/api-openapi-ref.md`

**Endpoints Defined** (5 endpoints):
1. **POST /api/upload** - Multipart PDF upload (max 100 files, 10MB each)
2. **GET /api/sessions** - List sessions with pagination (90-day window)
3. **GET /api/sessions/{id}** - Session details with all related data
4. **GET /api/sessions/{id}/report** - Stream Excel/CSV report
5. **DELETE /api/sessions/{id}** - Manual session deletion

**Request/Response Schemas**:
- Session, SessionDetail, Employee, Transaction, Receipt, MatchResult, Pagination, Error
- All responses include proper HTTP status codes (200, 400, 404, 500)
- Streaming support for large report downloads

### 3. Kubernetes Manifests ✅

**Output**: `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/contracts/k8s/` (12 files)

**Manifests Created**:
- ✅ `secret-provider.yaml` - Azure Key Vault CSI driver configuration
- ✅ `postgres-statefulset.yaml` - PostgreSQL 16 with persistent volume
- ✅ `postgres-service.yaml` - Headless service for StatefulSet
- ✅ `backend-deployment.yaml` - FastAPI deployment (1 replica)
- ✅ `backend-service.yaml` - ClusterIP service for backend
- ✅ `frontend-deployment.yaml` - Next.js deployment (1 replica)
- ✅ `frontend-service.yaml` - ClusterIP service for frontend
- ✅ `ingress.yaml` - HTTPS ingress with TLS termination
- ✅ `cleanup-cronjob.yaml` - Daily 90-day data cleanup (2 AM UTC)
- ✅ `backup-cronjob.yaml` - Weekly PostgreSQL backup (Sunday 1 AM UTC)
- ✅ `README.md` - Deployment order and troubleshooting guide

### 4. Quickstart Scenarios ✅

**Output**: `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/quickstart.md` (1,236 lines)

**Test Scenarios Documented**:
1. ✅ Local development setup (Docker Compose)
2. ✅ AKS deployment procedure (12-step deployment)
3. ✅ Smoke tests (manual validation, 7 scenarios)
4. ✅ Database validation queries (health checks, TTL verification)
5. ✅ API validation (curl commands for all endpoints)
6. ✅ Log analysis (error detection, performance monitoring)
7. ✅ Rollback procedures (database restore, deployment rollback)
8. ✅ Cost verification (resource utilization, storage usage)
9. ✅ Troubleshooting guide (pod failures, database errors, ingress issues)

**Integration Test Scenarios** (from User Stories):
- Upload workflow test (PDF upload → processing → results)
- Session retrieval test (query by ID, 90-day window)
- 90-day expiration test (automatic cleanup verification)
- Report generation test (Excel/CSV download)
- HTTPS access test (ingress routing, TLS termination)
- Cost validation test (resource limits, storage usage)
- Backup restore test (pg_dump recovery)

### 5. Agent Context Update ✅

**Status**: NOT APPLICABLE - Claude Code uses CLAUDE.md in repository root (existing file)

**Current Agent Context**: `/Users/rogercox/Credit-Card-Processor/CLAUDE.md` exists and documents:
- Project: Expense Reconciliation System
- Active Feature: 004-change-the-dark (Dark Mode Toggle - previous feature)
- Tech Stack: TypeScript 5.x, React 19, Next.js 15.5.4, shadcn/ui, Tailwind CSS 4.x

**Action Required**: After /tasks command completes, update CLAUDE.md to reflect feature 005 as active.

## Phase 2: Task Planning Approach

**This section describes what the /tasks command will do - NOT executed during /plan**

### Task Generation Strategy

**Input Documents**:
- `data-model.md` - 5 entities → 5 model creation tasks [P]
- `contracts/api-openapi-ref.md` - 5 endpoints → 5 contract test tasks [P] + 5 implementation tasks
- `contracts/k8s/*.yaml` - 12 manifests → validation and deployment tasks
- `quickstart.md` - 9 test scenarios → 9 integration test tasks

**Task Categories**:

1. **Setup Tasks** (T001-T010):
   - Create backend project structure (FastAPI, SQLAlchemy, pytest)
   - Initialize Alembic for database migrations
   - Configure Azure Key Vault integration
   - Set up backend Dockerfile and requirements.txt
   - Update frontend API client for new endpoints
   - Configure environment variables (.env files)
   - Create database initialization script (init.sql)
   - Set up Docker Compose for local development
   - Configure Kubernetes namespace and RBAC
   - Create ACR push/pull secrets

2. **Test Tasks - Contract Tests** [P] (T011-T015):
   - T011 [P] Contract test POST /api/upload in `backend/tests/contract/test_upload_contract.py`
   - T012 [P] Contract test GET /api/sessions in `backend/tests/contract/test_sessions_list_contract.py`
   - T013 [P] Contract test GET /api/sessions/{id} in `backend/tests/contract/test_session_detail_contract.py`
   - T014 [P] Contract test GET /api/sessions/{id}/report in `backend/tests/contract/test_report_contract.py`
   - T015 [P] Contract test DELETE /api/sessions/{id} in `backend/tests/contract/test_delete_contract.py`

3. **Core Tasks - Database Models** [P] (T016-T020):
   - T016 [P] Session model in `backend/src/models/session.py`
   - T017 [P] Employee model in `backend/src/models/employee.py`
   - T018 [P] Transaction model in `backend/src/models/transaction.py`
   - T019 [P] Receipt model in `backend/src/models/receipt.py`
   - T020 [P] MatchResult model in `backend/src/models/match_result.py`

4. **Core Tasks - Repositories** [P] (T021-T025):
   - T021 [P] SessionRepository in `backend/src/repositories/session_repository.py`
   - T022 [P] EmployeeRepository in `backend/src/repositories/employee_repository.py`
   - T023 [P] TransactionRepository in `backend/src/repositories/transaction_repository.py`
   - T024 [P] ReceiptRepository in `backend/src/repositories/receipt_repository.py`
   - T025 [P] MatchResultRepository in `backend/src/repositories/match_result_repository.py`

5. **Core Tasks - Services** (T026-T029):
   - T026 UploadService in `backend/src/services/upload_service.py`
   - T027 ExtractionService in `backend/src/services/extraction_service.py`
   - T028 MatchingService in `backend/src/services/matching_service.py`
   - T029 ReportService in `backend/src/services/report_service.py`

6. **Core Tasks - API Endpoints** (T030-T034):
   - T030 POST /api/upload in `backend/src/api/routes/upload.py`
   - T031 GET /api/sessions in `backend/src/api/routes/sessions.py`
   - T032 GET /api/sessions/{id} in `backend/src/api/routes/sessions.py`
   - T033 GET /api/sessions/{id}/report in `backend/src/api/routes/reports.py`
   - T034 DELETE /api/sessions/{id} in `backend/src/api/routes/sessions.py`

7. **Integration Tasks** (T035-T042):
   - T035 Database connection and session factory in `backend/src/database.py`
   - T036 FastAPI dependency injection in `backend/src/api/dependencies.py`
   - T037 Configuration management in `backend/src/config.py`
   - T038 Error handling middleware
   - T039 CORS configuration
   - T040 Request/response logging
   - T041 Health check endpoint
   - T042 Alembic migration for initial schema

8. **Frontend Integration Tasks** (T043-T047):
   - T043 Update API client in `app/lib/api-client.ts` for new endpoints
   - T044 Create upload page in `app/upload/page.tsx`
   - T045 Create upload form component in `components/upload-form.tsx`
   - T046 Create progress display component in `components/progress-display.tsx`
   - T047 Update session detail page for report download

9. **Kubernetes Deployment Tasks** (T048-T057):
   - T048 Build and push backend Docker image to ACR
   - T049 Build and push frontend Docker image to ACR
   - T050 Apply Secret Provider Class manifest
   - T051 Deploy PostgreSQL StatefulSet
   - T052 Initialize database schema
   - T053 Deploy backend service
   - T054 Deploy frontend service
   - T055 Apply ingress manifest
   - T056 Deploy cleanup CronJob
   - T057 Deploy backup CronJob

10. **Integration Test Tasks** [P] (T058-T066):
    - T058 [P] Upload workflow test in `backend/tests/integration/test_upload_workflow.py`
    - T059 [P] Session retrieval test in `backend/tests/integration/test_session_retrieval.py`
    - T060 [P] 90-day expiration test in `backend/tests/integration/test_90day_expiration.py`
    - T061 [P] Report generation test in `backend/tests/integration/test_report_generation.py`
    - T062 [P] Database persistence test
    - T063 [P] Cleanup CronJob test
    - T064 [P] Backup CronJob test
    - T065 [P] HTTPS access test
    - T066 [P] Cost validation test

11. **Polish Tasks** (T067-T072):
    - T067 [P] Unit tests for extraction service
    - T068 [P] Unit tests for matching service
    - T069 [P] Unit tests for report service
    - T070 Performance optimization (database query profiling)
    - T071 Update CLAUDE.md with feature 005 context
    - T072 Run complete quickstart validation

### Ordering Strategy

**Dependency Rules**:
1. Setup (T001-T010) → All other tasks
2. Contract tests (T011-T015) → Implementation tasks (must fail first)
3. Models (T016-T020) → Repositories (T021-T025)
4. Repositories (T021-T025) → Services (T026-T029)
5. Services (T026-T029) → API endpoints (T030-T034)
6. Database setup (T035, T042) → All repository/service tasks
7. Core backend (T016-T042) → Frontend integration (T043-T047)
8. All application code → Kubernetes deployment (T048-T057)
9. All implementation → Integration tests (T058-T066)
10. All features working → Polish (T067-T072)

**Parallel Execution Markers [P]**:
- Contract tests: All 5 can run in parallel (different files)
- Model creation: All 5 can run in parallel (different files)
- Repository creation: All 5 can run in parallel (different files)
- Integration tests: All 9 can run in parallel (different files, read-only)
- Unit tests: All 3 can run in parallel (different files)

**Sequential Tasks** (shared files, dependencies):
- Services (T026-T029) may share utility code → sequential
- API endpoints in same file (T031, T032, T034 in sessions.py) → sequential
- Frontend components may share types → sequential within groups

### Estimated Output

**Total Tasks**: 72 tasks across 11 categories
**Parallel Tasks**: 27 tasks marked [P] (contract tests, models, repositories, integration tests, unit tests)
**Sequential Tasks**: 45 tasks (setup, services, endpoints, integration, deployment, polish)

**Execution Time Estimate**:
- Sequential tasks: ~15 hours (45 tasks × 20 minutes average)
- Parallel tasks: ~3 hours (27 tasks in batches of 5-10)
- Total: ~18-20 hours with parallel execution

**Dependencies Summary**:
```
Setup (T001-T010)
  ↓
Contract Tests [P] (T011-T015)
  ↓
Models [P] (T016-T020)
  ↓
Repositories [P] (T021-T025)
  ↓
Services (T026-T029)
  ↓
API Endpoints (T030-T034)
  ↓
Integration (T035-T042)
  ↓
Frontend (T043-T047)
  ↓
Deployment (T048-T057)
  ↓
Integration Tests [P] (T058-T066)
  ↓
Polish [P] (T067-T072)
```

**IMPORTANT**: This phase will be executed by the `/tasks` command, NOT by `/plan`.

## Phase 3+: Future Implementation

**These phases are beyond the scope of the /plan command**

**Phase 3**: Task execution (/tasks command creates tasks.md with 72 numbered tasks)
**Phase 4**: Implementation (execute tasks.md following TDD and dependency order)
**Phase 5**: Validation (run integration tests, execute quickstart.md, verify cost targets)

## Complexity Tracking

**Status**: ✅ No complexity violations

This implementation follows standard web application patterns:
- Three-tier architecture (presentation, business logic, data access)
- Repository pattern for data access abstraction
- Service layer for business logic encapsulation
- Async I/O for non-blocking database operations
- Infrastructure as code for reproducible deployments

**Justification**: Not applicable - no violations detected

## Progress Tracking

### Phase 0: Research ✅
- [x] Technical unknowns identified from spec
- [x] Research tasks dispatched (6 major areas)
- [x] Findings consolidated in research.md
- [x] All NEEDS CLARIFICATION resolved
- [x] **Output**: research.md (1,390 lines, 6 decisions documented)

### Phase 1: Design & Contracts ✅
- [x] Entities extracted from spec (5 core + 1 ephemeral)
- [x] Data model documented with PostgreSQL schema
- [x] API contracts defined (5 endpoints, OpenAPI 3.0)
- [x] Kubernetes manifests created (12 YAML files)
- [x] Contract tests planned (5 tests, not implemented yet)
- [x] Integration test scenarios documented (9 scenarios)
- [x] Quickstart guide created (1,236 lines)
- [x] **Output**: data-model.md (795 lines), contracts/ (12 files), quickstart.md (1,236 lines)

### Phase 2: Task Planning ✅
- [x] Task generation strategy documented
- [x] 72 tasks identified across 11 categories
- [x] Dependency graph created
- [x] Parallel execution markers applied (27 tasks)
- [x] Estimated execution time calculated (18-20 hours)
- [x] **Ready for**: /tasks command to generate tasks.md

### Final Checklist ✅
- [x] All research complete (research.md)
- [x] All design complete (data-model.md, contracts/, quickstart.md)
- [x] Constitution check passed (no violations)
- [x] Task planning approach documented
- [x] No ERROR states in execution
- [x] **Status**: READY FOR /tasks COMMAND

---

**Next Command**: `/tasks` to generate tasks.md with 72 numbered tasks based on this plan

**Artifacts Generated**:
1. ✅ `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/spec.md` (existing, 247 lines, 8 clarifications)
2. ✅ `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/research.md` (1,390 lines)
3. ✅ `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/data-model.md` (795 lines)
4. ✅ `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/contracts/api-openapi-ref.md` (23 lines)
5. ✅ `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/contracts/k8s/` (12 YAML files)
6. ✅ `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/quickstart.md` (1,236 lines)
7. ✅ `/Users/rogercox/Credit-Card-Processor/specs/005-lean-internal-deployment/plan.md` (THIS FILE)
