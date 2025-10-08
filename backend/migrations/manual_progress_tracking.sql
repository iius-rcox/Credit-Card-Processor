-- Manual SQL script to add progress tracking columns to sessions table
-- Run this script if alembic migration fails due to connection issues

-- Add processing_progress JSONB column for flexible progress state
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS processing_progress JSONB;

-- Add current_phase VARCHAR column for fast filtering
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS current_phase VARCHAR(50);

-- Add overall_percentage DECIMAL column for cached aggregate
ALTER TABLE sessions
ADD COLUMN IF NOT EXISTS overall_percentage NUMERIC(5, 2) DEFAULT 0.00;

-- Add index on current_phase for efficient queries (partial index for non-null values)
CREATE INDEX IF NOT EXISTS idx_sessions_current_phase
ON sessions(current_phase)
WHERE current_phase IS NOT NULL;

-- Add check constraint for overall_percentage range
ALTER TABLE sessions
ADD CONSTRAINT chk_sessions_overall_percentage
CHECK (overall_percentage >= 0 AND overall_percentage <= 100);

-- Add check constraint for valid current_phase values
ALTER TABLE sessions
ADD CONSTRAINT chk_sessions_current_phase
CHECK (current_phase IS NULL OR current_phase IN ('upload', 'processing', 'matching', 'report_generation', 'completed', 'failed'));

-- Update alembic version table to mark this migration as complete
INSERT INTO alembic_version (version_num)
VALUES ('34992237d751')
ON CONFLICT (version_num) DO NOTHING;

-- Verify the changes
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'sessions'
    AND column_name IN ('processing_progress', 'current_phase', 'overall_percentage')
ORDER BY ordinal_position;