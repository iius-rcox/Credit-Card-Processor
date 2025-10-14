# Fix: Session Stuck on Processing (Matching Issue)

**Date:** 2025-10-14
**Issue:** Sessions were getting stuck on "processing" status after the PDF extraction refactor (008)
**Root Cause:** Duplicate/deprecated Celery tasks and undefined `temp_dir` reference

---

## Problem Analysis

After refactoring PDF extraction to run inline during upload (feature 008), sessions were getting stuck because:

1. **Old `process_session_task` still being called** - The upload route was calling the deprecated task which referenced removed `temp_dir` variable
2. **Duplicate task queueing** - Both old and new tasks were being queued for the same session
3. **NameError crashes** - Old task crashed with `NameError: name 'temp_dir' is not defined`

### Error Logs
```
[2025-10-14 02:51:57,854: ERROR] Background processing failed:
NameError: name 'temp_dir' is not defined
```

---

## Changes Made

### 1. Deprecated Old Function (`backend/src/services/upload_service.py`)
Replaced `process_session_background()` with a graceful deprecation stub that:
- Logs clear deprecation warning
- Fails the session gracefully
- Prevents `temp_dir` reference errors

**Before:** 160+ lines with temp storage logic
**After:** 30 lines graceful deprecation handler

### 2. Deprecated Old Task (`backend/src/tasks.py`)
Replaced `process_session_task()` with a deprecation stub that:
- Returns error immediately without calling deprecated function
- Logs clear warning about using wrong task
- Prevents crashes from old queued jobs

**Before:** Called `process_session_background()` → crash
**After:** Returns error immediately → no crash

### 3. Fixed Upload Route (`backend/src/api/routes/upload.py`)
Removed duplicate task queueing:
- **Removed:** Import and call to deprecated `process_session_task`
- **Kept:** `process_upload()` already queues `match_session_task` internally
- **Updated:** API documentation to reflect inline extraction flow

**Before:** Queued both old and new tasks
**After:** Only new `match_session_task` queued

---

## Testing

### Test Results
```bash
$ python test_matching.py

Testing Matching Workflow (Post-Refactor Fix)
============================================================

1. Uploading test-upload.pdf...
   Session ID: 5d472de8-906f-4c0d-b372-4fff8a4b7a9c
   Initial status: extracting

2. Polling for completion...
   Poll 1: status=completed

3. SUCCESS!
   Final status: completed
```

### Celery Logs Verification
```
[2025-10-14 03:55:08,397: INFO] ✓ CELERY TASK STARTED: match_session_task
[2025-10-14 03:55:08,461: INFO] Task tasks.match_session succeeded in 0.065s
```

**Confirmed:**
- ✅ Only `match_session_task` triggered (no deprecated task)
- ✅ Task completes successfully in < 0.1s
- ✅ Session transitions: `extracting` → `matching` → `completed`

---

## Current Task Flow (After Fix)

### Upload Flow
1. **Client uploads PDFs** → `POST /api/upload`
2. **Backend validates files** (count, size, type)
3. **Inline extraction** → `ExtractionService.extract_from_upload_file()`
4. **Status: extracting → matching**
5. **Queue matching task** → `match_session_task.delay(session_id)`
6. **Return session to client** (status='matching')

### Background Matching (Celery)
1. **Worker receives task** → `match_session_task`
2. **Load data from DB** (transactions + receipts already saved)
3. **Run matching algorithm** (placeholder for now)
4. **Update session** → status='completed'

**Total time:** < 2 seconds for small PDFs

---

## Deprecated Components (Still Present for Compatibility)

These functions/tasks are kept to prevent import errors but will fail gracefully if called:

- `process_session_background()` - Old extraction+matching function
- `process_session_task` - Old Celery task (kept as stub)

**Why keep them?**
- Prevents import errors in existing deployments
- Handles old queued jobs gracefully
- Clear deprecation warnings in logs

**Future cleanup:** Can be removed in a future major version after ensuring no old jobs remain in queue.

---

## Files Modified

```
backend/src/services/upload_service.py   | Deprecated process_session_background
backend/src/tasks.py                     | Deprecated process_session_task
backend/src/api/routes/upload.py         | Removed duplicate task call
test_matching.py                         | Created test script
docs/MATCHING_STUCK_FIX.md              | This document
```

---

## Maintenance Notes

### If Sessions Stuck Again
1. Check Celery logs: `docker logs credit-card-celery-worker --tail 100`
2. Look for: `match_session_task` started/completed messages
3. Verify no deprecated task calls in logs
4. Check session status: `GET /api/sessions/{session_id}`

### If Old Task Called
If you see deprecation warnings in Celery logs:
1. Purge old queue: `docker exec credit-card-celery-worker celery -A src.celery_app purge -f`
2. Restart worker: `docker restart credit-card-celery-worker`
3. Check code for old imports: `grep -r "process_session_task" src/`

---

## Related Documentation

- Feature 008 PRP: `PRPs/refactor-pdf-extraction-to-backend.md`
- Shared Storage Cleanup: `docs/AZURE_CLEANUP_COMMANDS.md`
- E2E Validation: `docs/E2E_VALIDATION_GUIDE.md`
