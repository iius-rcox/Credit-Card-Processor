# Credit-Card-Processor Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-10

## Active Technologies
- Python 3.11+ (backend), TypeScript/Next.js 15 (frontend) + FastAPI, SQLAlchemy, Next.js 15, React 19, SSE/WebSocket (006-better-status-updates)
- pdfplumber 0.10.3 for PDF text extraction (007-actual-pdf-parsing)

## Project Structure
```
backend/
  src/
    models/
      employee_alias.py (NEW - 007)
    repositories/
      alias_repository.py (NEW - 007)
    services/
      alias_service.py (NEW - 007)
      extraction_service.py (UPDATED - 007: real PDF parsing)
    api/routes/
      aliases.py (NEW - 007)
  migrations/versions/
    34a1f65dd845_add_employee_aliases_and_transaction_.py (NEW - 007)
frontend/
  src/
    services/
      aliasService.ts (NEW - 007)
    components/
      AliasManager.tsx (NEW - 007)
    app/reconciliation/aliases/
      page.tsx (NEW - 007)
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.11+ (backend), TypeScript/Next.js 15 (frontend): Follow standard conventions

## Recent Changes
- 007-actual-pdf-parsing: Real PDF extraction with regex patterns, employee alias mapping, pdfplumber integration, incomplete/credit transaction flags
- 006-better-status-updates: Added Python 3.11+ (backend), TypeScript/Next.js 15 (frontend) + FastAPI, SQLAlchemy, Next.js 15, React 19, SSE/WebSocket

## Data Model Updates (007-actual-pdf-parsing)

### New Tables
- **employee_aliases**: Maps extracted PDF names to employee records
  - id (UUID, PK)
  - extracted_name (VARCHAR, unique, indexed)
  - employee_id (UUID, FK to employees with CASCADE)
  - created_at (TIMESTAMP)

### Modified Tables
- **transactions**: Added extraction quality flags
  - incomplete_flag (BOOLEAN, default false) - Set when required fields missing
  - is_credit (BOOLEAN, default false) - Set when amount < 0
  - amount: Now allows negative values (CHECK constraint removed)

### Key Features
- Regex-based PDF parsing (pdfplumber for text extraction)
- Employee name resolution via exact match or alias lookup
- Graceful handling of incomplete extractions
- Credit/refund detection (negative amounts)
- Bulk insert optimization for 10k+ transactions

<!-- MANUAL ADDITIONS START -->
## CRITICAL: File Editing on Windows

### ⚠️ MANDATORY: Always Use Backslashes on Windows for File Paths

**When using Edit or MultiEdit tools on Windows, you MUST use backslashes (`\`) in file paths, NOT forward slashes (`/`).**

#### ❌ WRONG - Will cause errors:
```
Edit(file_path: "D:/repos/project/file.tsx", ...)
MultiEdit(file_path: "D:/repos/project/file.tsx", ...)
```

#### ✅ CORRECT - Always works:
```
Edit(file_path: "D:\repos\project\file.tsx", ...)
MultiEdit(file_path: "D:\repos\project\file.tsx", ...)
```
<!-- MANUAL ADDITIONS END -->
