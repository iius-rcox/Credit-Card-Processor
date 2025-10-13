# Implementation Plan: Fix Processing Stuck Issue

## Overview
Diagnose and fix the critical bug causing uploaded sessions to remain stuck in "processing" status indefinitely. The root cause has been identified as a database constraint violation when attempting to transition session status to "matching" - a status value not included in the valid status constraint.

## Requirements Summary
- Sessions stuck in "processing" status never complete
- Background Celery tasks appear to run but sessions don't update
- Users cannot download reports because sessions never reach "completed" status
- All uploads since the 007-actual-pdf-parsing feature merge are affected

## Research Findings

### Root Cause Analysis
**Primary Issue:** Database constraint violation causing silent failure

**Evidence:**
1. **Database Constraint** (`backend/src/models/session.py:174-177`):
   ```python
   CheckConstraint(
       "status IN ('processing', 'completed', 'failed', 'expired')",
       name="chk_sessions_status"
   )
   ```
   Only 4 statuses are allowed, but code tries to set "matching"

2. **Conflicting Status Update** (`backend/src/services/extraction_service.py:698-699`):
   ```python
   # Update status to matching (next phase)
   await self.session_repo.update_session_status(session_id, "matching")
   ```
   This line attempts to set an invalid status value

3. **Empty Matching Phase** (`backend/src/services/upload_service.py:558-563`):
   ```python
   if matching_service:
       logger.info(f"Starting matching phase for session {session_id}")
       # TODO: Implement matching with progress tracking
       pass  # Does nothing!
   ```

### Best Practices
- Database constraints must match application logic
- Status transitions should be validated at the application layer before database commits
- Background tasks should have comprehensive error handling and logging
- Status transitions should follow a clear state machine pattern

### Reference Implementations
- Session status management pattern similar to job queue systems (pending → running → completed/failed)
- FastAPI + Celery + SQLAlchemy async pattern is correctly implemented
- Progress tracking infrastructure is in place but status transitions are broken

### Technology Decisions
- **Alembic migration** required to update database constraint
- **Remove invalid status transition** as immediate fix (minimal code change)
- **Add proper status values** for long-term solution
- **Keep existing Celery + Redis architecture** (working correctly)

## Implementation Tasks

### Phase 1: Immediate Hotfix (Critical Priority)

#### Task 1: Remove Invalid Status Transition
- **Description**: Comment out or remove the line that attempts to set status to "matching", which violates the database constraint and causes sessions to get stuck.
- **Files to modify**:
  - `backend/src/services/extraction_service.py` (line 698-699)
- **Dependencies**: None
- **Estimated effort**: 5 minutes

**Changes:**
```python
# Line 698-699: Remove or comment out
# BEFORE:
# Update status to matching (next phase)
await self.session_repo.update_session_status(session_id, "matching")

# AFTER:
# Note: Keeping status as "processing" until completion
# Matching phase status removed due to constraint violation
# Will be re-added after database migration completes
```

#### Task 2: Verify Session Repository Status Update Logic
- **Description**: Check that `update_session_status()` doesn't have additional logic that could fail silently. Add defensive validation if needed.
- **Files to check**:
  - `backend/src/repositories/session_repository.py`
- **Dependencies**: None
- **Estimated effort**: 10 minutes

#### Task 3: Test Immediate Fix Locally
- **Description**: Test that sessions now complete successfully with the status transition removed
- **Files to test**: Upload workflow end-to-end
- **Dependencies**: Task 1 complete
- **Estimated effort**: 15 minutes

**Test Plan:**
```bash
# 1. Restart backend and celery worker
cd deploy
docker-compose restart backend celery-worker

# 2. Upload test PDF via frontend or API
# 3. Monitor logs:
docker logs credit-card-backend --follow
docker logs credit-card-celery-worker --follow

# 4. Verify session completes:
# Check database: SELECT id, status, updated_at FROM sessions ORDER BY created_at DESC LIMIT 5;
```

### Phase 2: Proper Database Schema Fix

#### Task 4: Update Session Model Constraint
- **Description**: Add "extracting", "matching", and any other intermediate statuses to the valid status constraint
- **Files to modify**:
  - `backend/src/models/session.py` (line 174-177)
- **Dependencies**: Phase 1 tested and working
- **Estimated effort**: 10 minutes

**Changes:**
```python
# BEFORE:
CheckConstraint(
    "status IN ('processing', 'completed', 'failed', 'expired')",
    name="chk_sessions_status"
),

# AFTER:
CheckConstraint(
    "status IN ('processing', 'extracting', 'matching', 'completed', 'failed', 'expired')",
    name="chk_sessions_status"
),
```

#### Task 5: Create Alembic Migration
- **Description**: Generate and verify Alembic migration to update the database constraint
- **Files to create**:
  - New migration in `backend/migrations/versions/`
- **Dependencies**: Task 4 complete
- **Estimated effort**: 15 minutes

**Commands:**
```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "Add extracting and matching to session status constraint"

# Review generated migration
# Edit if needed to ensure it properly drops and recreates the constraint

# Apply migration locally
alembic upgrade head
```

#### Task 6: Test Migration on Local Database
- **Description**: Verify migration runs successfully and doesn't break existing sessions
- **Files to test**: Database schema
- **Dependencies**: Task 5 complete
- **Estimated effort**: 10 minutes

**Verification:**
```sql
-- Check constraint exists with new values
SELECT
    conname,
    pg_get_constraintdef(oid) as definition
FROM pg_constraint
WHERE conname = 'chk_sessions_status';

-- Verify existing sessions still valid
SELECT status, COUNT(*)
FROM sessions
GROUP BY status;
```

### Phase 3: Re-enable Status Transitions

#### Task 7: Restore Status Transition to "matching"
- **Description**: Uncomment/restore the status transition now that database supports it
- **Files to modify**:
  - `backend/src/services/extraction_service.py` (line 698-699)
- **Dependencies**: Task 6 complete (migration applied)
- **Estimated effort**: 5 minutes

**Changes:**
```python
# Restore with improved comment
# Update status to matching phase (next phase after extraction)
await self.session_repo.update_session_status(session_id, "matching")
```

#### Task 8: Add Status Validation Helper
- **Description**: Create a helper method to validate status transitions and prevent future constraint violations
- **Files to create/modify**:
  - `backend/src/models/session.py` - Add VALID_STATUSES constant and validation method
- **Dependencies**: Task 4 complete
- **Estimated effort**: 20 minutes

**Implementation:**
```python
# Add to session.py
class Session(Base):
    VALID_STATUSES = [
        'processing',
        'extracting',
        'matching',
        'completed',
        'failed',
        'expired'
    ]

    VALID_TRANSITIONS = {
        'processing': ['extracting', 'matching', 'completed', 'failed'],
        'extracting': ['matching', 'completed', 'failed'],
        'matching': ['completed', 'failed'],
        'completed': [],
        'failed': [],
        'expired': []
    }

    @classmethod
    def validate_status_transition(cls, from_status: str, to_status: str) -> bool:
        """Validate if status transition is allowed."""
        if to_status not in cls.VALID_STATUSES:
            raise ValueError(f"Invalid status: {to_status}")

        if from_status not in cls.VALID_STATUSES:
            raise ValueError(f"Invalid current status: {from_status}")

        if to_status not in cls.VALID_TRANSITIONS.get(from_status, []):
            logger.warning(
                f"Unusual status transition: {from_status} -> {to_status}"
            )
            return False

        return True
```

#### Task 9: Update Repository to Use Validation
- **Description**: Modify session repository to validate status transitions before updating
- **Files to modify**:
  - `backend/src/repositories/session_repository.py`
- **Dependencies**: Task 8 complete
- **Estimated effort**: 15 minutes

### Phase 4: Integration & Testing

#### Task 10: Comprehensive Integration Testing
- **Description**: Test complete upload → extraction → matching → completion workflow
- **Files to test**: Entire processing pipeline
- **Dependencies**: All previous tasks complete
- **Estimated effort**: 30 minutes

**Test Cases:**
1. Single PDF upload with valid transactions
2. Multiple PDF upload (2-3 files)
3. Large PDF (50+ pages, 500+ transactions)
4. Upload with incomplete employee data (test alias resolution)
5. Upload with credit transactions (negative amounts)
6. Concurrent uploads (2+ simultaneous sessions)
7. Error scenarios (invalid PDF, corrupted file)

#### Task 11: Fix Unstuck Sessions in Database
- **Description**: Update any existing stuck sessions to proper status
- **Files involved**: Database only
- **Dependencies**: Migration applied (Task 6)
- **Estimated effort**: 10 minutes

**Cleanup Script:**
```sql
-- Find stuck sessions (processing for > 10 minutes)
SELECT
    id,
    status,
    created_at,
    updated_at,
    NOW() - updated_at as stuck_duration
FROM sessions
WHERE status = 'processing'
  AND updated_at < NOW() - INTERVAL '10 minutes';

-- Option 1: Mark as failed (safe default)
UPDATE sessions
SET
    status = 'failed',
    updated_at = NOW()
WHERE status = 'processing'
  AND updated_at < NOW() - INTERVAL '10 minutes';

-- Option 2: Retry by resetting to processing (if files still exist)
-- This would require manual investigation per session
```

#### Task 12: Add Monitoring for Status Transitions
- **Description**: Add logging to track status transitions and catch future issues early
- **Files to modify**:
  - `backend/src/repositories/session_repository.py`
- **Dependencies**: None (can be done anytime)
- **Estimated effort**: 15 minutes

**Implementation:**
```python
async def update_session_status(self, session_id: UUID, new_status: str) -> None:
    """Update session status with validation and logging."""
    session = await self.get_session(session_id)
    old_status = session.status

    # Log transition
    logger.info(
        f"Session {session_id} status transition: {old_status} -> {new_status}"
    )

    # Validate transition (optional: use Task 8's validation)
    if hasattr(Session, 'validate_status_transition'):
        Session.validate_status_transition(old_status, new_status)

    # Update
    session.status = new_status
    session.updated_at = datetime.utcnow()
    await self.db.commit()

    logger.info(f"Session {session_id} status updated successfully to {new_status}")
```

### Phase 5: Deployment & Verification

#### Task 13: Deploy to Development Environment
- **Description**: Deploy fixes to dev environment and verify
- **Files involved**: Docker containers, K8s deployments
- **Dependencies**: All tasks in Phases 1-4 complete
- **Estimated effort**: 20 minutes

**Deployment Steps:**
```bash
# 1. Build new images
cd backend
docker build -t iiusacr.azurecr.io/expense-backend:v1.0.X .

# 2. Push to ACR
az acr login --name iiusacr
docker push iiusacr.azurecr.io/expense-backend:v1.0.X

# 3. Update K8s deployments
kubectl set image deployment/backend \
  backend=iiusacr.azurecr.io/expense-backend:v1.0.X \
  -n credit-card-processor

kubectl set image deployment/celery-worker \
  celery-worker=iiusacr.azurecr.io/expense-backend:v1.0.X \
  -n credit-card-processor

# 4. Run migration
kubectl exec -it deployment/backend -n credit-card-processor -- \
  alembic upgrade head
```

#### Task 14: Production Smoke Tests
- **Description**: Verify fixes work in production with test uploads
- **Dependencies**: Task 13 complete
- **Estimated effort**: 15 minutes

**Test Plan:**
1. Upload single test PDF
2. Monitor session status transitions
3. Verify completion and report download
4. Check logs for any errors

#### Task 15: Documentation Update
- **Description**: Update PROJECT_ARCHITECTURE.md and CLAUDE.md with status flow changes
- **Files to modify**:
  - `PROJECT_ARCHITECTURE.md`
  - `CLAUDE.md`
- **Dependencies**: All fixes verified working
- **Estimated effort**: 15 minutes

## Codebase Integration Points

### Files to Modify

1. **`backend/src/services/extraction_service.py`**
   - **Line 698-699**: Remove/restore status transition to "matching"
   - **Impact**: Critical - fixes immediate stuck session issue

2. **`backend/src/models/session.py`**
   - **Line 174-177**: Update status constraint
   - **Add**: VALID_STATUSES constant and validation method
   - **Impact**: Medium - enables proper status transitions

3. **`backend/src/repositories/session_repository.py`**
   - **Modify**: `update_session_status()` method
   - **Add**: Status validation and comprehensive logging
   - **Impact**: Medium - prevents future constraint violations

### New Files to Create

1. **`backend/migrations/versions/YYYYMMDD_HHMM_add_extracting_matching_statuses.py`**
   - Purpose: Alembic migration to update database constraint
   - Generated via: `alembic revision --autogenerate`

### Existing Patterns to Follow

1. **Migration Pattern**: Follow existing Alembic migration structure in `backend/migrations/versions/`
2. **Status Update Pattern**: Use existing repository pattern with async/await
3. **Error Handling**: Follow existing try/except with logging pattern in upload_service.py
4. **Validation Pattern**: Similar to Pydantic validation in schemas

## Technical Design

### Status State Machine

```
┌─────────────┐
│  processing │ (Initial upload state)
└──────┬──────┘
       │
       ├─────────> extracting (PDF text extraction phase)
       │
       └─────────> matching (Transaction matching phase)
                   │
                   ├─────> completed (Success!)
                   │
                   └─────> failed (Error occurred)

expired (Auto-cleanup after 90 days)
```

### Data Flow

```
1. User uploads PDFs
   ↓
2. FastAPI creates session (status: "processing")
   ↓
3. Celery task dispatched
   ↓
4. ExtractionService processes PDFs
   ├─ (CURRENT BUG) Tries to set status="matching" → CONSTRAINT VIOLATION
   ├─ (FIX) Remove invalid transition OR update constraint
   └─ Continue to completion
   ↓
5. Mark session as "completed"
   ↓
6. User downloads report
```

### Database Schema Changes

**Before (Current - BROKEN):**
```sql
CONSTRAINT chk_sessions_status CHECK (
    status IN ('processing', 'completed', 'failed', 'expired')
)
```

**After (Fixed):**
```sql
CONSTRAINT chk_sessions_status CHECK (
    status IN ('processing', 'extracting', 'matching', 'completed', 'failed', 'expired')
)
```

## Dependencies and Libraries

**No new dependencies required.** All fixes use existing libraries:
- SQLAlchemy 2.0+ (ORM and constraint management)
- Alembic 1.12+ (database migrations)
- asyncpg (PostgreSQL async driver)

## Testing Strategy

### Unit Tests
- Test `Session.validate_status_transition()` with all valid and invalid combinations
- Test `SessionRepository.update_session_status()` with validation
- Mock database to test constraint violation handling

### Integration Tests
- Test complete upload workflow (upload → extract → match → complete)
- Test error scenarios (invalid status, missing files, extraction failures)
- Test concurrent uploads with status transitions

### Edge Cases to Cover
1. Session stuck in "processing" for >10 minutes
2. Celery worker restart during processing
3. Database connection loss during status update
4. Concurrent status updates (race conditions)
5. Invalid status values passed to repository
6. Migration rollback scenario

### Manual Testing Checklist
- [ ] Single PDF upload completes successfully
- [ ] Multiple PDF upload completes successfully
- [ ] Large PDF (500+ transactions) completes
- [ ] Session with incomplete data completes (with incomplete flags)
- [ ] Session with credit transactions completes
- [ ] Concurrent uploads (2+ sessions) all complete
- [ ] Error handling: Invalid PDF marked as "failed"
- [ ] Status transitions logged correctly
- [ ] Report download works after completion
- [ ] Old stuck sessions cleaned up or marked failed

## Success Criteria

- [x] Root cause identified (database constraint violation)
- [ ] Immediate fix applied (invalid status transition removed)
- [ ] Sessions complete successfully in local testing
- [ ] Database migration created and tested
- [ ] Status validation helper implemented
- [ ] All integration tests passing
- [ ] No sessions stuck in "processing" for >10 minutes
- [ ] Deployed to production and verified with test uploads
- [ ] Documentation updated with new status flow
- [ ] Existing stuck sessions cleaned up in database

## Notes and Considerations

### Why This Bug Wasn't Caught Earlier
1. **Silent Failure**: Database constraint violations were caught by exception handlers but not properly logged
2. **Recent Change**: Introduced in 007-actual-pdf-parsing merge (commit b882629)
3. **Dev Environment**: May have been masked by development environment differences
4. **Celery Async**: Background task failures don't immediately surface to frontend

### Potential Challenges
1. **Production Migration**: Running Alembic migration in production AKS requires careful coordination
2. **Stuck Sessions**: Need to decide whether to retry or mark as failed
3. **Status Rollback**: If matching phase is empty (TODO comment), should we skip the "matching" status entirely?

### Future Enhancements
1. **Status Machine Library**: Consider using a formal state machine library (e.g., python-statemachine)
2. **Progress Tracking**: Align progress phases with status values
3. **Retry Logic**: Implement automatic retry for failed sessions
4. **Monitoring**: Add Prometheus metrics for status transitions
5. **Matching Implementation**: Complete the matching service (currently just `pass`)

### Alternative Approaches Considered

#### Approach 1: Remove All Intermediate Statuses (Rejected)
- **Pros**: Simpler, no migration needed
- **Cons**: Loses visibility into processing phases, harder to debug

#### Approach 2: Use Separate "phase" Column (Rejected)
- **Pros**: Status stays "processing", phases tracked separately
- **Cons**: Requires schema change, more complex than fixing constraint

#### Approach 3: Use JSONB for Flexible Status (Rejected)
- **Pros**: No constraint issues, infinitely flexible
- **Cons**: Loses database-level validation, query complexity

**Selected Approach**: Fix the constraint to match application logic (most straightforward, maintains existing patterns)

---

## Quick Reference: Files and Line Numbers

**Critical Files:**
- `backend/src/services/extraction_service.py:698-699` - Remove invalid status transition (IMMEDIATE FIX)
- `backend/src/models/session.py:174-177` - Update status constraint (PROPER FIX)
- `backend/src/services/upload_service.py:558-563` - Empty matching phase (TODO)
- `backend/src/repositories/session_repository.py` - Add status validation

**Supporting Files:**
- `backend/src/tasks.py:25-69` - Celery task definition (working correctly)
- `backend/src/api/routes/upload.py:73-88` - Task dispatch (working correctly)
- `backend/src/celery_app.py` - Celery configuration (working correctly)

---

*This plan is ready for execution with `/execute-plan PRPs/fix-processing-stuck-issue.md`*
