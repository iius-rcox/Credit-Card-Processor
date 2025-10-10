# Credit-Card-Processor Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-08

## Active Technologies
- Python 3.11+ (backend), TypeScript/Next.js 15 (frontend) + FastAPI, SQLAlchemy, Next.js 15, React 19, SSE/WebSocket (006-better-status-updates)

## Project Structure
```
backend/
frontend/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.11+ (backend), TypeScript/Next.js 15 (frontend): Follow standard conventions

## Recent Changes
- 006-better-status-updates: Added Python 3.11+ (backend), TypeScript/Next.js 15 (frontend) + FastAPI, SQLAlchemy, Next.js 15, React 19, SSE/WebSocket

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