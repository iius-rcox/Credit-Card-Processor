# Deployment Validation Quickstart Guide

**Feature**: 005-lean-internal-deployment
**System**: Expense Reconciliation System (Next.js + FastAPI)
**Target**: Azure Kubernetes Service (AKS) - dev-aks cluster
**Namespace**: credit-card-processor
**Domain**: https://credit-card.ii-us.com
**Database**: PostgreSQL StatefulSet with 90-day TTL

---

## 1. Prerequisites

### Required Access & Tools

- [ ] **kubectl** configured for dev-aks cluster
  ```bash
  # Verify kubectl context
  kubectl config current-context
  # Expected output: dev-aks or similar

  # Test access to namespace
  kubectl get pods -n credit-card-processor
  ```

- [ ] **Azure CLI** authenticated
  ```bash
  # Login to Azure
  az login

  # Verify subscription
  az account show --query name

  # Verify ACR access
  az acr login --name iiusacr
  ```

- [ ] **Access Verification**
  - Azure Container Registry (iiusacr.azurecr.io) - pull permissions
  - Azure Key Vault - read access for secrets
  - AKS cluster (dev-aks in rg_prod) - kubectl admin access
  - Internal network access to ii-us.com domain

### Sample Test Data

Prepare the following test files:

- [ ] **Credit Card Statement PDF** - Sample bank/credit card statement with 5-10 transactions
- [ ] **Receipt PDFs** (3-5 files) - Sample receipts matching some transactions
- [ ] **Employee List** - Names matching statement transactions

**Test Data Location**: Store in `C:/Users/rcox/test-data/credit-card/` for easy reference

---

## 2. Local Development Setup (Docker Compose)

### 2.1 Create docker-compose.yml

**File**: `C:/Users/rcox/OneDrive - INSULATIONS, INC/Documents/Cursor Projects/Credit-Card-Processor/docker-compose.yml`

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: credit-card-postgres
    environment:
      POSTGRES_DB: credit_card_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: dev_password_only
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d credit_card_db"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - credit-card-network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: credit-card-redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
    networks:
      - credit-card-network

  # FastAPI Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: credit-card-backend
    environment:
      DATABASE_URL: postgresql://postgres:dev_password_only@postgres:5432/credit_card_db
      REDIS_URL: redis://redis:6379/0
      ENVIRONMENT: development
      LOG_LEVEL: INFO
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./backend:/app
      - /tmp/uploads:/tmp/uploads
    networks:
      - credit-card-network

  # Next.js Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: credit-card-frontend
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NODE_ENV: development
    ports:
      - "3000:3000"
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    networks:
      - credit-card-network

volumes:
  postgres_data:
    driver: local

networks:
  credit-card-network:
    driver: bridge
```

### 2.2 Create Environment Variables

**File**: `.env.local` (root directory)

```bash
# Database Configuration
DATABASE_URL=postgresql://postgres:dev_password_only@localhost:5432/credit_card_db
POSTGRES_DB=credit_card_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev_password_only

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Configuration
ENVIRONMENT=development
LOG_LEVEL=DEBUG
API_BASE_URL=http://localhost:8000

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2.3 Create Database Schema Initialization

**File**: `init.sql`

```sql
-- Database initialization script
-- Runs automatically when PostgreSQL container starts

-- Sessions table with 90-day TTL
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '90 days'),
    status VARCHAR(50) DEFAULT 'pending',
    total_transactions INTEGER DEFAULT 0,
    matched_transactions INTEGER DEFAULT 0,
    unmatched_transactions INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Index for cleanup queries
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);

-- Employees table
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    employee_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_employees_session_id ON employees(session_id);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    merchant VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_transactions_session_id ON transactions(session_id);
CREATE INDEX idx_transactions_employee_id ON transactions(employee_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at);

-- Receipts table
CREATE TABLE IF NOT EXISTS receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    receipt_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    vendor VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_receipts_session_id ON receipts(session_id);

-- Match results table
CREATE TABLE IF NOT EXISTS match_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    transaction_id UUID REFERENCES transactions(id) ON DELETE CASCADE,
    receipt_id UUID REFERENCES receipts(id) ON DELETE CASCADE,
    match_status VARCHAR(50) DEFAULT 'unmatched',
    confidence_score DECIMAL(5, 2),
    reason_code VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_match_results_session_id ON match_results(session_id);
CREATE INDEX idx_match_results_transaction_id ON match_results(transaction_id);

-- Uploaded files tracking (temporary)
CREATE TABLE IF NOT EXISTS uploaded_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50),
    file_size INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_uploaded_files_session_id ON uploaded_files(session_id);
CREATE INDEX idx_uploaded_files_created_at ON uploaded_files(created_at);

-- Processing logs
CREATE TABLE IF NOT EXISTS processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    log_level VARCHAR(20),
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_processing_logs_session_id ON processing_logs(session_id);
CREATE INDEX idx_processing_logs_created_at ON processing_logs(created_at);
```

### 2.4 Start Local Environment

```bash
# Navigate to project directory
cd "C:/Users/rcox/OneDrive - INSULATIONS, INC/Documents/Cursor Projects/Credit-Card-Processor"

# Start all services
docker-compose up -d

# Verify all containers are running
docker-compose ps
# Expected: postgres, redis, backend, frontend - all "Up"

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Wait for services to be ready (30 seconds)
Start-Sleep -Seconds 30
```

### 2.5 Access Local Application

- [ ] **Frontend**: http://localhost:3000 (expect Next.js app)
- [ ] **Backend API Docs**: http://localhost:8000/docs (expect FastAPI Swagger UI)
- [ ] **Backend Health**: http://localhost:8000/health (expect `{"status": "healthy"}`)
- [ ] **Database**: `localhost:5432` (connect with pgAdmin or psql)

```bash
# Test database connection
docker exec -it credit-card-postgres psql -U postgres -d credit_card_db -c "\dt"
# Expected: List of tables (sessions, employees, transactions, etc.)
```

---

## 3. Deploy to AKS

### 3.1 Pre-Deployment Verification

```bash
# Verify namespace exists
kubectl get namespace credit-card-processor
# If not exists, create it:
# kubectl create namespace credit-card-processor

# Verify existing Redis service
kubectl get svc redis -n credit-card-processor
# Expected: redis service on port 6379

# Check current deployments (if replacing existing app)
kubectl get deployments -n credit-card-processor
kubectl get ingress -n credit-card-processor
```

### 3.2 Configure Secrets in Azure Key Vault

```bash
# Set Azure Key Vault name (replace with your actual vault name)
$KEYVAULT_NAME = "your-keyvault-name"

# Create database secrets
az keyvault secret set --vault-name $KEYVAULT_NAME --name POSTGRES-DB --value "credit_card_db"
az keyvault secret set --vault-name $KEYVAULT_NAME --name POSTGRES-USER --value "ccprocessor"
az keyvault secret set --vault-name $KEYVAULT_NAME --name POSTGRES-PASSWORD --value "$(openssl rand -base64 32)"

# Verify secrets
az keyvault secret list --vault-name $KEYVAULT_NAME --query "[?contains(name, 'POSTGRES')].name"
```

### 3.3 Deploy Kubernetes Manifests (In Order)

**Important**: Deploy in this exact order to ensure dependencies are met.

```bash
# Navigate to K8s manifests directory
cd "C:/Users/rcox/OneDrive - INSULATIONS, INC/Documents/Cursor Projects/Credit-Card-Processor/specs/005-lean-internal-deployment/contracts/k8s"

# Step 1: Deploy Secret Provider Class (Azure Key Vault integration)
kubectl apply -f secret-provider.yaml
kubectl get secretproviderclass -n credit-card-processor

# Step 2: Deploy PostgreSQL StatefulSet
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml

# Wait for PostgreSQL to be ready (check every 10 seconds)
kubectl wait --for=condition=ready pod -l app=postgres -n credit-card-processor --timeout=300s

# Verify PostgreSQL pod
kubectl get pods -n credit-card-processor -l app=postgres
kubectl logs -n credit-card-processor -l app=postgres --tail=50

# Step 3: Verify PVC was created
kubectl get pvc -n credit-card-processor
# Expected: postgres-storage-postgres-0 with status "Bound"

# Step 4: Initialize Database Schema
# Copy init.sql to postgres pod and execute
kubectl cp init.sql credit-card-processor/postgres-0:/tmp/init.sql
kubectl exec -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db -f /tmp/init.sql

# Verify tables created
kubectl exec -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db -c "\dt"

# Step 5: Deploy Backend Service
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml

# Wait for backend to be ready
kubectl wait --for=condition=ready pod -l app=backend -n credit-card-processor --timeout=300s

# Verify backend pod
kubectl get pods -n credit-card-processor -l app=backend
kubectl logs -n credit-card-processor -l app=backend --tail=50

# Step 6: Deploy Frontend Service
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml

# Wait for frontend to be ready
kubectl wait --for=condition=ready pod -l app=frontend -n credit-card-processor --timeout=300s

# Verify frontend pod
kubectl get pods -n credit-card-processor -l app=frontend
kubectl logs -n credit-card-processor -l app=frontend --tail=50

# Step 7: Deploy Ingress
kubectl apply -f ingress.yaml

# Verify ingress
kubectl get ingress -n credit-card-processor
# Expected: credit-card-ingress with address and host credit-card.ii-us.com

# Step 8: Deploy CronJobs (Data Cleanup & Backup)
kubectl apply -f cleanup-cronjob.yaml
kubectl apply -f backup-cronjob.yaml

# Verify CronJobs
kubectl get cronjobs -n credit-card-processor
# Expected: data-cleanup (daily 2AM), postgres-backup (weekly Sunday 1AM)
```

### 3.4 Final Deployment Verification

```bash
# Check all resources
kubectl get all -n credit-card-processor

# Expected output:
# - pod/postgres-0 (Running)
# - pod/backend-deployment-xxx (Running)
# - pod/frontend-deployment-xxx (Running)
# - service/postgres-service (ClusterIP)
# - service/backend-service (ClusterIP)
# - service/frontend-service (ClusterIP)
# - service/redis (ClusterIP - pre-existing)
# - statefulset.apps/postgres (1/1)
# - deployment.apps/backend-deployment (1/1)
# - deployment.apps/frontend-deployment (1/1)
# - ingress/credit-card-ingress

# Check pod logs for errors
kubectl logs -n credit-card-processor -l app=backend --tail=100
kubectl logs -n credit-card-processor -l app=frontend --tail=100
kubectl logs -n credit-card-processor -l app=postgres --tail=100
```

### 3.5 Environment Variables Check

```bash
# Verify backend pod environment
kubectl exec -n credit-card-processor -l app=backend -- env | grep -E 'DATABASE|REDIS|POSTGRES'

# Verify frontend pod environment
kubectl exec -n credit-card-processor -l app=frontend -- env | grep -E 'NEXT_PUBLIC|API'

# Verify postgres pod environment
kubectl exec -n credit-card-processor postgres-0 -- env | grep POSTGRES
```

---

## 4. Smoke Tests (Manual Validation)

### 4.1 Application Access Test

- [ ] **Access application via HTTPS**
  ```bash
  # From browser or curl (on internal network)
  curl -k https://credit-card.ii-us.com
  # Expected: 200 OK with HTML content

  # Check SSL certificate
  curl -vI https://credit-card.ii-us.com 2>&1 | grep -E 'SSL|TLS|certificate'
  ```

- [ ] **Check health endpoints**
  ```bash
  # Backend health
  curl -k https://credit-card.ii-us.com/health
  # Expected: {"status": "healthy", "database": "connected", "redis": "connected"}

  # API documentation
  curl -k https://credit-card.ii-us.com/docs
  # Expected: 200 OK with Swagger UI HTML
  ```

### 4.2 Upload Test PDFs

- [ ] **Prepare test data**
  - 1 credit card statement PDF (5-10 transactions)
  - 3-5 receipt PDFs

- [ ] **Upload via UI**
  1. Open https://credit-card.ii-us.com in browser
  2. Click "Upload Files" or similar
  3. Select credit card statement
  4. Select receipt PDFs
  5. Click "Process" or "Upload"
  6. **Expected**: Session ID returned, processing status shown

- [ ] **Upload via API** (alternative test)
  ```bash
  # Upload credit card statement
  curl -X POST https://credit-card.ii-us.com/api/sessions \
    -F "credit_card_statement=@test-statement.pdf" \
    -F "receipts=@receipt1.pdf" \
    -F "receipts=@receipt2.pdf" \
    -F "receipts=@receipt3.pdf"

  # Expected response:
  # {
  #   "session_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  #   "status": "processing",
  #   "created_at": "2025-10-06T12:00:00Z",
  #   "expires_at": "2026-01-04T12:00:00Z"
  # }

  # Save session_id for next steps
  $SESSION_ID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  ```

### 4.3 Check Processing Status

- [ ] **Poll session status**
  ```bash
  # Get session status (repeat every 5-10 seconds)
  curl https://credit-card.ii-us.com/api/sessions/$SESSION_ID

  # Expected progression:
  # status: "processing" -> "extracting" -> "matching" -> "completed"

  # Final response:
  # {
  #   "session_id": "...",
  #   "status": "completed",
  #   "total_transactions": 10,
  #   "matched_transactions": 7,
  #   "unmatched_transactions": 3,
  #   "created_at": "...",
  #   "expires_at": "..."
  # }
  ```

- [ ] **Check backend logs during processing**
  ```bash
  kubectl logs -n credit-card-processor -l app=backend --tail=100 -f
  # Look for:
  # - PDF extraction logs
  # - Transaction parsing logs
  # - Receipt matching logs
  # - No ERROR messages
  ```

### 4.4 Download Report

- [ ] **Download Excel report**
  ```bash
  # Download XLSX report
  curl -o report.xlsx https://credit-card.ii-us.com/api/sessions/$SESSION_ID/report?format=xlsx

  # Verify file downloaded
  ls -lh report.xlsx
  # Expected: File size > 0 bytes

  # Open in Excel and verify:
  # - Transaction list with dates, amounts, merchants
  # - Receipt list with matching status
  # - Summary statistics
  ```

- [ ] **Download CSV report** (alternative)
  ```bash
  curl -o report.csv https://credit-card.ii-us.com/api/sessions/$SESSION_ID/report?format=csv
  ```

### 4.5 Verify Database Persistence

- [ ] **Query sessions table**
  ```bash
  # Connect to database
  kubectl exec -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db

  # Inside psql:
  SELECT id, status, total_transactions, matched_transactions,
         created_at, expires_at
  FROM sessions
  ORDER BY created_at DESC
  LIMIT 5;

  # Verify:
  # - Session exists with correct status
  # - expires_at = created_at + 90 days
  # - Transaction counts match expected
  ```

- [ ] **Verify TTL calculation**
  ```sql
  SELECT
    id,
    created_at,
    expires_at,
    (expires_at - created_at) AS retention_period,
    (expires_at - NOW()) AS days_remaining
  FROM sessions
  WHERE id = '<session_id>';

  # Expected: retention_period = 90 days
  ```

- [ ] **Check related data**
  ```sql
  -- Count transactions for session
  SELECT COUNT(*) FROM transactions WHERE session_id = '<session_id>';

  -- Count receipts for session
  SELECT COUNT(*) FROM receipts WHERE session_id = '<session_id>';

  -- Check match results
  SELECT match_status, COUNT(*)
  FROM match_results
  WHERE session_id = '<session_id>'
  GROUP BY match_status;
  ```

### 4.6 Test 90-Day Cleanup CronJob

- [ ] **Manually trigger cleanup job**
  ```bash
  # Create a manual job from CronJob
  kubectl create job --from=cronjob/data-cleanup manual-cleanup-test -n credit-card-processor

  # Watch job completion
  kubectl get jobs -n credit-card-processor -w

  # Check job logs
  kubectl logs -n credit-card-processor job/manual-cleanup-test

  # Expected output:
  # - "Starting 90-day data cleanup..."
  # - "Deleting records older than: YYYY-MM-DD"
  # - "X sessions_deleted"
  # - "X transactions_deleted"
  # - "Cleanup completed successfully"
  ```

- [ ] **Verify cleanup worked** (if test data > 90 days old)
  ```bash
  # Check session count before/after
  kubectl exec -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db -c "SELECT COUNT(*) FROM sessions;"

  # Verify old data deleted
  kubectl exec -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db -c "SELECT COUNT(*) FROM sessions WHERE created_at < NOW() - INTERVAL '90 days';"
  # Expected: 0 rows
  ```

- [ ] **Delete test job**
  ```bash
  kubectl delete job manual-cleanup-test -n credit-card-processor
  ```

### 4.7 Test Backup CronJob

- [ ] **Manually trigger backup job**
  ```bash
  # Create manual backup job
  kubectl create job --from=cronjob/postgres-backup manual-backup-test -n credit-card-processor

  # Watch job progress
  kubectl get jobs -n credit-card-processor -w

  # Check job logs
  kubectl logs -n credit-card-processor job/manual-backup-test -f

  # Expected output:
  # - "Starting PostgreSQL backup..."
  # - "Backup created: /tmp/backup-YYYYMMDD-HHMMSS.sql.gz"
  # - "Backup uploaded to Azure Blob Storage"
  # - "Backup completed successfully"
  ```

- [ ] **Verify backup in Azure Blob Storage**
  ```bash
  # List backups in Azure Storage
  $STORAGE_ACCOUNT = "your-storage-account-name"
  az storage blob list \
    --account-name $STORAGE_ACCOUNT \
    --container-name postgres-backups \
    --prefix postgres/backup- \
    --query "[].{name:name, size:properties.contentLength, created:properties.creationTime}" \
    --output table

  # Expected: Latest backup file with timestamp
  ```

- [ ] **Delete test job**
  ```bash
  kubectl delete job manual-backup-test -n credit-card-processor
  ```

---

## 5. Validation Queries

### 5.1 Database Health Queries

```sql
-- Connect to database
kubectl exec -it -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db

-- Check session count and status distribution
SELECT
  status,
  COUNT(*) AS count,
  MIN(created_at) AS oldest_session,
  MAX(created_at) AS newest_session
FROM sessions
GROUP BY status;

-- Verify TTL calculation for all sessions
SELECT
  id,
  status,
  created_at,
  expires_at,
  AGE(expires_at, created_at) AS retention_period,
  CASE
    WHEN AGE(expires_at, created_at) = INTERVAL '90 days' THEN 'OK'
    ELSE 'INCORRECT'
  END AS ttl_check
FROM sessions
ORDER BY created_at DESC
LIMIT 10;

-- Check database size
SELECT
  pg_size_pretty(pg_database_size('credit_card_db')) AS database_size;

-- Check table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Verify indexes are being used (EXPLAIN query)
EXPLAIN ANALYZE
SELECT * FROM sessions
WHERE created_at < NOW() - INTERVAL '90 days';
-- Expected: Index Scan using idx_sessions_created_at

-- Check for sessions nearing expiration (next 7 days)
SELECT
  id,
  status,
  created_at,
  expires_at,
  (expires_at - NOW()) AS time_until_expiration
FROM sessions
WHERE expires_at < NOW() + INTERVAL '7 days'
ORDER BY expires_at ASC;

-- Verify cascading deletes work
SELECT
  s.id AS session_id,
  COUNT(DISTINCT t.id) AS transaction_count,
  COUNT(DISTINCT r.id) AS receipt_count,
  COUNT(DISTINCT m.id) AS match_result_count
FROM sessions s
LEFT JOIN transactions t ON t.session_id = s.id
LEFT JOIN receipts r ON r.session_id = s.id
LEFT JOIN match_results m ON m.session_id = s.id
GROUP BY s.id
ORDER BY s.created_at DESC
LIMIT 5;
```

### 5.2 API Validation (curl commands)

```bash
# Health check
curl -X GET https://credit-card.ii-us.com/health
# Expected: {"status": "healthy", "database": "connected", "redis": "connected"}

# Create new session (upload PDFs)
curl -X POST https://credit-card.ii-us.com/api/sessions \
  -F "credit_card_statement=@statement.pdf" \
  -F "receipts=@receipt1.pdf" \
  -H "Content-Type: multipart/form-data"
# Expected: {"session_id": "...", "status": "processing", ...}

# Get session status
curl -X GET https://credit-card.ii-us.com/api/sessions/<session_id>
# Expected: {"session_id": "...", "status": "completed", "total_transactions": N, ...}

# Get session report (Excel)
curl -X GET "https://credit-card.ii-us.com/api/sessions/<session_id>/report?format=xlsx" \
  -o report.xlsx
# Expected: Binary file downloaded

# Get session report (CSV)
curl -X GET "https://credit-card.ii-us.com/api/sessions/<session_id>/report?format=csv" \
  -o report.csv
# Expected: CSV file downloaded

# List all sessions (if endpoint exists)
curl -X GET https://credit-card.ii-us.com/api/sessions
# Expected: Array of session objects

# Test 404 for expired/non-existent session
curl -X GET https://credit-card.ii-us.com/api/sessions/00000000-0000-0000-0000-000000000000
# Expected: 404 Not Found or {"error": "Session not found"}
```

### 5.3 Log Analysis

```bash
# Backend application logs - check for errors
kubectl logs -n credit-card-processor -l app=backend --tail=500 | grep -i error
# Expected: No critical errors

# Backend application logs - check processing metrics
kubectl logs -n credit-card-processor -l app=backend --tail=500 | grep -E 'processing|extracted|matched'
# Look for:
# - "Extracted N transactions from statement"
# - "Extracted N receipts"
# - "Matched N transactions with receipts"

# Frontend application logs
kubectl logs -n credit-card-processor -l app=frontend --tail=200
# Expected: No build errors, successful page renders

# PostgreSQL logs - check for slow queries
kubectl logs -n credit-card-processor postgres-0 --tail=500 | grep -E 'slow|duration'
# Expected: No queries taking > 1 second

# PostgreSQL logs - check for connection errors
kubectl logs -n credit-card-processor postgres-0 --tail=500 | grep -i 'error\|fatal'
# Expected: No connection errors or fatal errors

# Ingress controller logs (if accessible)
kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx --tail=200 | grep credit-card
# Check for:
# - 200 status codes for successful requests
# - No 500 errors
# - Response times < 5 seconds
```

---

## 6. Rollback Procedure

### 6.1 Database Backup Restoration

If deployment fails or data corruption occurs:

```bash
# Step 1: Stop application pods
kubectl scale deployment backend-deployment --replicas=0 -n credit-card-processor
kubectl scale deployment frontend-deployment --replicas=0 -n credit-card-processor

# Step 2: Download backup from Azure Blob Storage
$STORAGE_ACCOUNT = "your-storage-account-name"
$BACKUP_FILE = "backup-YYYYMMDD-HHMMSS.sql.gz"

az storage blob download \
  --account-name $STORAGE_ACCOUNT \
  --container-name postgres-backups \
  --name "postgres/$BACKUP_FILE" \
  --file "$BACKUP_FILE"

# Step 3: Copy backup to PostgreSQL pod
kubectl cp "$BACKUP_FILE" credit-card-processor/postgres-0:/tmp/restore.sql.gz

# Step 4: Restore database
kubectl exec -n credit-card-processor postgres-0 -- bash -c "gunzip < /tmp/restore.sql.gz | psql -U ccprocessor -d credit_card_db"

# Step 5: Verify restoration
kubectl exec -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db -c "SELECT COUNT(*) FROM sessions;"

# Step 6: Restart application pods
kubectl scale deployment backend-deployment --replicas=1 -n credit-card-processor
kubectl scale deployment frontend-deployment --replicas=1 -n credit-card-processor

# Step 7: Verify application health
kubectl wait --for=condition=ready pod -l app=backend -n credit-card-processor --timeout=300s
curl https://credit-card.ii-us.com/health
```

### 6.2 Application Rollback (Previous Deployment)

If new deployment has issues:

```bash
# Check deployment history
kubectl rollout history deployment/backend-deployment -n credit-card-processor
kubectl rollout history deployment/frontend-deployment -n credit-card-processor

# Rollback backend to previous version
kubectl rollout undo deployment/backend-deployment -n credit-card-processor

# Rollback frontend to previous version
kubectl rollout undo deployment/frontend-deployment -n credit-card-processor

# Wait for rollback to complete
kubectl rollout status deployment/backend-deployment -n credit-card-processor
kubectl rollout status deployment/frontend-deployment -n credit-card-processor

# Verify rolled back version
kubectl describe deployment backend-deployment -n credit-card-processor | grep Image
kubectl describe deployment frontend-deployment -n credit-card-processor | grep Image

# Check health after rollback
kubectl get pods -n credit-card-processor
curl https://credit-card.ii-us.com/health
```

### 6.3 DNS Revert (If Needed)

If ingress configuration needs to be reverted:

```bash
# Delete current ingress
kubectl delete ingress credit-card-ingress -n credit-card-processor

# Restore previous ingress configuration (if backup exists)
kubectl apply -f ingress-backup.yaml

# OR recreate from previous version
git checkout HEAD~1 specs/005-lean-internal-deployment/contracts/k8s/ingress.yaml
kubectl apply -f specs/005-lean-internal-deployment/contracts/k8s/ingress.yaml

# Verify ingress
kubectl get ingress -n credit-card-processor
kubectl describe ingress credit-card-ingress -n credit-card-processor
```

### 6.4 Complete Deployment Removal

If rollback is not sufficient and clean restart is needed:

```bash
# Delete all deployments
kubectl delete deployment backend-deployment -n credit-card-processor
kubectl delete deployment frontend-deployment -n credit-card-processor

# Delete services
kubectl delete service backend-service -n credit-card-processor
kubectl delete service frontend-service -n credit-card-processor

# Delete ingress
kubectl delete ingress credit-card-ingress -n credit-card-processor

# Delete CronJobs
kubectl delete cronjob data-cleanup -n credit-card-processor
kubectl delete cronjob postgres-backup -n credit-card-processor

# CAUTION: This will delete database and all data
# kubectl delete statefulset postgres -n credit-card-processor
# kubectl delete pvc postgres-storage-postgres-0 -n credit-card-processor

# Redeploy from scratch
# Follow section 3.3 "Deploy Kubernetes Manifests (In Order)"
```

### 6.5 Health Check Verification After Rollback

```bash
# Verify all pods running
kubectl get pods -n credit-card-processor
# Expected: All pods in "Running" state, 1/1 ready

# Check pod logs for errors
kubectl logs -n credit-card-processor -l app=backend --tail=100
kubectl logs -n credit-card-processor -l app=frontend --tail=100

# Test application endpoints
curl https://credit-card.ii-us.com/health
curl https://credit-card.ii-us.com/docs
curl https://credit-card.ii-us.com/

# Test database connectivity
kubectl exec -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db -c "SELECT 1;"

# Check resource utilization
kubectl top pods -n credit-card-processor
```

---

## 7. Cost Verification

### 7.1 AKS Node Utilization

```bash
# Check node resource allocation
kubectl top nodes

# Check namespace resource usage
kubectl top pods -n credit-card-processor

# Get resource requests and limits
kubectl describe pods -n credit-card-processor | grep -A 5 "Requests\|Limits"

# Expected resource allocation:
# - postgres: 500m CPU (request), 1 CPU (limit), 1Gi-2Gi memory
# - backend: 200m CPU (request), 500m CPU (limit), 512Mi-1Gi memory
# - frontend: 100m CPU (request), 300m CPU (limit), 256Mi-512Mi memory
# - Total: ~800m CPU request, ~1.8 CPU limit, ~2-4Gi memory
```

### 7.2 Storage Usage

```bash
# Check persistent volume claims
kubectl get pvc -n credit-card-processor
# Expected: postgres-storage-postgres-0 (10Gi Premium_LRS)

# Check actual storage usage
kubectl exec -n credit-card-processor postgres-0 -- df -h /var/lib/postgresql/data
# Expected: < 1Gi used initially

# Check database size
kubectl exec -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db -c "SELECT pg_size_pretty(pg_database_size('credit_card_db'));"
# Expected: 10-50MB for small dataset

# Estimate storage costs:
# - 10Gi Premium SSD (P10): ~$2.40/month
# - Backups in blob storage (~200MB for 30 days): ~$0.02/month
# - Total storage: ~$2.50/month
```

### 7.3 Azure Cost Analysis Query

```bash
# Set variables
$RESOURCE_GROUP = "rg_prod"
$NAMESPACE = "credit-card-processor"

# Get AKS cluster cost breakdown
az consumption usage list \
  --start-date 2025-09-01 \
  --end-date 2025-10-06 \
  --query "[?contains(instanceName, 'dev-aks')].{Name:instanceName, Cost:pretaxCost, Currency:currency}" \
  --output table

# Check storage account costs
az consumption usage list \
  --start-date 2025-09-01 \
  --end-date 2025-10-06 \
  --query "[?contains(meterCategory, 'Storage')].{Name:instanceName, Cost:pretaxCost, Currency:currency}" \
  --output table

# Estimated monthly cost breakdown:
# - AKS compute (shared cluster): $0 (part of existing cluster)
# - Premium SSD storage (10Gi): ~$2.40/month
# - Blob storage (backups): ~$0.02/month
# - Egress (minimal internal traffic): ~$0.10/month
# - Total: ~$2.50-$3.00/month (well under $10 target)
```

### 7.4 Cost Optimization Verification

```bash
# Verify resource limits prevent waste
kubectl get pods -n credit-card-processor -o json | jq '.items[] | {name: .metadata.name, requests: .spec.containers[0].resources.requests, limits: .spec.containers[0].resources.limits}'

# Check for over-provisioned resources
kubectl top pods -n credit-card-processor
# Compare "CPU(cores)" and "MEMORY(bytes)" to limits
# If usage is < 50% of limits, consider reducing limits

# Verify autoscaling disabled (single replica deployment)
kubectl get hpa -n credit-card-processor
# Expected: No resources found (no horizontal pod autoscaling)

# Check for unused PVCs
kubectl get pvc -n credit-card-processor
# Verify only one PVC exists (postgres-storage)

# Verify ingress is not creating external load balancer
kubectl get svc -n credit-card-processor
# Expected: All services type ClusterIP (no LoadBalancer)
```

---

## 8. Troubleshooting Common Issues

### 8.1 Pod Not Starting

```bash
# Check pod status
kubectl get pods -n credit-card-processor

# Describe pod for events
kubectl describe pod <pod-name> -n credit-card-processor

# Common issues:
# - ImagePullBackOff: Check ACR credentials
#   kubectl get secret -n credit-card-processor
#   az acr login --name iiusacr
#
# - CrashLoopBackOff: Check application logs
#   kubectl logs <pod-name> -n credit-card-processor --previous
#
# - Pending: Check PVC status
#   kubectl get pvc -n credit-card-processor
```

### 8.2 Database Connection Errors

```bash
# Test PostgreSQL pod directly
kubectl exec -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db -c "SELECT 1;"

# Check secrets are mounted
kubectl exec -n credit-card-processor postgres-0 -- env | grep POSTGRES

# Verify service DNS resolution from backend pod
kubectl exec -n credit-card-processor -l app=backend -- nslookup postgres-service.credit-card-processor.svc.cluster.local

# Check database logs
kubectl logs -n credit-card-processor postgres-0 | grep -i error
```

### 8.3 Ingress Not Working

```bash
# Check ingress status
kubectl get ingress -n credit-card-processor
kubectl describe ingress credit-card-ingress -n credit-card-processor

# Verify ingress controller is running
kubectl get pods -n ingress-nginx

# Test backend service directly
kubectl port-forward -n credit-card-processor svc/backend-service 8000:8000
# Then access http://localhost:8000/health

# Check TLS certificate
kubectl get secret credit-card-tls-cert -n credit-card-processor
kubectl describe secret credit-card-tls-cert -n credit-card-processor
```

### 8.4 CronJob Not Running

```bash
# Check CronJob status
kubectl get cronjobs -n credit-card-processor

# Check last run
kubectl get jobs -n credit-card-processor --sort-by=.status.startTime

# Manually trigger for testing
kubectl create job --from=cronjob/data-cleanup test-cleanup -n credit-card-processor
kubectl logs -n credit-card-processor job/test-cleanup

# Verify schedule format
kubectl describe cronjob data-cleanup -n credit-card-processor | grep Schedule
```

---

## Completion Checklist

### Deployment Validation
- [ ] All pods running (postgres, backend, frontend)
- [ ] PVC bound and storage allocated
- [ ] Services created and endpoints available
- [ ] Ingress configured with TLS certificate
- [ ] CronJobs scheduled (cleanup, backup)
- [ ] Secrets mounted from Azure Key Vault

### Functional Testing
- [ ] Application accessible via HTTPS
- [ ] PDF upload and processing working
- [ ] Session data persists to database
- [ ] Reports generate and download correctly
- [ ] 90-day TTL calculated correctly
- [ ] Cleanup CronJob deletes old data
- [ ] Backup CronJob creates backups

### Operational Readiness
- [ ] Health checks passing
- [ ] Logs show no errors
- [ ] Database indexes used efficiently
- [ ] Resource utilization within limits
- [ ] Costs under $10/month target
- [ ] Rollback procedure tested and documented

---

## Quick Reference Commands

```bash
# Check deployment status
kubectl get all -n credit-card-processor

# Follow backend logs
kubectl logs -n credit-card-processor -l app=backend -f

# Access database
kubectl exec -it -n credit-card-processor postgres-0 -- psql -U ccprocessor -d credit_card_db

# Restart deployment
kubectl rollout restart deployment/backend-deployment -n credit-card-processor

# Scale replicas
kubectl scale deployment backend-deployment --replicas=0 -n credit-card-processor
kubectl scale deployment backend-deployment --replicas=1 -n credit-card-processor

# Port forward for local testing
kubectl port-forward -n credit-card-processor svc/backend-service 8000:8000
kubectl port-forward -n credit-card-processor svc/frontend-service 3000:3000

# Delete namespace (full cleanup)
# kubectl delete namespace credit-card-processor
```

---

## Support Contacts

**AKS Cluster**: dev-aks (rg_prod)
**Namespace**: credit-card-processor
**GitHub Repository**: https://github.com/iius-rcox/Credit-Card-Processor
**Domain**: https://credit-card.ii-us.com
**Documentation**: specs/005-lean-internal-deployment/
