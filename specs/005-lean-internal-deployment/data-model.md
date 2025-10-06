# Data Model: Expense Reconciliation System

## Overview

This document defines the database schema for a 90-day staging environment that processes expense reconciliation. All session data automatically expires and is eligible for deletion 90 days after creation.

## Entity Relationship Diagram

```
Session (1) ----< (N) Employee
Session (1) ----< (N) Transaction
Session (1) ----< (N) Receipt
Session (1) ----< (N) MatchResult

Employee (1) ----< (N) Transaction

Transaction (1) ----< (0..1) MatchResult
Receipt (0..1) >---- (1) MatchResult
```

**Cardinality Rules**:
- Each Session contains multiple Employees, Transactions, Receipts, and MatchResults
- Each Transaction belongs to one Employee and one Session
- Each MatchResult links one Transaction to zero or one Receipt (unmatched transactions have null receipt_id)
- All child entities are cascade-deleted when their parent Session expires

## Entity Definitions

### Session

Primary entity representing a single reconciliation workflow instance.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique session identifier |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL DEFAULT NOW() | Session creation timestamp |
| expires_at | TIMESTAMP WITH TIME ZONE | NOT NULL GENERATED ALWAYS AS (created_at + INTERVAL '90 days') STORED | Auto-calculated expiration (90 days from creation) |
| status | VARCHAR(20) | NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed', 'expired')) | Current processing state |
| upload_count | INTEGER | NOT NULL DEFAULT 0 CHECK (upload_count >= 0) | Number of files uploaded in this session |
| total_transactions | INTEGER | NOT NULL DEFAULT 0 CHECK (total_transactions >= 0) | Count of transactions processed |
| total_receipts | INTEGER | NOT NULL DEFAULT 0 CHECK (total_receipts >= 0) | Count of receipts uploaded |
| matched_count | INTEGER | NOT NULL DEFAULT 0 CHECK (matched_count >= 0) | Count of successful matches |
| updated_at | TIMESTAMP WITH TIME ZONE | NOT NULL DEFAULT NOW() | Last modification timestamp |

**Indexes**:
- `idx_sessions_created_at` ON sessions(created_at) - For 90-day window queries
- `idx_sessions_expires_at` ON sessions(expires_at) - For cleanup job efficiency
- `idx_sessions_status` ON sessions(status) - For active session queries

**Triggers**:
- `trg_sessions_update_timestamp` - Updates `updated_at` on row modification
- `trg_sessions_validate_expiration` - Ensures expires_at = created_at + 90 days

---

### Employee

Employee master data associated with a reconciliation session.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique employee record identifier |
| session_id | UUID | NOT NULL FK → sessions(id) ON DELETE CASCADE | Parent session reference |
| employee_number | VARCHAR(50) | NOT NULL | Employee identifier from source system |
| name | VARCHAR(255) | NOT NULL | Employee full name |
| department | VARCHAR(100) | NULL | Department name (optional) |
| cost_center | VARCHAR(50) | NULL | Cost center code (optional) |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL DEFAULT NOW() | Record creation timestamp |

**Indexes**:
- `idx_employees_session_id` ON employees(session_id) - For session-based queries
- `idx_employees_employee_number` ON employees(session_id, employee_number) - For lookup by employee number within session
- `idx_employees_session_created` ON employees(session_id, created_at) - For chronological retrieval

**Constraints**:
- `uq_employees_session_employee` UNIQUE(session_id, employee_number) - Prevent duplicate employees per session

---

### Transaction

Credit card or expense transactions to be reconciled against receipts.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique transaction identifier |
| session_id | UUID | NOT NULL FK → sessions(id) ON DELETE CASCADE | Parent session reference |
| employee_id | UUID | NOT NULL FK → employees(id) ON DELETE CASCADE | Employee who made the transaction |
| transaction_date | DATE | NOT NULL | Date of transaction |
| post_date | DATE | NULL | Date transaction posted to account |
| amount | DECIMAL(12,2) | NOT NULL CHECK (amount > 0) | Transaction amount (positive values only) |
| currency | CHAR(3) | NOT NULL DEFAULT 'USD' | ISO 4217 currency code |
| merchant_name | VARCHAR(255) | NOT NULL | Merchant/vendor name |
| merchant_category | VARCHAR(100) | NULL | MCC category (if available) |
| description | TEXT | NULL | Transaction description/memo |
| card_last_four | CHAR(4) | NULL | Last 4 digits of card used |
| reference_number | VARCHAR(100) | NULL | Bank reference or transaction ID |
| raw_data | JSONB | NULL | Original transaction data from source file |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL DEFAULT NOW() | Record creation timestamp |

**Indexes**:
- `idx_transactions_session_id` ON transactions(session_id) - For session retrieval
- `idx_transactions_employee_id` ON transactions(employee_id) - For employee transaction history
- `idx_transactions_session_date` ON transactions(session_id, transaction_date DESC) - For date-ordered queries
- `idx_transactions_amount` ON transactions(session_id, amount) - For amount-based matching
- `idx_transactions_merchant` ON transactions(session_id, merchant_name) - For merchant lookup
- `idx_transactions_raw_data` ON transactions USING GIN(raw_data) - For JSON queries (PostgreSQL)

**Constraints**:
- `uq_transactions_reference` UNIQUE(session_id, reference_number) WHERE reference_number IS NOT NULL - Prevent duplicate transaction imports

---

### Receipt

Uploaded receipt images and extracted data.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique receipt identifier |
| session_id | UUID | NOT NULL FK → sessions(id) ON DELETE CASCADE | Parent session reference |
| receipt_date | DATE | NOT NULL | Date on receipt |
| amount | DECIMAL(12,2) | NOT NULL CHECK (amount > 0) | Total amount on receipt |
| currency | CHAR(3) | NOT NULL DEFAULT 'USD' | ISO 4217 currency code |
| vendor_name | VARCHAR(255) | NOT NULL | Vendor name from receipt |
| file_name | VARCHAR(500) | NOT NULL | Original uploaded filename |
| file_path | VARCHAR(1000) | NOT NULL | Storage path or blob reference |
| file_size | INTEGER | NOT NULL CHECK (file_size > 0) | File size in bytes |
| mime_type | VARCHAR(100) | NOT NULL | MIME type (image/jpeg, application/pdf, etc.) |
| ocr_confidence | DECIMAL(5,4) | NULL CHECK (ocr_confidence BETWEEN 0 AND 1) | OCR extraction confidence score |
| extracted_data | JSONB | NOT NULL | Full OCR extraction results (items, tax, tip, etc.) |
| processing_status | VARCHAR(20) | NOT NULL DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')) | OCR processing state |
| error_message | TEXT | NULL | Error details if processing failed |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL DEFAULT NOW() | Upload timestamp |
| processed_at | TIMESTAMP WITH TIME ZONE | NULL | OCR completion timestamp |

**Indexes**:
- `idx_receipts_session_id` ON receipts(session_id) - For session retrieval
- `idx_receipts_session_date` ON receipts(session_id, receipt_date DESC) - For date-ordered queries
- `idx_receipts_amount` ON receipts(session_id, amount) - For amount-based matching
- `idx_receipts_vendor` ON receipts(session_id, vendor_name) - For vendor lookup
- `idx_receipts_status` ON receipts(processing_status) WHERE processing_status != 'completed' - For monitoring pending OCR jobs
- `idx_receipts_extracted_data` ON receipts USING GIN(extracted_data) - For JSON queries (PostgreSQL)

**Sample extracted_data JSON structure**:
```json
{
  "vendor": "Acme Office Supplies",
  "date": "2025-10-01",
  "total": 127.45,
  "subtotal": 118.00,
  "tax": 9.45,
  "tip": 0.00,
  "items": [
    {"description": "Paper Reams", "quantity": 5, "price": 23.60}
  ],
  "payment_method": "Credit Card",
  "raw_text": "..."
}
```

---

### MatchResult

Results of matching transactions to receipts using fuzzy logic.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | UUID | PK | Unique match result identifier |
| session_id | UUID | NOT NULL FK → sessions(id) ON DELETE CASCADE | Parent session reference |
| transaction_id | UUID | NOT NULL FK → transactions(id) ON DELETE CASCADE | Transaction being matched |
| receipt_id | UUID | NULL FK → receipts(id) ON DELETE SET NULL | Matched receipt (NULL for unmatched transactions) |
| confidence_score | DECIMAL(5,4) | NOT NULL CHECK (confidence_score BETWEEN 0 AND 1) | Match confidence (0.0 - 1.0) |
| match_status | VARCHAR(20) | NOT NULL CHECK (match_status IN ('matched', 'unmatched', 'manual_review', 'approved', 'rejected')) | Match outcome |
| match_reason | TEXT | NULL | Explanation of match logic or failure reason |
| amount_difference | DECIMAL(12,2) | NULL | Absolute difference between transaction and receipt amounts |
| date_difference_days | INTEGER | NULL CHECK (date_difference_days >= 0) | Days between transaction and receipt dates |
| merchant_similarity | DECIMAL(5,4) | NULL CHECK (merchant_similarity BETWEEN 0 AND 1) | Fuzzy string match score for merchant/vendor names |
| matching_factors | JSONB | NULL | Detailed breakdown of matching algorithm factors |
| reviewed_by | VARCHAR(255) | NULL | User who performed manual review (if applicable) |
| reviewed_at | TIMESTAMP WITH TIME ZONE | NULL | Manual review timestamp |
| notes | TEXT | NULL | User notes from manual review |
| created_at | TIMESTAMP WITH TIME ZONE | NOT NULL DEFAULT NOW() | Match execution timestamp |

**Indexes**:
- `idx_matchresults_session_id` ON matchresults(session_id) - For session retrieval
- `idx_matchresults_transaction_id` ON matchresults(transaction_id) - For join performance (critical)
- `idx_matchresults_receipt_id` ON matchresults(receipt_id) WHERE receipt_id IS NOT NULL - For reverse lookup
- `idx_matchresults_status` ON matchresults(session_id, match_status) - For filtering by match status
- `idx_matchresults_confidence` ON matchresults(session_id, confidence_score DESC) - For high-confidence matches first
- `idx_matchresults_review` ON matchresults(match_status) WHERE match_status = 'manual_review' - For review queue

**Constraints**:
- `uq_matchresults_transaction` UNIQUE(transaction_id) - One match result per transaction
- `chk_matchresults_matched_receipt` CHECK ((match_status = 'matched' AND receipt_id IS NOT NULL) OR (match_status != 'matched')) - Matched status requires receipt_id

**Sample matching_factors JSON structure**:
```json
{
  "amount_match": 1.0,
  "date_proximity": 0.95,
  "merchant_match": 0.87,
  "algorithm_version": "v2.1.0",
  "weights": {
    "amount": 0.5,
    "date": 0.3,
    "merchant": 0.2
  }
}
```

---

## Cascade Deletion Rules

When a Session is deleted (manually or via automated cleanup):
1. All Employees in the session are deleted
2. All Transactions in the session are deleted
3. All Receipts in the session are deleted (including file cleanup)
4. All MatchResults in the session are deleted

This ensures complete data removal for expired sessions.

---

## Database-Specific Implementation Notes

### PostgreSQL

```sql
-- Session table with generated expiration
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ GENERATED ALWAYS AS (created_at + INTERVAL '90 days') STORED,
    status VARCHAR(20) NOT NULL DEFAULT 'processing'
        CHECK (status IN ('processing', 'completed', 'failed', 'expired')),
    upload_count INTEGER NOT NULL DEFAULT 0 CHECK (upload_count >= 0),
    total_transactions INTEGER NOT NULL DEFAULT 0 CHECK (total_transactions >= 0),
    total_receipts INTEGER NOT NULL DEFAULT 0 CHECK (total_receipts >= 0),
    matched_count INTEGER NOT NULL DEFAULT 0 CHECK (matched_count >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Auto-update trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sessions_update_timestamp
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Cleanup job (run daily via cron/scheduler)
DELETE FROM sessions
WHERE expires_at < NOW()
  AND status != 'processing';
```

### MySQL 8.0+

```sql
-- Session table (MySQL doesn't support GENERATED ALWAYS for computed columns with intervals)
CREATE TABLE sessions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'processing'
        CHECK (status IN ('processing', 'completed', 'failed', 'expired')),
    upload_count INT NOT NULL DEFAULT 0 CHECK (upload_count >= 0),
    total_transactions INT NOT NULL DEFAULT 0 CHECK (total_transactions >= 0),
    total_receipts INT NOT NULL DEFAULT 0 CHECK (total_receipts >= 0),
    matched_count INT NOT NULL DEFAULT 0 CHECK (matched_count >= 0),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Trigger to calculate expires_at on insert
DELIMITER $$
CREATE TRIGGER trg_sessions_set_expiration
BEFORE INSERT ON sessions
FOR EACH ROW
BEGIN
    SET NEW.expires_at = DATE_ADD(NEW.created_at, INTERVAL 90 DAY);
END$$
DELIMITER ;

-- Cleanup job
DELETE FROM sessions
WHERE expires_at < NOW()
  AND status != 'processing';
```

---

## Validation Rules

### Session
- `expires_at` MUST equal `created_at + 90 days` (enforced by generated column or trigger)
- `status` transitions: processing → completed/failed → expired
- Cannot delete sessions with status = 'processing'

### Employee
- `employee_number` must be unique within a session
- `name` cannot be empty string

### Transaction
- `amount` must be positive (> 0)
- `transaction_date` cannot be in the future (> current date)
- `post_date` must be >= `transaction_date` if provided
- `currency` must be valid ISO 4217 code

### Receipt
- `amount` must be positive (> 0)
- `receipt_date` cannot be in the future (> current date)
- `file_size` must be positive (> 0)
- `ocr_confidence` must be between 0.0 and 1.0
- `extracted_data` must be valid JSON with required fields: vendor, date, total

### MatchResult
- `confidence_score` must be between 0.0 and 1.0
- If `match_status = 'matched'`, then `receipt_id` must NOT be NULL
- If `match_status != 'matched'`, then `receipt_id` must be NULL
- `amount_difference` must be non-negative (>= 0) if provided
- `date_difference_days` must be non-negative (>= 0) if provided
- Only one MatchResult per transaction (enforced by unique constraint)

---

## Performance Optimization Recommendations

### Query Patterns

**Most Common Queries**:
1. Retrieve all session data: JOIN across all tables by session_id
2. Find unmatched transactions: WHERE match_status = 'unmatched'
3. Get transactions for employee: WHERE employee_id = ?
4. Cleanup expired sessions: WHERE expires_at < NOW()

### Index Strategy

**Critical Indexes** (required for acceptable performance):
- `idx_sessions_expires_at` - Cleanup job runs daily, must be fast
- `idx_transactions_session_id` - Session retrieval is primary access pattern
- `idx_receipts_session_id` - Session retrieval is primary access pattern
- `idx_matchresults_transaction_id` - JOIN performance on transaction matching

**Recommended Indexes** (significant performance improvement):
- All composite indexes on (session_id, <sort_field>) for paginated queries
- GIN indexes on JSONB columns for extracted_data and raw_data queries
- Partial indexes on status fields to filter incomplete/pending records

### Partitioning Strategy

For high-volume deployments (>1M sessions/month):
- Partition `sessions` by `created_at` (monthly partitions)
- Partition child tables by `session_id` using hash or range partitioning
- Automatic partition creation for future months
- Automated partition dropping for data older than 90 days

Example (PostgreSQL):
```sql
CREATE TABLE sessions (
    id UUID,
    created_at TIMESTAMPTZ NOT NULL,
    -- other fields
) PARTITION BY RANGE (created_at);

CREATE TABLE sessions_2025_10 PARTITION OF sessions
    FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

CREATE TABLE sessions_2025_11 PARTITION OF sessions
    FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

### Caching Strategy

**Redis Cache Keys**:
- `session:{session_id}:summary` - Session metadata (TTL: 1 hour)
- `session:{session_id}:transactions` - All transactions (TTL: 30 min)
- `session:{session_id}:receipts` - All receipts (TTL: 30 min)
- `session:{session_id}:matches` - All match results (TTL: 15 min)

**Cache Invalidation**:
- Invalidate on any write to session's child tables
- Use Redis pub/sub for multi-instance invalidation

**Sample Cache Implementation**:
```typescript
async function getSessionWithData(sessionId: string) {
    const cacheKey = `session:${sessionId}:full`;

    // Try cache first
    const cached = await redis.get(cacheKey);
    if (cached) return JSON.parse(cached);

    // Cache miss - query database
    const session = await db.query(`
        SELECT
            s.*,
            json_agg(DISTINCT e.*) as employees,
            json_agg(DISTINCT t.*) as transactions,
            json_agg(DISTINCT r.*) as receipts,
            json_agg(DISTINCT m.*) as matches
        FROM sessions s
        LEFT JOIN employees e ON e.session_id = s.id
        LEFT JOIN transactions t ON t.session_id = s.id
        LEFT JOIN receipts r ON r.session_id = s.id
        LEFT JOIN matchresults m ON m.session_id = s.id
        WHERE s.id = $1
        GROUP BY s.id
    `, [sessionId]);

    // Cache for 15 minutes
    await redis.setex(cacheKey, 900, JSON.stringify(session));

    return session;
}
```

---

## Migration Scripts

### Initial Schema Creation

```sql
-- PostgreSQL migration
BEGIN;

-- Sessions table
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ GENERATED ALWAYS AS (created_at + INTERVAL '90 days') STORED,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    upload_count INTEGER NOT NULL DEFAULT 0,
    total_transactions INTEGER NOT NULL DEFAULT 0,
    total_receipts INTEGER NOT NULL DEFAULT 0,
    matched_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_sessions_status CHECK (status IN ('processing', 'completed', 'failed', 'expired')),
    CONSTRAINT chk_sessions_upload_count CHECK (upload_count >= 0),
    CONSTRAINT chk_sessions_total_transactions CHECK (total_transactions >= 0),
    CONSTRAINT chk_sessions_total_receipts CHECK (total_receipts >= 0),
    CONSTRAINT chk_sessions_matched_count CHECK (matched_count >= 0)
);

CREATE INDEX idx_sessions_created_at ON sessions(created_at);
CREATE INDEX idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX idx_sessions_status ON sessions(status);

-- Employees table
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    employee_number VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    department VARCHAR(100),
    cost_center VARCHAR(50),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_employees_session_employee UNIQUE(session_id, employee_number)
);

CREATE INDEX idx_employees_session_id ON employees(session_id);
CREATE INDEX idx_employees_employee_number ON employees(session_id, employee_number);
CREATE INDEX idx_employees_session_created ON employees(session_id, created_at);

-- Transactions table
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    transaction_date DATE NOT NULL,
    post_date DATE,
    amount DECIMAL(12,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    merchant_name VARCHAR(255) NOT NULL,
    merchant_category VARCHAR(100),
    description TEXT,
    card_last_four CHAR(4),
    reference_number VARCHAR(100),
    raw_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_transactions_amount CHECK (amount > 0),
    CONSTRAINT chk_transactions_post_date CHECK (post_date IS NULL OR post_date >= transaction_date),
    CONSTRAINT uq_transactions_reference UNIQUE NULLS NOT DISTINCT (session_id, reference_number)
);

CREATE INDEX idx_transactions_session_id ON transactions(session_id);
CREATE INDEX idx_transactions_employee_id ON transactions(employee_id);
CREATE INDEX idx_transactions_session_date ON transactions(session_id, transaction_date DESC);
CREATE INDEX idx_transactions_amount ON transactions(session_id, amount);
CREATE INDEX idx_transactions_merchant ON transactions(session_id, merchant_name);
CREATE INDEX idx_transactions_raw_data ON transactions USING GIN(raw_data);

-- Receipts table
CREATE TABLE receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    receipt_date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    currency CHAR(3) NOT NULL DEFAULT 'USD',
    vendor_name VARCHAR(255) NOT NULL,
    file_name VARCHAR(500) NOT NULL,
    file_path VARCHAR(1000) NOT NULL,
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    ocr_confidence DECIMAL(5,4),
    extracted_data JSONB NOT NULL,
    processing_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    CONSTRAINT chk_receipts_amount CHECK (amount > 0),
    CONSTRAINT chk_receipts_file_size CHECK (file_size > 0),
    CONSTRAINT chk_receipts_ocr_confidence CHECK (ocr_confidence IS NULL OR (ocr_confidence BETWEEN 0 AND 1)),
    CONSTRAINT chk_receipts_status CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
);

CREATE INDEX idx_receipts_session_id ON receipts(session_id);
CREATE INDEX idx_receipts_session_date ON receipts(session_id, receipt_date DESC);
CREATE INDEX idx_receipts_amount ON receipts(session_id, amount);
CREATE INDEX idx_receipts_vendor ON receipts(session_id, vendor_name);
CREATE INDEX idx_receipts_status ON receipts(processing_status) WHERE processing_status != 'completed';
CREATE INDEX idx_receipts_extracted_data ON receipts USING GIN(extracted_data);

-- MatchResults table
CREATE TABLE matchresults (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    transaction_id UUID NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
    receipt_id UUID REFERENCES receipts(id) ON DELETE SET NULL,
    confidence_score DECIMAL(5,4) NOT NULL,
    match_status VARCHAR(20) NOT NULL,
    match_reason TEXT,
    amount_difference DECIMAL(12,2),
    date_difference_days INTEGER,
    merchant_similarity DECIMAL(5,4),
    matching_factors JSONB,
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_matchresults_confidence CHECK (confidence_score BETWEEN 0 AND 1),
    CONSTRAINT chk_matchresults_status CHECK (match_status IN ('matched', 'unmatched', 'manual_review', 'approved', 'rejected')),
    CONSTRAINT chk_matchresults_date_diff CHECK (date_difference_days IS NULL OR date_difference_days >= 0),
    CONSTRAINT chk_matchresults_merchant_sim CHECK (merchant_similarity IS NULL OR (merchant_similarity BETWEEN 0 AND 1)),
    CONSTRAINT chk_matchresults_matched_receipt CHECK ((match_status = 'matched' AND receipt_id IS NOT NULL) OR (match_status != 'matched')),
    CONSTRAINT uq_matchresults_transaction UNIQUE(transaction_id)
);

CREATE INDEX idx_matchresults_session_id ON matchresults(session_id);
CREATE INDEX idx_matchresults_transaction_id ON matchresults(transaction_id);
CREATE INDEX idx_matchresults_receipt_id ON matchresults(receipt_id) WHERE receipt_id IS NOT NULL;
CREATE INDEX idx_matchresults_status ON matchresults(session_id, match_status);
CREATE INDEX idx_matchresults_confidence ON matchresults(session_id, confidence_score DESC);
CREATE INDEX idx_matchresults_review ON matchresults(match_status) WHERE match_status = 'manual_review';

-- Triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sessions_update_timestamp
    BEFORE UPDATE ON sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
```

### Rollback Script

```sql
-- PostgreSQL rollback
BEGIN;

DROP TRIGGER IF EXISTS trg_sessions_update_timestamp ON sessions;
DROP FUNCTION IF EXISTS update_updated_at_column();

DROP TABLE IF EXISTS matchresults CASCADE;
DROP TABLE IF EXISTS receipts CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS sessions CASCADE;

COMMIT;
```

---

## Query Performance Benchmarks

### Target Performance Metrics

| Query Type | Target | Acceptable | Unacceptable |
|-----------|--------|------------|--------------|
| Session retrieval (all data) | <50ms | <200ms | >500ms |
| Transaction list (paginated) | <20ms | <100ms | >300ms |
| Match result update | <10ms | <50ms | >100ms |
| Cleanup job (1000 sessions) | <5s | <30s | >60s |
| Unmatched transactions query | <30ms | <150ms | >400ms |

### Sample EXPLAIN ANALYZE Queries

**Session Retrieval**:
```sql
EXPLAIN ANALYZE
SELECT
    s.*,
    json_agg(DISTINCT jsonb_build_object(
        'id', e.id,
        'employee_number', e.employee_number,
        'name', e.name
    )) FILTER (WHERE e.id IS NOT NULL) as employees,
    json_agg(DISTINCT jsonb_build_object(
        'id', t.id,
        'date', t.transaction_date,
        'amount', t.amount,
        'merchant', t.merchant_name
    )) FILTER (WHERE t.id IS NOT NULL) as transactions,
    json_agg(DISTINCT jsonb_build_object(
        'id', r.id,
        'date', r.receipt_date,
        'amount', r.amount,
        'vendor', r.vendor_name
    )) FILTER (WHERE r.id IS NOT NULL) as receipts
FROM sessions s
LEFT JOIN employees e ON e.session_id = s.id
LEFT JOIN transactions t ON t.session_id = s.id
LEFT JOIN receipts r ON r.session_id = s.id
WHERE s.id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479'
GROUP BY s.id;

-- Expected: Index Scan on sessions, Nested Loop joins on child tables
-- Cost: <10ms for session with 100 transactions, 50 receipts
```

**Unmatched Transactions**:
```sql
EXPLAIN ANALYZE
SELECT t.*, m.match_reason
FROM transactions t
INNER JOIN matchresults m ON m.transaction_id = t.id
WHERE m.session_id = 'f47ac10b-58cc-4372-a567-0e02b2c3d479'
  AND m.match_status = 'unmatched'
ORDER BY t.amount DESC
LIMIT 50;

-- Expected: Index Scan on idx_matchresults_status, Hash Join
-- Cost: <20ms for session with 1000 transactions
```

**Cleanup Job**:
```sql
EXPLAIN ANALYZE
DELETE FROM sessions
WHERE expires_at < NOW()
  AND status != 'processing'
RETURNING id;

-- Expected: Index Scan on idx_sessions_expires_at
-- Cost: <5s for deleting 1000 expired sessions with all child records
```

---

## Monitoring Queries

**Slow Query Detection**:
```sql
-- PostgreSQL: Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Find slowest queries
SELECT
    query,
    calls,
    total_exec_time / 1000 as total_seconds,
    mean_exec_time / 1000 as avg_seconds,
    max_exec_time / 1000 as max_seconds
FROM pg_stat_statements
WHERE query LIKE '%sessions%'
   OR query LIKE '%transactions%'
   OR query LIKE '%receipts%'
ORDER BY mean_exec_time DESC
LIMIT 20;
```

**Table Size Monitoring**:
```sql
-- PostgreSQL: Check table and index sizes
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) AS index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Session Statistics**:
```sql
-- Active sessions summary
SELECT
    status,
    COUNT(*) as count,
    AVG(total_transactions) as avg_transactions,
    AVG(matched_count) as avg_matched,
    AVG(EXTRACT(EPOCH FROM (NOW() - created_at))/3600) as avg_age_hours
FROM sessions
WHERE expires_at > NOW()
GROUP BY status;
```

---

## Data Retention and Cleanup

### Automated Cleanup Job

**Schedule**: Daily at 2:00 AM (low traffic period)

**Logic**:
1. Find all sessions where `expires_at < NOW()` AND `status != 'processing'`
2. For each expired session:
   - Delete associated receipt files from storage
   - CASCADE delete all database records (automatic via FK constraints)
3. Log cleanup statistics
4. VACUUM tables to reclaim disk space

**Bash Script** (PostgreSQL + AWS S3):
```bash
#!/bin/bash
# cleanup-expired-sessions.sh

DB_HOST="localhost"
DB_NAME="expense_reconciliation"
DB_USER="cleanup_user"
S3_BUCKET="s3://receipts-staging"

# Get list of expired sessions and their receipt file paths
psql -h $DB_HOST -d $DB_NAME -U $DB_USER -t -c "
    SELECT r.file_path
    FROM receipts r
    INNER JOIN sessions s ON s.id = r.session_id
    WHERE s.expires_at < NOW()
      AND s.status != 'processing'
" | while read file_path; do
    # Delete receipt file from S3
    aws s3 rm "$S3_BUCKET/$file_path"
done

# Delete expired sessions (cascade deletes all child records)
DELETED_COUNT=$(psql -h $DB_HOST -d $DB_NAME -U $DB_USER -t -c "
    WITH deleted AS (
        DELETE FROM sessions
        WHERE expires_at < NOW()
          AND status != 'processing'
        RETURNING id
    )
    SELECT COUNT(*) FROM deleted;
")

echo "Deleted $DELETED_COUNT expired sessions at $(date)"

# Vacuum to reclaim disk space
psql -h $DB_HOST -d $DB_NAME -U $DB_USER -c "VACUUM ANALYZE sessions, employees, transactions, receipts, matchresults;"
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-06 | Initial data model specification |

---

**Document Status**: Approved for Implementation
**Next Review**: After initial deployment and performance testing
