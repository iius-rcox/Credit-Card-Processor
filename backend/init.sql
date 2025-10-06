-- PostgreSQL initialization script for Credit Card Reconciliation System
-- This script creates the database schema with all tables, indexes, and triggers

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
