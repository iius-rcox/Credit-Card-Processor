# Data Model: Better Status Updates

**Feature**: 006-better-status-updates
**Date**: 2025-10-08
**Phase**: Phase 1 - Design

## Overview
This document defines the data structures for tracking progress across PDF processing phases with page-level granularity and multi-file support.

---

## Entities

### 1. Session (Extended)

**Purpose**: Extend existing Session model with progress tracking fields

**Fields:**
- `processing_progress` (JSONB, nullable): Complete progress state snapshot
- `current_phase` (VARCHAR(50), nullable): Cached current phase for filtering
- `overall_percentage` (DECIMAL(5,2), nullable): Cached aggregate progress (0.00-100.00)

**Relationships:**
- Existing relationships unchanged (employees, transactions, receipts)

**Validation Rules:**
- `overall_percentage`: Must be between 0 and 100
- `current_phase`: One of: 'upload', 'processing', 'matching', 'report_generation', 'completed', 'failed'
- `processing_progress`: Must conform to ProcessingProgress schema (validated via Pydantic)

**State Transitions:**
```
null → upload → processing → matching → report_generation → completed
                    ↓             ↓              ↓
                  failed       failed         failed
```

**Lifecycle:**
- Created: When session starts
- Updated: Every 2-3 seconds during processing
- Cleared: `processing_progress` set to null on completion
- Deleted: Cascades on session deletion (90-day retention)

---

### 2. ProcessingProgress (Pydantic Schema)

**Purpose**: Structure for JSONB `processing_progress` column

**Fields:**
- `overall_percentage` (int, 0-100): Aggregate progress across all phases
- `current_phase` (str): Active phase name
- `phases` (dict[str, PhaseProgress]): Progress per phase
- `last_update` (datetime): Timestamp of last update
- `status_message` (str): Human-readable status (e.g., "Processing File 2 of 3: Page 5/12")
- `error` (ErrorContext, optional): Error details if failed

**Example:**
```json
{
  "overall_percentage": 45,
  "current_phase": "processing",
  "phases": {
    "upload": {
      "status": "completed",
      "percentage": 100,
      "completed_at": "2025-10-08T14:23:15Z"
    },
    "processing": {
      "status": "in_progress",
      "percentage": 35,
      "total_files": 3,
      "current_file_index": 1,
      "current_file": {
        "name": "statement_002.pdf",
        "total_pages": 12,
        "current_page": 5,
        "regex_matches_found": 23
      }
    },
    "matching": {
      "status": "pending",
      "percentage": 0
    },
    "report_generation": {
      "status": "pending",
      "percentage": 0
    }
  },
  "last_update": "2025-10-08T14:25:42Z",
  "status_message": "Processing File 2 of 3: Page 5/12"
}
```

**Validation:**
- `overall_percentage`: 0 ≤ value ≤ 100
- `current_phase`: Must exist in `phases` dict
- `phases`: At least one phase required
- `last_update`: Must be recent (within last 5 minutes for active processing)

---

### 3. PhaseProgress (Nested Schema)

**Purpose**: Progress details for a single processing phase

**Fields:**
- `status` (enum): 'pending', 'in_progress', 'completed', 'failed'
- `percentage` (int, 0-100): Progress within this phase
- `started_at` (datetime, optional): When phase began
- `completed_at` (datetime, optional): When phase finished
- **Phase-Specific Fields** (flexible, varies by phase):
  - Upload: `files_uploaded`, `bytes_uploaded`
  - Processing: `total_files`, `current_file_index`, `current_file` (FileProgress)
  - Matching: `matches_found`, `unmatched_count`
  - Report Generation: `report_type`, `records_written`

**Validation:**
- `percentage`: 0 ≤ value ≤ 100
- `completed_at`: Must be after `started_at`
- If `status == 'completed'`: `percentage` must be 100
- If `status == 'in_progress'`: `started_at` must be set

---

### 4. FileProgress (Nested Schema)

**Purpose**: Tracks progress for a single PDF file during processing phase

**Fields:**
- `name` (str): Filename
- `file_id` (UUID, optional): Reference to uploaded file (if tracked separately)
- `total_pages` (int): Total page count from PDF metadata
- `current_page` (int): Currently processing page number
- `regex_matches_found` (int): Count of regex matches extracted so far
- `started_at` (datetime): When file processing began
- `completed_at` (datetime, optional): When file processing finished

**Derived Fields:**
- `percentage`: `(current_page / total_pages) * 100`

**Validation:**
- `current_page`: 1 ≤ value ≤ `total_pages`
- `total_pages`: Must be > 0
- `regex_matches_found`: Must be ≥ 0

**Example:**
```json
{
  "name": "statement_002.pdf",
  "total_pages": 12,
  "current_page": 5,
  "regex_matches_found": 23,
  "started_at": "2025-10-08T14:24:30Z"
}
```

---

### 5. ErrorContext (Nested Schema)

**Purpose**: Captures error details when processing fails

**Fields:**
- `type` (str): Error class name (e.g., "ExtractionError", "ValidationError")
- `message` (str): Human-readable error message
- `context` (dict): Error location details
  - `phase` (str): Which phase failed
  - `file` (str, optional): Filename where error occurred
  - `page` (int, optional): Page number where error occurred
- `timestamp` (datetime): When error occurred
- `traceback` (str, optional): Stack trace (for debugging, not shown to user)

**Example:**
```json
{
  "type": "RegexExtractionError",
  "message": "Invalid regex pattern in transaction extraction",
  "context": {
    "phase": "processing",
    "file": "statement_002.pdf",
    "page": 5
  },
  "timestamp": "2025-10-08T14:27:00Z"
}
```

**Usage:**
- Stored in `ProcessingProgress.error` field
- Satisfies FR-015 (indicate which phase failed)
- Provides context for FR-016 (error messages with context)

---

## Data Flow

### 1. Progress Update Flow

```
ExtractionService.process_page()
    ↓
ProgressTracker.update_progress()
    ↓
[Batch check: elapsed >= 2.5s OR boundary]
    ↓
ProgressRepository.update_session_progress()
    ↓
Session.processing_progress (JSONB) updated
Session.current_phase updated (cached)
Session.overall_percentage updated (cached)
```

### 2. Progress Retrieval Flow

```
Frontend polls GET /api/sessions/{id}/progress
    ↓
ProgressService.get_progress()
    ↓
SessionRepository.get_session(id)
    ↓
Return Session.processing_progress + cached fields
```

### 3. Multi-File Aggregation Flow

```
For each file in batch:
    ProgressTracker.update_progress(file, page, total)
        ↓
    Calculate file_percentage = (page / total) * 100
        ↓
    Calculate aggregate_percentage =
        ((files_completed + current_file_contribution) / total_files) * 100
        ↓
    Update ProcessingProgress with both file-level and aggregate
```

---

## Persistence Strategy

### Database Schema Changes

**Table**: `sessions` (existing, to be extended)

**New Columns:**
```sql
ALTER TABLE sessions
ADD COLUMN processing_progress JSONB DEFAULT NULL,
ADD COLUMN current_phase VARCHAR(50) DEFAULT NULL,
ADD COLUMN overall_percentage DECIMAL(5,2) DEFAULT 0.00;

CREATE INDEX idx_sessions_current_phase
ON sessions(current_phase)
WHERE current_phase IS NOT NULL;
```

**Storage Characteristics:**
- JSONB size: ~500-1000 bytes per progress snapshot
- Update frequency: Every 2.5 seconds during active processing
- Cleanup: Automatic on session deletion
- Indexing: GIN index on `current_phase` for filtering (optional)

---

## Calculation Formulas

### 1. File-Level Progress

```python
file_progress_pct = (current_page / total_pages) * 100
```

### 2. Aggregate Progress (Multi-File)

```python
files_completed = current_file_index - 1
current_file_contribution = (current_page / total_pages) / total_files
aggregate_pct = ((files_completed + current_file_contribution) / total_files) * 100
```

**Example:**
- File 1: 100 pages (complete) → 33.33% of aggregate
- File 2: 50 pages, page 25 → 16.67% of aggregate
- File 3: 200 pages (not started) → 0% of aggregate
- **Total aggregate**: 50%

### 3. Overall Progress (Across Phases)

```python
# Weighted by phase importance (configurable)
phase_weights = {
    "upload": 0.1,        # 10% of overall
    "processing": 0.6,    # 60% of overall
    "matching": 0.2,      # 20% of overall
    "report_generation": 0.1  # 10% of overall
}

overall_pct = sum(
    phase_weights[phase] * phase_progress[phase]["percentage"]
    for phase in phases
)
```

**Example:**
- Upload: 100% complete → 0.1 * 100 = 10
- Processing: 50% complete → 0.6 * 50 = 30
- Matching: 0% complete → 0.2 * 0 = 0
- Report: 0% complete → 0.1 * 0 = 0
- **Overall**: 40%

---

## Pydantic Models (Python)

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID

class FileProgress(BaseModel):
    name: str
    file_id: Optional[UUID] = None
    total_pages: int = Field(gt=0)
    current_page: int = Field(ge=1)
    regex_matches_found: int = Field(ge=0)
    started_at: datetime
    completed_at: Optional[datetime] = None

    @property
    def percentage(self) -> float:
        return (self.current_page / self.total_pages) * 100

class ErrorContext(BaseModel):
    type: str
    message: str
    context: dict
    timestamp: datetime
    traceback: Optional[str] = None

class PhaseProgress(BaseModel):
    status: Literal['pending', 'in_progress', 'completed', 'failed']
    percentage: int = Field(ge=0, le=100)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    # Phase-specific fields stored in extra dict
    total_files: Optional[int] = None
    current_file_index: Optional[int] = None
    current_file: Optional[FileProgress] = None

class ProcessingProgress(BaseModel):
    overall_percentage: int = Field(ge=0, le=100)
    current_phase: str
    phases: dict[str, PhaseProgress]
    last_update: datetime
    status_message: str
    error: Optional[ErrorContext] = None
```

---

## Summary

**Key Entities:**
1. **Session (extended)**: Stores JSONB progress + cached aggregates
2. **ProcessingProgress**: Complete progress snapshot structure
3. **PhaseProgress**: Per-phase progress details
4. **FileProgress**: Per-file tracking with page counters
5. **ErrorContext**: Error details with location context

**Design Principles:**
- **Flexible**: JSONB accommodates varying phase structures
- **Efficient**: Cached aggregates avoid JSON parsing for filtering
- **Atomic**: Each update is a complete snapshot
- **Hierarchical**: Naturally represents overall → phase → file → page
- **Type-safe**: Pydantic models validate structure before persistence

Ready for API contract generation.
