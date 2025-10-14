# Implementation Plan: Refactor PDF Extraction to Backend Upload Endpoint

## Overview
Move PDF extraction from Celery worker to the backend upload endpoint. This eliminates the need for shared storage, prevents memory issues with large PDFs in background workers, and provides immediate feedback on extraction errors to users.

## Problem Statement

### Current Architecture Issues
1. **Memory Constraints:** Celery worker OOMKilled (Exit Code 137) when processing 184MB PDFs with 1Gi memory limit
2. **Azure Policy Blocker:** Cannot increase memory beyond 1Gi without policy exception
3. **Complexity:** Requires shared storage (Azure Files PVC) for file transfer between pods
4. **Delayed Feedback:** Extraction errors only discovered in background processing
5. **Resource Waste:** Files stored temporarily on disk, then loaded into memory for processing

### Root Cause
- PDFs are uploaded to backend → saved to shared storage → celery worker reads from disk → loads into memory → processes
- Large PDFs (100-200MB) cause memory exhaustion in celery worker's 1Gi container
- Shared storage adds infrastructure complexity and potential failure points

## Proposed Solution

### New Architecture: Extract During Upload

```
┌─────────────────────────────────────────────────────┐
│  Backend Pod (Upload Endpoint)                      │
│                                                      │
│  1. Receive PDF upload (streaming)                  │
│  2. Extract data immediately (pdfplumber)           │
│  3. Save extracted transactions to database         │
│  4. Discard PDF (never store to disk)               │
│  5. Queue lightweight matching task (JSON data)     │
│                                                      │
│  Memory: Processes one PDF at a time, GC cleans up  │
└─────────────────────────────────────────────────────┘
                         ↓ (Pass transaction IDs only)
┌─────────────────────────────────────────────────────┐
│  Celery Worker Pod (Matching Only)                  │
│                                                      │
│  1. Receive session ID + transaction IDs            │
│  2. Load transactions from database                 │
│  3. Run matching algorithm                          │
│  4. Save match results                              │
│  5. Mark session complete                           │
│                                                      │
│  Memory: Only loads transaction data (lightweight)  │
└─────────────────────────────────────────────────────┘
```

### Benefits
- ✅ **No shared storage required** - Eliminates Azure Files PVC, secrets, PV complexity
- ✅ **No memory issues** - Backend processes PDFs one at a time with proper GC
- ✅ **Immediate feedback** - Extraction errors shown to user during upload
- ✅ **Simpler architecture** - Fewer moving parts, easier to debug
- ✅ **Better user experience** - Progress bar shows real extraction progress
- ✅ **Lower resource usage** - Celery worker only handles lightweight matching
- ✅ **Scalability** - Can handle multiple uploads concurrently without storage contention

## Requirements Summary

### Functional Requirements
- FR1: Extract PDF data during upload request (synchronous in backend)
- FR2: Store extracted transactions in database immediately
- FR3: Queue only matching task to Celery (pass session ID)
- FR4: Display extraction progress to user during upload
- FR5: Show extraction errors immediately (invalid PDF, no transactions, etc.)
- FR6: Celery worker loads transactions from database for matching
- FR7: Remove all shared storage infrastructure (PVC, PV, secrets)
- FR8: Remove TEMP_STORAGE_PATH configuration

### Non-Functional Requirements
- NFR1: Process PDFs up to 300MB within reasonable request timeout
- NFR2: Backend memory sufficient for concurrent PDF processing
- NFR3: Graceful handling of timeout for very large PDFs
- NFR4: Progress updates during extraction (SSE streaming)
- NFR5: Transaction-based database operations (rollback on failure)

## Implementation Tasks

### Phase 1: Refactor Upload Endpoint

#### Task 1: Update UploadService to Extract Inline
- **Description**: Modify `backend/src/services/upload_service.py` to call ExtractionService directly during upload
- **Files to modify**:
  - `backend/src/services/upload_service.py`
- **Dependencies**: None
- **Estimated effort**: 30 minutes

**Changes:**
```python
# upload_service.py - process_upload method

async def process_upload(self, files: List[UploadFile]) -> Session:
    """Process uploaded files and extract data immediately."""

    # Validate files
    validated_files = []
    for file in files:
        await self._validate_file(file)
        validated_files.append(file)

    # Create session
    session = await self.session_repo.create_session({
        "status": "extracting",  # Changed from "processing"
        "upload_count": len(validated_files)
    })

    # Extract data from PDFs immediately (no temp storage!)
    transactions = []
    receipts = []

    for idx, file in enumerate(validated_files):
        # Update progress: extracting file X of Y
        if self.progress_repo:
            await self._update_extraction_progress(session.id, idx + 1, len(validated_files))

        # Extract directly from file stream (no disk write!)
        file_transactions, file_receipts = await self.extraction_service.extract_from_upload_file(
            file, session.id
        )
        transactions.extend(file_transactions)
        receipts.extend(file_receipts)

    # Bulk insert transactions and receipts
    await self.transaction_repo.bulk_create(transactions)
    await self.receipt_repo.bulk_create(receipts)

    # Update session with counts
    await self.session_repo.update_session_status(session.id, "matching")

    # Queue lightweight matching task (only session ID needed)
    from ..tasks import match_session_task
    match_session_task.delay(str(session.id))

    return session
```

#### Task 2: Create extract_from_upload_file Method in ExtractionService
- **Description**: Add method to process UploadFile directly without saving to disk
- **Files to modify**:
  - `backend/src/services/extraction_service.py`
- **Dependencies**: Task 1
- **Estimated effort**: 45 minutes

**New Method:**
```python
# extraction_service.py

async def extract_from_upload_file(
    self,
    file: UploadFile,
    session_id: UUID
) -> Tuple[List[TransactionCreate], List[ReceiptCreate]]:
    """
    Extract transactions and receipts from an uploaded PDF file stream.

    Args:
        file: FastAPI UploadFile (PDF)
        session_id: Session UUID

    Returns:
        Tuple of (transactions, receipts)

    Note:
        Processes PDF in-memory without saving to disk.
        Memory is released after processing each file.
    """
    import io

    # Read file content
    content = await file.read()

    # Process PDF from bytes (in-memory)
    pdf_stream = io.BytesIO(content)

    try:
        transactions, receipts = await self._extract_from_pdf_stream(
            pdf_stream, file.filename, session_id
        )
        return transactions, receipts
    finally:
        # Ensure memory is released
        pdf_stream.close()
        del content
        del pdf_stream
```

#### Task 3: Create New Celery Task for Matching Only
- **Description**: Create `match_session_task` that only handles matching, no extraction
- **Files to modify**:
  - `backend/src/tasks.py`
- **Dependencies**: Task 2
- **Estimated effort**: 20 minutes

**New Task:**
```python
# tasks.py

@celery_app.task(name="tasks.match_session")
def match_session_task(session_id: str) -> dict:
    """
    Background task to match transactions with receipts.

    Args:
        session_id: Session UUID string

    Returns:
        dict with status and counts

    Note:
        Transactions are already extracted and in database.
        This task only performs matching logic.
    """
    from uuid import UUID
    import asyncio

    session_uuid = UUID(session_id)
    logger.info(f"✓ CELERY TASK STARTED: match_session_task")
    logger.info(f"  Session ID: {session_id}")

    try:
        result = asyncio.run(match_session_background(session_uuid))
        return result
    except Exception as e:
        logger.error(f"Match task failed: {e}", exc_info=True)
        raise
```

### Phase 2: Update Progress Tracking

#### Task 4: Add Extraction Progress Updates
- **Description**: Update progress tracking to show extraction happening during upload
- **Files to modify**:
  - `backend/src/services/upload_service.py`
  - `backend/src/schemas/phase_progress.py` (if needed)
- **Dependencies**: Task 1
- **Estimated effort**: 20 minutes

**Progress Updates:**
```python
async def _update_extraction_progress(
    self,
    session_id: UUID,
    files_processed: int,
    total_files: int,
    current_filename: str,
    transactions_found: int = 0
) -> None:
    """Update progress during PDF extraction."""
    percentage = int((files_processed / total_files) * 100)

    progress = ProcessingProgress(
        overall_percentage=int(percentage * 0.6),  # Extraction is 60% of overall
        current_phase="extracting",
        phases={
            "upload": PhaseProgress(status="completed", percentage=100),
            "extracting": PhaseProgress(
                status="in_progress",
                percentage=percentage,
                files_processed=files_processed,
                total_files=total_files,
                transactions_found=transactions_found
            ),
            "matching": PhaseProgress(status="pending", percentage=0),
            "report_generation": PhaseProgress(status="pending", percentage=0)
        },
        last_update=datetime.utcnow(),
        status_message=f"Extracting data from {current_filename}... ({files_processed}/{total_files})"
    )

    await self.progress_repo.update_session_progress(session_id, progress)
```

#### Task 5: Update Session Status Flow
- **Description**: Update session status transitions to reflect new flow
- **Files to modify**:
  - `backend/src/models/session.py` (add "extracting" status if needed)
  - `backend/src/repositories/session_repository.py`
- **Dependencies**: Task 4
- **Estimated effort**: 15 minutes

**Status Flow:**
- OLD: `processing` → `completed`/`failed`
- NEW: `uploading` → `extracting` → `matching` → `completed`/`failed`

### Phase 3: Remove Shared Storage Infrastructure

#### Task 6: Remove TEMP_STORAGE_PATH Usage
- **Description**: Remove all references to TEMP_STORAGE_PATH since files are no longer saved
- **Files to modify**:
  - `backend/src/services/upload_service.py` (remove temp file methods)
  - `backend/src/config.py` (remove TEMP_STORAGE_PATH setting)
- **Dependencies**: Tasks 1-3 complete and tested
- **Estimated effort**: 20 minutes

#### Task 7: Remove Volume Mounts from Deployments
- **Description**: Remove shared-temp-storage volume mounts and TEMP_STORAGE_PATH env var
- **Files to modify**:
  - `deploy/k8s/backend-deployment.yaml`
  - `deploy/k8s/celery-worker-deployment.yaml`
  - `deploy/docker-compose.yml`
- **Dependencies**: Task 6
- **Estimated effort**: 15 minutes

#### Task 8: Delete Azure Files Resources
- **Description**: Clean up Azure Files storage account, PV, PVC, and secrets
- **Commands**:
```bash
# Delete Kubernetes resources
kubectl delete pvc credit-card-temp-pvc -n credit-card-processor
kubectl delete pv credit-card-temp-pv
kubectl delete secret azure-files-secret -n credit-card-processor

# Delete Azure Files share
az storage share delete --name credit-card-temp --account-name ccproctemp2025

# Optionally delete storage account if not needed for other purposes
az storage account delete --name ccproctemp2025 --resource-group rg_prod --yes
```
- **Dependencies**: Tasks 6-7 deployed and verified
- **Estimated effort**: 10 minutes

### Phase 4: Testing and Validation

#### Task 9: Test with Small PDF Files
- **Description**: Upload small PDFs (< 10MB) to verify extraction works in backend
- **Dependencies**: Tasks 1-5 complete
- **Estimated effort**: 15 minutes

**Validation:**
- Upload completes successfully
- Transactions appear in database immediately
- Progress shows "Extracting" phase
- Matching task queued after extraction
- No temp files created

#### Task 10: Test with Large PDF Files
- **Description**: Upload large PDFs (100-200MB) to verify memory handling
- **Dependencies**: Task 9 pass
- **Estimated effort**: 20 minutes

**Validation:**
- Backend handles large PDFs without OOM
- Memory usage monitored (should stay under limits)
- Multiple concurrent uploads don't cause issues
- Progress updates work for large files

#### Task 11: Load Testing
- **Description**: Test multiple concurrent uploads to verify backend can handle load
- **Dependencies**: Task 10 pass
- **Estimated effort**: 30 minutes

**Test Cases:**
- 3 concurrent uploads (small PDFs)
- 2 concurrent uploads (large PDFs)
- Mixed small and large uploads
- Monitor backend memory and CPU

### Phase 5: Cleanup and Documentation

#### Task 12: Update API Documentation
- **Description**: Update OpenAPI docs to reflect synchronous extraction
- **Files to modify**:
  - `backend/src/api/routes/upload.py` (docstrings)
- **Dependencies**: Tasks 1-11 complete
- **Estimated effort**: 10 minutes

#### Task 13: Update CLAUDE.md
- **Description**: Document the new extraction architecture in project guidelines
- **Files to modify**:
  - `CLAUDE.md`
- **Dependencies**: All tasks complete
- **Estimated effort**: 10 minutes

## Technical Design

### Current Flow (Problematic)
```
POST /api/upload
  ↓
Validate files
  ↓
Save to /app/shared-temp/session-{id}/
  ↓
Create session (status="processing")
  ↓
Queue celery task: process_session_task(session_id)
  ↓
Return 202 Accepted
---
[CELERY WORKER]
  ↓
Read PDFs from /app/shared-temp/
  ↓
Extract with pdfplumber (OOMKilled here!)
  ↓
Save transactions to DB
  ↓
Run matching
  ↓
Delete temp files
  ↓
Mark session complete
```

### New Flow (Optimized)
```
POST /api/upload (with progress streaming)
  ↓
Validate files
  ↓
Create session (status="extracting")
  ↓
FOR EACH PDF (streamed, not saved):
  ├─ Extract with pdfplumber (in-memory)
  ├─ Parse transactions
  ├─ Update progress via SSE
  └─ GC cleans up after each file
  ↓
Bulk insert all transactions to DB
  ↓
Update session (status="matching")
  ↓
Queue celery task: match_session_task(session_id)
  ↓
Return 200 OK (extraction complete!)
---
[CELERY WORKER]
  ↓
Load transactions from DB (lightweight)
  ↓
Run matching algorithm
  ↓
Save match results
  ↓
Mark session complete
```

### Key Differences

| Aspect | Old (Current) | New (Proposed) |
|--------|---------------|----------------|
| PDF Storage | Temp files on Azure Files | Not stored (in-memory only) |
| Extraction | Celery worker (async) | Backend (during upload) |
| Memory Risk | Celery worker OOMKilled | Backend handles sequentially |
| User Feedback | Delayed (background) | Immediate (during request) |
| Complexity | High (shared storage) | Low (database only) |
| Celery Payload | Session ID (finds files) | Session ID (loads from DB) |
| Infrastructure | PVC, PV, Secret, Storage Account | None needed |

## Code Changes

### Files to Modify

1. **`backend/src/services/upload_service.py`**
   - Remove: `_save_files_to_temp`, `_save_files_to_temp_with_progress`, `cleanup_temp_files`
   - Modify: `process_upload` to call extraction service inline
   - Add: `_update_extraction_progress` for real-time progress

2. **`backend/src/services/extraction_service.py`**
   - Add: `extract_from_upload_file(file: UploadFile, session_id: UUID)`
   - Add: `_extract_from_pdf_stream(pdf_stream: BytesIO, filename: str, session_id: UUID)`
   - Keep: Existing `_extract_transactions_from_pdf` logic (refactor to use stream)

3. **`backend/src/tasks.py`**
   - Add: `match_session_task(session_id: str)` - new lightweight task
   - Modify: `process_session_task` - mark as deprecated or remove
   - Add: `match_session_background(session_id: UUID)` - async matching logic

4. **`backend/src/api/routes/upload.py`**
   - Modify: Change from 202 Accepted to 200 OK (extraction completes synchronously)
   - Update: Docstrings to reflect new flow
   - Add: Timeout handling for very large PDFs (optional: defer to background if > 5 min)

5. **`backend/src/config.py`**
   - Remove: `TEMP_STORAGE_PATH` setting
   - Add: `MAX_EXTRACTION_TIME_SECONDS` (timeout for extraction)

### Files to Remove

1. **`deploy/k8s/shared-storage-pv.yaml`** - No longer needed
2. **`deploy/k8s/shared-storage-pvc.yaml`** - No longer needed

### Kubernetes Resources to Delete

```bash
# PersistentVolumeClaim
kubectl delete pvc credit-card-temp-pvc -n credit-card-processor

# PersistentVolume
kubectl delete pv credit-card-temp-pv

# Secret
kubectl delete secret azure-files-secret -n credit-card-processor
```

### Azure Resources to Delete

```bash
# File share
az storage share delete --name credit-card-temp --account-name ccproctemp2025

# Storage account (if no other uses)
az storage account delete --name ccproctemp2025 --resource-group rg_prod --yes
```

## Memory Considerations

### Backend Pod Memory
- **Current**: 512Mi request, 512Mi limit
- **Recommended**: 1Gi request, 2Gi limit (to handle concurrent uploads)
- **Rationale**: Processing 2-3 PDFs concurrently, each ~200MB, needs ~1.5Gi peak

### Celery Worker Memory
- **Current**: 512Mi request, 1Gi limit
- **New**: Can REDUCE to 256Mi request, 512Mi limit
- **Rationale**: Only matching logic, no PDF processing

### Memory Savings
- **Before**: 512Mi (backend) + 1Gi (celery) = 1.5Gi total
- **After**: 2Gi (backend) + 512Mi (celery) = 2.5Gi total
- **Net**: +1Gi total BUT celery is more stable, backend handles load better

## Error Handling

### Extraction Errors (Immediate Feedback)
```python
try:
    transactions, receipts = await extraction_service.extract_from_upload_file(file, session.id)
    if not transactions:
        raise HTTPException(
            status_code=400,
            detail=f"No transactions found in {file.filename}. Please verify it's a valid credit card statement."
        )
except PDFException as e:
    raise HTTPException(
        status_code=400,
        detail=f"Failed to read PDF {file.filename}: {str(e)}"
    )
```

### Timeout Handling (Optional Future Enhancement)
```python
# For very large PDFs, option to defer to background
if file_size > 100 * 1024 * 1024:  # > 100MB
    # Save to temp storage and process in background
    # Fallback to current architecture for edge cases
    ...
```

## Testing Strategy

### Unit Tests
1. **test_extract_from_upload_file**
   - Small PDF → transactions extracted
   - Invalid PDF → raises exception
   - Empty PDF → raises exception

2. **test_process_upload_with_extraction**
   - Uploads PDF → transactions in database
   - Progress updates called
   - Matching task queued

3. **test_match_session_task**
   - Session ID → loads transactions from DB
   - Runs matching
   - Updates session status

### Integration Tests
1. **test_e2e_upload_and_match**
   - Upload PDF via API
   - Verify transactions in DB
   - Verify matching task completes
   - Check final session status

2. **test_concurrent_uploads**
   - Multiple uploads simultaneously
   - All complete successfully
   - No resource contention

### Performance Tests
1. Small PDF (1MB, 10 pages) - Target: < 5 seconds
2. Medium PDF (50MB, 50 pages) - Target: < 30 seconds
3. Large PDF (200MB, 200 pages) - Target: < 2 minutes
4. 3 concurrent small PDFs - Target: < 10 seconds total

## Rollback Plan

If new architecture has issues:

1. **Revert code changes**:
```bash
git revert <commit-hash>
docker build -t iiusacr.azurecr.io/expense-backend:v1.0.12 .
docker push iiusacr.azurecr.io/expense-backend:v1.0.12
```

2. **Restore shared storage** (PV/PVC already exist, just need to mount):
```bash
kubectl apply -f deploy/k8s/backend-deployment.yaml  # Old version
kubectl apply -f deploy/k8s/celery-worker-deployment.yaml  # Old version
```

3. **Keep Azure Files** until new architecture is proven stable

## Success Criteria

- [ ] Upload endpoint extracts PDFs synchronously
- [ ] Transactions saved to database during upload
- [ ] No temporary files created
- [ ] Extraction progress visible to user in real-time
- [ ] Extraction errors shown immediately (not in background)
- [ ] Matching task receives session ID only
- [ ] Celery worker loads transactions from database
- [ ] No OOMKilled errors with large PDFs
- [ ] Concurrent uploads work correctly
- [ ] Shared storage infrastructure removed
- [ ] Memory usage within limits (backend < 2Gi, celery < 512Mi)

## Migration Strategy

### Step 1: Implement New Code (Side-by-Side)
- Add new extraction methods
- Keep old code working
- Test new flow in dev environment

### Step 2: Deploy with Feature Flag (Optional)
- Add `USE_INLINE_EXTRACTION` environment variable
- Default to false (old flow)
- Test in production with flag enabled

### Step 3: Switch Over
- Set flag to true (new flow)
- Monitor for 24 hours
- Verify no issues

### Step 4: Cleanup
- Remove old code
- Delete shared storage resources
- Update documentation

## Dependencies and Libraries

**No new dependencies required!**
- Existing: pdfplumber 0.10.3
- Existing: FastAPI, SQLAlchemy, Celery

**Changes:**
- Use `io.BytesIO` for in-memory PDF processing
- Add proper memory cleanup (`del` statements, GC hints)

## Notes and Considerations

### Backend Request Timeout
- FastAPI/Uvicorn default timeout: 300s (5 minutes)
- For 184MB PDF (178 pages): Processing took ~30-60 seconds before OOM
- New architecture should complete within 2 minutes per PDF

### Database Transaction Size
- Bulk inserting 10k transactions from large PDF
- Ensure connection pool can handle it
- Consider batching if > 10k transactions

### Concurrent Upload Limits
- Backend currently has 2 workers (WORKERS=2)
- Each worker can handle 1 upload at a time
- Max concurrent: 2 uploads (consider increasing workers if needed)

### Progress Streaming
- Current SSE implementation supports real-time updates
- Extraction progress can be streamed to frontend
- Better UX than current "processing..." spinner

---

## Quick Reference: Implementation Checklist

### Code Changes
- [ ] upload_service.py - inline extraction
- [ ] extraction_service.py - extract_from_upload_file method
- [ ] tasks.py - match_session_task (lightweight)
- [ ] upload.py route - return 200 OK instead of 202
- [ ] Remove temp file methods
- [ ] Remove TEMP_STORAGE_PATH config

### Deployment Changes
- [ ] Remove volume mounts from backend-deployment.yaml
- [ ] Remove volume mounts from celery-worker-deployment.yaml
- [ ] Increase backend memory (1Gi → 2Gi)
- [ ] Reduce celery memory (1Gi → 512Mi)
- [ ] Update docker-compose.yml (remove shared volume)

### Infrastructure Cleanup
- [ ] Delete PVC credit-card-temp-pvc
- [ ] Delete PV credit-card-temp-pv
- [ ] Delete secret azure-files-secret
- [ ] Delete Azure Files share
- [ ] Delete storage account (optional)

### Testing
- [ ] Small PDF extraction
- [ ] Large PDF extraction
- [ ] Concurrent uploads
- [ ] Error handling (invalid PDF)
- [ ] Progress updates
- [ ] Matching task execution

---

*This plan addresses the architectural concern raised during shared storage testing. The shared storage implementation was successful, but revealed that storing PDFs is unnecessary and causes memory issues.*

**Recommendation:** Proceed with this refactor as the next phase to eliminate complexity and resolve the OOM issue.
