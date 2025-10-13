# Credit Card Processor - Complete Architecture Review

**Last Updated:** 2025-10-13
**Production URL:** https://credit-card.ii-us.com
**Repository:** https://github.com/iius-rcox/Credit-Card-Processor.git

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Backend Architecture](#backend-architecture)
5. [Frontend Architecture](#frontend-architecture)
6. [Database Schema](#database-schema)
7. [Deployment Architecture](#deployment-architecture)
8. [Development Workflow](#development-workflow)
9. [Key Features](#key-features)
10. [Environment Configuration](#environment-configuration)

---

## Project Overview

The **Credit Card Reconciliation System** is an internal application that automates the reconciliation of credit card transactions with expense receipts. It extracts data from PDF files, matches transactions to receipts using fuzzy matching algorithms, and generates reconciliation reports.

### Purpose
- Upload credit card statements and receipt reports (PDF format)
- Automatically extract transaction and receipt data using pdfplumber
- Match transactions to receipts using intelligent algorithms
- Generate Excel and CSV reports for accounting
- Manage employee aliases for name resolution
- Track incomplete transactions and credit refunds

### Business Rules
- 90-day automatic data retention
- Session-based workflow (create → process → report → cleanup)
- Employee name resolution with alias mapping
- Support for incomplete transactions and credit transactions

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Production (AKS)                        │
│                   https://credit-card.ii-us.com                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ├─── Azure Container Registry (ACR)
                              │    └── iiusacr.azurecr.io
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Azure Kubernetes Service (AKS)               │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Frontend   │  │   Backend    │  │ Celery       │        │
│  │   (Next.js)  │  │   (FastAPI)  │  │ Worker       │        │
│  │   Port 3000  │  │   Port 8000  │  │              │        │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘        │
│         │                  │                  │                 │
│         │                  │                  │                 │
│  ┌──────┴──────────────────┴──────────────────┴───────┐       │
│  │                                                       │       │
│  │  ┌──────────────┐      ┌──────────────┐            │       │
│  │  │  PostgreSQL  │      │    Redis     │            │       │
│  │  │  Port 5432   │      │  Port 6379   │            │       │
│  │  │              │      │              │            │       │
│  │  │  • sessions  │      │  • Celery    │            │       │
│  │  │  • employees │      │    queue     │            │       │
│  │  │  • trans...  │      │  • Cache     │            │       │
│  │  └──────────────┘      └──────────────┘            │       │
│  │                                                       │       │
│  └───────────────────────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Layers

1. **Presentation Layer (Frontend)**
   - Next.js 15 with React 19
   - Server-Side Rendering (SSR)
   - Tailwind CSS + Radix UI components
   - Real-time progress updates via polling

2. **API Layer (Backend)**
   - FastAPI (async Python)
   - RESTful API endpoints
   - CORS middleware
   - Request logging
   - Global exception handling

3. **Business Logic Layer**
   - Services: Upload, Extraction, Matching, Report generation
   - Repositories: Database access patterns
   - Background tasks via Celery

4. **Data Layer**
   - PostgreSQL 16 (relational data)
   - Redis 7 (task queue + cache)
   - Session-based data isolation

---

## Technology Stack

### Backend
```yaml
Language: Python 3.11+
Framework: FastAPI 0.104+
ORM: SQLAlchemy 2.0+ (async)
Database Driver: asyncpg 0.29+
Migration Tool: Alembic 1.12+
Task Queue: Celery 5.3+
Message Broker: Redis 5.0+
PDF Processing: pdfplumber 0.10.3
Server: Uvicorn with uvloop
```

### Frontend
```yaml
Framework: Next.js 15.5.4
UI Library: React 19.1.0
Styling: Tailwind CSS 4 + Radix UI
Forms: React Hook Form + Zod validation
HTTP Client: Native Fetch API
Build Tool: Turbopack (Next.js 15)
TypeScript: 5+
```

### Infrastructure
```yaml
Container Registry: Azure Container Registry (ACR)
Orchestration: Azure Kubernetes Service (AKS)
Database: PostgreSQL 16 (containerized)
Cache/Queue: Redis 7 (containerized)
Reverse Proxy: Nginx (AKS Ingress)
SSL/TLS: Let's Encrypt certificates
DNS: ii-us.com domain
```

### Development Tools
```yaml
Version Control: Git + GitHub
Testing: pytest (backend), Vitest (frontend)
Code Quality: Ruff (Python linter), ESLint (TypeScript)
Documentation: Storybook (component library)
API Docs: FastAPI OpenAPI (Swagger/ReDoc)
```

---

## Backend Architecture

### Project Structure
```
backend/
├── src/
│   ├── api/
│   │   ├── routes/            # API endpoints
│   │   │   ├── upload.py      # File upload
│   │   │   ├── sessions.py    # Session management
│   │   │   ├── progress.py    # Progress tracking
│   │   │   ├── reports.py     # Report generation
│   │   │   ├── aliases.py     # Employee aliases
│   │   │   └── health.py      # Health checks
│   │   ├── middleware/        # Request/response middleware
│   │   ├── dependencies.py    # Dependency injection
│   │   └── schemas.py         # Pydantic models
│   ├── models/                # SQLAlchemy models
│   │   ├── session.py         # Session model
│   │   ├── employee.py        # Employee model
│   │   ├── employee_alias.py  # Alias model
│   │   ├── transaction.py     # Transaction model
│   │   ├── receipt.py         # Receipt model
│   │   └── match_result.py    # Match result model
│   ├── repositories/          # Database access layer
│   │   ├── session_repository.py
│   │   ├── employee_repository.py
│   │   ├── transaction_repository.py
│   │   └── ...
│   ├── services/              # Business logic
│   │   ├── upload_service.py      # File upload handling
│   │   ├── extraction_service.py  # PDF data extraction
│   │   ├── matching_service.py    # Transaction matching
│   │   ├── report_service.py      # Report generation
│   │   ├── alias_service.py       # Name resolution
│   │   └── progress_tracker.py    # Progress tracking
│   ├── schemas/               # Data validation
│   ├── celery_app.py          # Celery configuration
│   ├── tasks.py               # Background tasks
│   ├── config.py              # Settings management
│   ├── database.py            # Database connection
│   └── main.py                # FastAPI app
├── migrations/                # Alembic migrations
├── tests/                     # Test suite
│   ├── integration/           # Integration tests
│   ├── contract/              # Contract tests
│   └── performance/           # Performance tests
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Backend container
├── alembic.ini               # Migration config
└── pytest.ini                # Test config
```

### Key Components

#### 1. API Endpoints
```python
POST   /api/upload              # Upload PDF files
GET    /api/sessions            # List sessions
GET    /api/sessions/{id}       # Get session details
GET    /api/sessions/{id}/report # Download report
GET    /api/progress/{id}       # Get progress (SSE)
GET    /api/aliases             # List employee aliases
POST   /api/aliases             # Create alias
DELETE /api/aliases/{id}        # Delete alias
GET    /api/health              # Health check
```

#### 2. Background Task Flow
```python
# 1. Upload endpoint receives files
POST /api/upload
  ↓
# 2. Create session in database
session = await upload_service.process_upload(files)
  ↓
# 3. Queue Celery task
task = process_session_task.delay(str(session.id))
  ↓
# 4. Return 202 Accepted immediately
return SessionResponse(id=session.id, status="processing")

# === Background Processing (Celery Worker) ===
# 5. Celery worker picks up task
@celery_app.task
def process_session_task(session_id):
    ↓
# 6. Extract data from PDFs
extraction_service.extract_from_pdf(pdf_path)
    ↓
# 7. Save to database
transaction_repo.bulk_insert(transactions)
receipt_repo.bulk_insert(receipts)
    ↓
# 8. Match transactions to receipts
matching_service.match_all(session_id)
    ↓
# 9. Update session status
session_repo.update(session_id, status="completed")
```

#### 3. PDF Extraction Process
```python
# extraction_service.py
class ExtractionService:
    def extract_from_pdf(self, pdf_path: Path) -> dict:
        """
        Extract data from PDF using pdfplumber.

        Process:
        1. Open PDF with pdfplumber
        2. Extract text from each page
        3. Apply regex patterns to find transactions/receipts
        4. Resolve employee names (exact match or alias)
        5. Handle incomplete/credit transactions
        6. Return structured data
        """
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                # Apply regex patterns...
                transactions = self._parse_transactions(text)
                receipts = self._parse_receipts(text)

        return {
            "transactions": transactions,
            "receipts": receipts,
            "incomplete_count": incomplete_count
        }
```

#### 4. Transaction Matching Algorithm
```python
# matching_service.py
class MatchingService:
    def match_all(self, session_id: UUID) -> list[MatchResult]:
        """
        Match transactions to receipts using fuzzy matching.

        Matching criteria:
        - Amount similarity (exact or within threshold)
        - Date proximity (transaction_date ± N days)
        - Merchant name similarity (Levenshtein distance)
        - GL code matching (if present)

        Returns list of MatchResult objects with confidence scores.
        """
        transactions = await self.transaction_repo.get_by_session(session_id)
        receipts = await self.receipt_repo.get_by_session(session_id)

        matches = []
        for txn in transactions:
            best_match = self._find_best_match(txn, receipts)
            if best_match:
                matches.append(MatchResult(...))

        return matches
```

---

## Frontend Architecture

### Project Structure
```
frontend/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── page.tsx              # Home page (upload)
│   │   ├── layout.tsx            # Root layout
│   │   ├── sessions/
│   │   │   └── [id]/
│   │   │       └── page.tsx      # Session details
│   │   └── reconciliation/
│   │       └── aliases/
│   │           └── page.tsx      # Alias management
│   ├── components/               # React components
│   │   ├── progress/
│   │   │   ├── ProgressOverview.tsx
│   │   │   ├── PhaseIndicator.tsx
│   │   │   ├── FileProgressList.tsx
│   │   │   ├── StatusMessage.tsx
│   │   │   └── ErrorDisplay.tsx
│   │   └── AliasManager.tsx
│   ├── services/                 # API clients
│   │   ├── apiClient.ts          # Base API client
│   │   ├── sessionService.ts     # Session API
│   │   └── aliasService.ts       # Alias API
│   ├── types/                    # TypeScript types
│   │   ├── session.ts
│   │   ├── progress.ts
│   │   └── alias.ts
│   └── hooks/                    # Custom React hooks
│       └── useProgress.ts        # Progress polling hook
├── public/                       # Static assets
├── Dockerfile                    # Frontend container
└── package.json                  # Dependencies
```

### Key Components

#### 1. Upload Flow
```typescript
// app/page.tsx
export default function HomePage() {
  const handleUpload = async (files: File[]) => {
    // 1. Create FormData
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));

    // 2. POST to /api/upload
    const response = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    // 3. Get session ID from response
    const session = await response.json();

    // 4. Redirect to session page
    router.push(`/sessions/${session.id}`);
  };

  return <FileUploadForm onSubmit={handleUpload} />;
}
```

#### 2. Progress Tracking
```typescript
// hooks/useProgress.ts
export function useProgress(sessionId: string) {
  const [progress, setProgress] = useState<ProgressState | null>(null);

  useEffect(() => {
    // Poll every 2 seconds
    const interval = setInterval(async () => {
      const response = await fetch(`/api/sessions/${sessionId}`);
      const data = await response.json();
      setProgress(data.processing_progress);

      // Stop polling when completed/failed
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(interval);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [sessionId]);

  return progress;
}
```

#### 3. Component Architecture
```typescript
// Session Details Page
<SessionPage>
  <ProgressOverview progress={progress} />

  <PhaseIndicator
    phases={['upload', 'processing', 'matching', 'report']}
    currentPhase={progress.current_phase}
  />

  <FileProgressList files={progress.files} />

  {progress.error && <ErrorDisplay error={progress.error} />}

  {session.status === 'completed' && (
    <ReportDownloadButtons sessionId={session.id} />
  )}
</SessionPage>
```

---

## Database Schema

### Entity Relationship Diagram
```
┌─────────────┐
│  sessions   │
│  (parent)   │
├─────────────┤
│ id (PK)     │
│ status      │
│ upload_count│
│ created_at  │
│ expires_at  │
│ progress    │
└──────┬──────┘
       │
       │ session_id (FK, CASCADE)
       ├─────────────────────────────┐
       │                             │
       ▼                             ▼
┌──────────────┐            ┌─────────────────┐
│  employees   │            │  transactions   │
├──────────────┤            ├─────────────────┤
│ id (PK)      │            │ id (PK)         │
│ session_id   │◄───────────│ session_id      │
│ name         │            │ employee_id (FK)│
│ dept         │            │ amount          │
│ cost_center  │            │ merchant_name   │
└──────┬───────┘            │ date            │
       │                    │ incomplete_flag │
       │                    │ is_credit       │
       │                    └─────────────────┘
       │ employee_id (FK)
       ▼
┌──────────────────┐
│ employee_aliases │
├──────────────────┤
│ id (PK)          │
│ extracted_name   │◄── Maps PDF names to employees
│ employee_id (FK) │
└──────────────────┘

       ┌─────────────────┐
       │    receipts     │
       ├─────────────────┤
       │ id (PK)         │
       │ session_id      │
       │ employee_id (FK)│
       │ amount          │
       │ merchant_name   │
       │ date            │
       │ gl_code         │
       └────────┬────────┘
                │
                │ receipt_id (FK)
                │ transaction_id (FK)
                ▼
       ┌─────────────────┐
       │  match_results  │
       ├─────────────────┤
       │ id (PK)         │
       │ session_id      │
       │ transaction_id  │
       │ receipt_id      │
       │ confidence      │
       │ match_status    │
       └─────────────────┘
```

### Table Definitions

#### sessions
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'processing',
    upload_count INTEGER DEFAULT 0,
    total_transactions INTEGER DEFAULT 0,
    total_receipts INTEGER DEFAULT 0,
    matched_count INTEGER DEFAULT 0,
    processing_progress JSONB,
    current_phase VARCHAR(50),
    overall_percentage NUMERIC(5,2) DEFAULT 0.00,
    summary VARCHAR(500),
    CONSTRAINT chk_status CHECK (status IN ('processing', 'extracting', 'matching', 'completed', 'failed', 'expired'))
);
```

#### transactions
```sql
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id),
    transaction_date DATE NOT NULL,
    post_date DATE,
    amount NUMERIC(10,2) NOT NULL,  -- Allows negative for credits
    currency VARCHAR(3) DEFAULT 'USD',
    merchant_name VARCHAR(255),
    merchant_category VARCHAR(100),
    description TEXT,
    card_last_four VARCHAR(4),
    reference_number VARCHAR(50),
    incomplete_flag BOOLEAN DEFAULT FALSE,  -- Missing required fields
    is_credit BOOLEAN DEFAULT FALSE,        -- Negative amount (refund)
    raw_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### employee_aliases
```sql
CREATE TABLE employee_aliases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    extracted_name VARCHAR(255) UNIQUE NOT NULL,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_aliases_extracted_name ON employee_aliases(extracted_name);
```

### Data Retention
- Sessions automatically expire after 90 days
- All related data (employees, transactions, receipts, matches) cascade deleted
- Cron job runs daily to clean up expired sessions

---

## Deployment Architecture

### Production Environment (Azure AKS)

#### Infrastructure Components
```yaml
Cluster: dev-aks (Azure Kubernetes Service)
Resource Group: rg_prod
Container Registry: iiusacr.azurecr.io
Namespace: credit-card-processor
Ingress: Nginx Ingress Controller
SSL: Let's Encrypt (auto-renewal)
Domain: credit-card.ii-us.com
```

#### Kubernetes Resources
```yaml
Deployments:
  - frontend:
      replicas: 2
      image: iiusacr.azurecr.io/expense-frontend:v1.0.1
      resources:
        limits: { cpu: 1000m, memory: 1Gi }
        requests: { cpu: 500m, memory: 512Mi }

  - backend:
      replicas: 2
      image: iiusacr.azurecr.io/expense-backend:v1.0.1
      resources:
        limits: { cpu: 2000m, memory: 2Gi }
        requests: { cpu: 1000m, memory: 1Gi }

  - celery-worker:
      replicas: 2
      image: iiusacr.azurecr.io/expense-backend:v1.0.1
      resources:
        limits: { cpu: 2000m, memory: 2Gi }
        requests: { cpu: 1000m, memory: 1Gi }

Services:
  - frontend-service (ClusterIP, port 3000)
  - backend-service (ClusterIP, port 8000)
  - postgres-service (ClusterIP, port 5432)
  - redis-service (ClusterIP, port 6379)

Ingress:
  - Host: credit-card.ii-us.com
  - TLS: Let's Encrypt certificate
  - Paths:
      / → frontend-service:3000
      /api → backend-service:8000

ConfigMaps:
  - backend-config (environment variables)

Secrets:
  - database-credentials
  - redis-credentials
```

### Deployment Process

#### 1. Build & Push Images
```bash
# Build frontend
docker build -t iiusacr.azurecr.io/expense-frontend:v1.0.1 \
  -f deploy/Dockerfile .

# Build backend
docker build -t iiusacr.azurecr.io/expense-backend:v1.0.1 \
  -f backend/Dockerfile backend/

# Push to ACR
az acr login --name iiusacr
docker push iiusacr.azurecr.io/expense-frontend:v1.0.1
docker push iiusacr.azurecr.io/expense-backend:v1.0.1
```

#### 2. Deploy to AKS
```bash
# Get AKS credentials
az aks get-credentials --resource-group rg_prod --name dev-aks

# Update deployments
kubectl set image deployment/frontend \
  frontend=iiusacr.azurecr.io/expense-frontend:v1.0.1 \
  -n credit-card-processor

kubectl set image deployment/backend \
  backend=iiusacr.azurecr.io/expense-backend:v1.0.1 \
  -n credit-card-processor

# Wait for rollout
kubectl rollout status deployment/frontend -n credit-card-processor
kubectl rollout status deployment/backend -n credit-card-processor
```

#### 3. Automated Deployment Script
```bash
# Full deployment (builds both, pushes, deploys)
./deploy/deploy-all.sh v1.0.1 v1.0.1

# Frontend only
./deploy/deploy-frontend.ps1 -ImageTag "v1.0.1"
```

### Local Development Environment

#### Docker Compose Setup
```bash
# Start all services
cd deploy
docker-compose up -d

# Services:
# - PostgreSQL: localhost:5432
# - Redis: localhost:6379
# - Backend: localhost:8000
# - Frontend: localhost:3000
# - Celery Worker: (background)

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f celery-worker

# Stop all
docker-compose down
```

---

## Development Workflow

### Getting Started

#### 1. Clone Repository
```bash
git clone https://github.com/iius-rcox/Credit-Card-Processor.git
cd Credit-Card-Processor
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start Celery worker (separate terminal)
celery -A src.celery_app worker --loglevel=debug --concurrency=2
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local

# Start frontend
npm run dev

# Open http://localhost:3000
```

### Testing

#### Backend Tests
```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/integration/
pytest tests/contract/
pytest tests/performance/

# Run contract tests only
./run_contract_tests.sh
```

#### Frontend Tests
```bash
cd frontend

# Run unit tests
npm run test

# Run with coverage
npm run test:coverage

# Run Storybook
npm run storybook
```

### Code Quality

#### Backend (Python)
```bash
# Lint with Ruff
ruff check .

# Format with Ruff
ruff format .

# Type checking (if using mypy)
mypy src/
```

#### Frontend (TypeScript)
```bash
# Lint with ESLint
npm run lint

# Type checking
npm run type-check  # If configured
```

---

## Key Features

### 1. PDF Data Extraction
- **Library:** pdfplumber 0.10.3
- **Process:**
  1. Extract text from each PDF page
  2. Apply regex patterns to identify transactions/receipts
  3. Parse structured data (dates, amounts, merchants)
  4. Handle incomplete data gracefully
- **Supported Formats:**
  - Cardholder Activity Report
  - Receipt Images Report

### 2. Employee Name Resolution
- **Exact Match:** Direct lookup in employees table
- **Alias Mapping:** Fallback to employee_aliases table
- **Graceful Handling:** Flag incomplete if no match found
- **Management UI:** Add/remove aliases via /reconciliation/aliases

### 3. Transaction Matching
- **Algorithm:** Fuzzy matching with multiple criteria
- **Criteria:**
  - Amount similarity
  - Date proximity (± configurable days)
  - Merchant name (Levenshtein distance)
  - GL code matching
- **Confidence Scoring:** 0-100 scale
- **Manual Override:** Review and adjust matches

### 4. Report Generation
- **Excel Format:** Detailed reconciliation report
  - Summary sheet
  - Transactions sheet
  - Receipts sheet
  - Matches sheet
- **CSV Format:** Raw data export
- **Filtering:** Complete/incomplete employees

### 5. Progress Tracking
- **Real-time Updates:** Poll every 2 seconds
- **Phases:** Upload → Processing → Matching → Report
- **Per-File Progress:** Track each PDF individually
- **Error Handling:** Detailed error messages

### 6. Session Management
- **List View:** All sessions with status
- **Details View:** Full session information
- **Auto-Expiration:** 90-day retention
- **Clean Architecture:** Session-based data isolation

#### Session Status State Machine
```
processing (initial upload)
    ↓
extracting (PDF extraction phase) [optional]
    ↓
matching (transaction matching phase)
    ↓
completed (success) OR failed (error occurred)

expired (auto-cleanup after 90 days)
```

**Status Transitions:**
- `processing` → `extracting`, `matching`, `completed`, `failed`
- `extracting` → `matching`, `completed`, `failed`
- `matching` → `completed`, `failed`
- `completed` → (terminal state)
- `failed` → (terminal state)
- `expired` → (terminal state)

**Validation:** All status transitions are validated in `Session.validate_status_transition()` before database update.

### 7. Incomplete Transaction Handling
- **Detection:** Flag when required fields missing
- **Visibility:** Highlight in reports
- **Resolution:** Manual data entry or alias creation

### 8. Credit Transaction Support
- **Detection:** Negative amounts automatically flagged
- **Separate Tracking:** is_credit boolean field
- **Reporting:** Separate counts in summary

---

## Environment Configuration

### Backend Environment Variables
```bash
# Environment
ENVIRONMENT=production              # development | production | test
LOG_LEVEL=INFO                     # DEBUG | INFO | WARNING | ERROR

# Database (PostgreSQL)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
POSTGRES_HOST=postgres-service.credit-card-processor.svc.cluster.local
POSTGRES_PORT=5432
POSTGRES_DB=credit_card_db
POSTGRES_USER=ccprocessor
POSTGRES_PASSWORD=<secret>

# Redis (Task Queue)
REDIS_URL=redis://redis-service:6379/0
REDIS_HOST=redis-service.credit-card-processor.svc.cluster.local
REDIS_PORT=6379

# Azure (Production Secrets)
AZURE_KEY_VAULT_NAME=<vault-name>
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<client-id>

# Upload Settings
MAX_UPLOAD_SIZE_MB=300
MAX_UPLOAD_COUNT=100
TEMP_STORAGE_PATH=/tmp/credit-card-uploads

# CORS
CORS_ORIGINS=["https://credit-card.ii-us.com"]

# API
API_V1_PREFIX=/api
```

### Frontend Environment Variables
```bash
# API URL
NEXT_PUBLIC_API_URL=https://credit-card.ii-us.com/api

# Environment
NODE_ENV=production  # development | production

# Build Config
NEXT_TELEMETRY_DISABLED=1
```

---

## Monitoring & Observability

### Health Checks
```bash
# Backend health
curl https://credit-card.ii-us.com/api/health

# Frontend health
curl https://credit-card.ii-us.com/

# Database health
kubectl exec -it <backend-pod> -n credit-card-processor -- \
  psql $DATABASE_URL -c "SELECT 1"

# Redis health
kubectl exec -it <redis-pod> -n credit-card-processor -- \
  redis-cli ping
```

### Logging
- **Backend:** Structured JSON logs to stdout
- **Frontend:** Console logs (development only)
- **Celery:** Detailed task execution logs
- **Aggregation:** Azure Monitor / Log Analytics (if configured)

### Metrics (Future Enhancement)
- Request latency
- Task processing time
- Queue depth
- Error rates
- Session success/failure rates

---

## Security Considerations

### Authentication & Authorization
- **Current:** Internal application (no auth)
- **Future:** Azure AD integration recommended

### Data Protection
- **In Transit:** TLS 1.2+ (Let's Encrypt)
- **At Rest:** PostgreSQL encryption (Azure managed)
- **Sensitive Data:** Environment variables via Kubernetes secrets

### Input Validation
- **File Upload:** Type checking, size limits, virus scanning (future)
- **API Input:** Pydantic validation
- **SQL Injection:** SQLAlchemy ORM prevents this

### CORS Configuration
- **Production:** Strict origin checking
- **Development:** Localhost allowed

---

## Known Issues & Limitations

### Current Issues
1. **No real-time progress:** Using polling instead of WebSockets/SSE (future enhancement)

### Recently Fixed Issues (2025-10-13)
1. **Processing Stuck Bug:** Sessions were getting stuck in 'processing' status due to database constraint violation when code attempted to transition to 'matching' status. Fixed by:
   - Updating database constraint to allow 'extracting' and 'matching' statuses
   - Adding status validation helper method in Session model
   - Enhanced logging in SessionRepository for status transitions
   - Migration: `20251013_1622_add_extracting_matching_status.py`

### Limitations
1. **PDF Format Support:** Limited to specific WEX formats
2. **Concurrent Uploads:** No limit on simultaneous sessions
3. **Large File Handling:** 300MB limit per file
4. **Error Recovery:** No automatic retry for failed tasks
5. **Manual Intervention:** Requires alias creation for unknown names

### Future Enhancements
1. **Real-time Updates:** Implement WebSocket/SSE for progress
2. **Advanced Matching:** Machine learning for better accuracy
3. **Bulk Operations:** Process multiple sessions simultaneously
4. **Email Notifications:** Alert on completion/failure
5. **Audit Trail:** Track all changes and actions
6. **API Versioning:** Prepare for breaking changes
7. **Multi-tenant:** Support multiple organizations

---

## Troubleshooting Guide

### Backend Not Starting
```bash
# Check logs
docker logs credit-card-backend

# Common issues:
# - Missing pdfplumber: pip install pdfplumber==0.10.3
# - Database connection: Check DATABASE_URL
# - Redis connection: Check REDIS_URL
```

### Celery Worker Not Processing
```bash
# Check worker status
docker exec credit-card-celery-worker celery -A src.celery_app inspect active

# Check registered tasks
docker exec credit-card-celery-worker celery -A src.celery_app inspect registered

# Check Redis queue
docker exec credit-card-redis redis-cli llen celery

# Common issues:
# - Worker not running: docker-compose up -d celery-worker
# - Redis connection: Check REDIS_URL
# - Task not registered: Check src/celery_app.py includes
```

### Frontend Build Failures
```bash
# Clear cache
rm -rf .next
npm run build

# Common issues:
# - Node version: Use Node 20+
# - Missing dependencies: npm install
# - TypeScript errors: npm run type-check
```

### Database Migration Issues
```bash
# Check current revision
alembic current

# Generate new migration
alembic revision --autogenerate -m "description"

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1
```

---

## Maintenance Tasks

### Daily
- Monitor production logs for errors
- Check Celery queue depth
- Verify session completion rates

### Weekly
- Review incomplete transactions
- Check disk usage (PostgreSQL, Redis)
- Update employee aliases as needed

### Monthly
- Database backup verification
- Security updates (dependencies)
- Performance analysis

### Quarterly
- Full disaster recovery test
- Dependency updates (major versions)
- Architecture review

---

## Contact & Support

**Development Team:**
- Repository: https://github.com/iius-rcox/Credit-Card-Processor
- Issues: https://github.com/iius-rcox/Credit-Card-Processor/issues

**Production URL:**
- https://credit-card.ii-us.com

**API Documentation:**
- https://credit-card.ii-us.com/api/docs (Swagger)
- https://credit-card.ii-us.com/api/redoc (ReDoc)

---

*Last Updated: 2025-10-13*
*Document Version: 1.0*
