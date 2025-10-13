# Debug Tasks: Production Transaction Persistence Issue

**Issue**: Transactions are extracted locally (1,518 from test PDF) but not persisted in production database (0 transactions)
**Status**: Core extraction logic works, issue is in production data flow
**Date**: 2025-10-13

---

## Diagnostic Task List

### Phase 1: Verify Extraction is Happening (Data Collection)

- [ ] **Task 1.1**: Add debug logging to ExtractionService._extract_credit_transactions()
  - **File**: `backend/src/services/extraction_service.py`
  - **Action**: Add `logger.info(f"Extracted {len(transactions)} transactions")` before return
  - **Action**: Add `logger.info(f"First transaction: {transactions[0] if transactions else 'None'}")`
  - **Purpose**: Confirm extraction is actually happening in production

- [ ] **Task 1.2**: Add debug logging to TransactionRepository.bulk_create_transactions()
  - **File**: `backend/src/repositories/transaction_repository.py`
  - **Action**: Add `logger.info(f"Bulk inserting {len(transactions)} transactions")`
  - **Action**: Add `logger.info(f"First transaction data: {transactions[0] if transactions else 'None'}")`
  - **Purpose**: Verify data is reaching the repository layer

- [ ] **Task 1.3**: Add exception logging around bulk insert
  - **File**: `backend/src/repositories/transaction_repository.py`
  - **Action**: Wrap bulk_insert_mappings in try/except with explicit logging
  - **Action**: Log any IntegrityError, DatabaseError, or generic exceptions
  - **Purpose**: Catch silent failures in bulk insert operation

- [ ] **Task 1.4**: Deploy debug version and test
  - **Command**: `./deploy/deploy-all.sh v1.0.5-debug v1.0.5-debug`
  - **Action**: Wait for rollout to complete
  - **Purpose**: Get new logging in production

- [ ] **Task 1.5**: Upload PDF and capture logs
  - **Tool**: Chrome DevTools to upload PDF
  - **Action**: Upload test PDF and click Process Reports
  - **Command**: `kubectl logs -n credit-card-processor celery-worker-[pod] --follow`
  - **Purpose**: Watch logs in real-time during extraction

### Phase 2: Verify Database Schema Compatibility

- [ ] **Task 2.1**: Check transactions table schema in production
  - **Command**: `kubectl exec postgres-0 -- psql -U ccprocessor -d credit_card_db -c "\d transactions"`
  - **Action**: Verify incomplete_flag and is_credit columns exist
  - **Purpose**: Ensure migration was fully applied

- [ ] **Task 2.2**: Test manual transaction insert
  - **Command**: Via psql, manually INSERT a transaction with incomplete_flag and is_credit
  - **Purpose**: Verify database accepts the new columns and data format

- [ ] **Task 2.3**: Check for database constraints that might reject data
  - **Command**: Query pg_constraint for transactions table
  - **Action**: Look for CHECK constraints or triggers that might reject data
  - **Purpose**: Identify silent constraint violations

### Phase 3: Verify Data Flow in Upload Service

- [ ] **Task 3.1**: Check if extract_transactions is being called
  - **File**: `backend/src/services/extraction_service.py` (extract_transactions method)
  - **Action**: Add logging at start: `logger.info(f"Extracting transactions from {pdf_path}")`
  - **Purpose**: Verify the main extraction method is being invoked

- [ ] **Task 3.2**: Verify transaction data structure matches repository expectations
  - **File**: `backend/src/services/extraction_service.py`
  - **Action**: Log the structure of transaction dict before return
  - **Action**: Compare with Transaction model fields
  - **Purpose**: Ensure data structure compatibility

- [ ] **Task 3.3**: Check if session_id is being added correctly
  - **File**: `backend/src/services/extraction_service.py` (extract_transactions method)
  - **Action**: Verify `transaction["session_id"] = session_id` is executed
  - **Action**: Log session_id value
  - **Purpose**: Ensure transactions are linked to correct session

### Phase 4: Check Bulk Insert Implementation

- [ ] **Task 4.1**: Verify bulk_insert_mappings is using correct syntax
  - **File**: `backend/src/repositories/transaction_repository.py`
  - **Current**: `await self.db.run_sync(lambda session: session.bulk_insert_mappings(Transaction, transactions))`
  - **Action**: Check if Transaction model class is correctly referenced
  - **Purpose**: Ensure bulk insert call is correct

- [ ] **Task 4.2**: Test if transactions list is empty
  - **File**: `backend/src/repositories/transaction_repository.py`
  - **Action**: Add `if not transactions: logger.warning("No transactions to insert!")`
  - **Purpose**: Catch empty list being passed to bulk insert

- [ ] **Task 4.3**: Verify commit is happening
  - **File**: Repository or service layer
  - **Action**: Add logging after `await self.db.flush()` or `await self.db.commit()`
  - **Purpose**: Ensure database transaction is being committed

### Phase 5: Check Employee/Session Creation

- [ ] **Task 5.1**: Verify employees are being created
  - **Command**: `kubectl exec postgres-0 -- psql -U ccprocessor -d credit_card_db -c "SELECT COUNT(*) FROM employees WHERE session_id = '[session_id]'"`
  - **Purpose**: Check if employee records exist (transactions need employee_id as FK)

- [ ] **Task 5.2**: Check if missing employee_id causes FK violation
  - **Issue**: All transactions have employee_id = None (employee not in DB)
  - **Action**: Check if FK constraint is rejecting inserts with NULL employee_id
  - **Solution**: Make employee_id nullable OR create employee record first

- [ ] **Task 5.3**: Review Transaction model FK constraints
  - **File**: `backend/src/models/transaction.py`
  - **Check**: Is `employee_id` nullable? Current shows `nullable=False`
  - **Fix**: Change to `nullable=True` to allow transactions with unresolved employees
  - **Deploy**: After fix

### Phase 6: Alternative Testing Approaches

- [ ] **Task 6.1**: Create minimal test endpoint
  - **File**: Create `backend/src/api/routes/debug.py`
  - **Endpoint**: POST /api/debug/extract - accepts PDF, returns extracted transaction count
  - **Purpose**: Test extraction WITHOUT going through Celery/upload workflow

- [ ] **Task 6.2**: Test extraction directly in Celery worker pod
  - **Command**: `kubectl exec celery-worker-[pod] -- python -c "[extraction code]"`
  - **Action**: Run extraction code directly in pod environment
  - **Purpose**: See if it's Celery-specific issue

- [ ] **Task 6.3**: Check Celery task code path
  - **File**: `backend/src/tasks.py` or wherever process_session is defined
  - **Action**: Verify it calls extraction_service.process_session_files_with_progress()
  - **Action**: Check if that calls extract_transactions() correctly
  - **Purpose**: Ensure data flows through correct code path

### Phase 7: Schema Fix (If FK Constraint is the Issue)

- [ ] **Task 7.1**: Update Transaction model to make employee_id nullable
  - **File**: `backend/src/models/transaction.py`
  - **Change**: `employee_id: Mapped[UUID]` → `employee_id: Mapped[Optional[UUID]]`
  - **Change**: `nullable=False` → `nullable=True`
  - **Reason**: Allow transactions with unresolved employee names

- [ ] **Task 7.2**: Create Alembic migration for nullable employee_id
  - **Command**: `alembic revision -m "make_transaction_employee_id_nullable"`
  - **SQL**: `ALTER TABLE transactions ALTER COLUMN employee_id DROP NOT NULL;`

- [ ] **Task 7.3**: Apply migration to production
  - **Command**: `kubectl exec postgres-0 -- psql -U ccprocessor -d credit_card_db -c "ALTER TABLE transactions ALTER COLUMN employee_id DROP NOT NULL;"`

- [ ] **Task 7.4**: Deploy and re-test
  - **Version**: v1.0.6
  - **Test**: Upload PDF and verify transactions are saved

### Phase 8: Verification & Validation

- [ ] **Task 8.1**: Verify transactions in database after debug
  - **Command**: Query transactions table for latest session_id
  - **Check**: COUNT(*), incomplete_flag count, is_credit count
  - **Expected**: ~1,500 transactions from test PDF

- [ ] **Task 8.2**: Verify transaction data quality
  - **SQL**: SELECT * FROM transactions LIMIT 10
  - **Check**: Dates, amounts, merchants, expense_types populated
  - **Check**: incomplete_flag = true (expected - no employee match)
  - **Check**: is_credit flags (if negative amounts exist)

- [ ] **Task 8.3**: Test employee alias creation
  - **UI**: Navigate to /reconciliation/aliases page
  - **Action**: Create alias for "WILLIAMBURT" → existing employee
  - **Action**: Re-upload PDF
  - **Expected**: Transactions now have employee_id, incomplete_flag = false

- [ ] **Task 8.4**: Verify complete end-to-end workflow
  - Upload PDF → Extract → Create alias → Re-upload → Verify resolution
  - **Success Criteria**: Transactions linked to employee via alias

- [ ] **Task 8.5**: Performance validation
  - **Check**: Extraction time for 178-page PDF
  - **Expected**: < 10 seconds for extraction
  - **Expected**: < 30 seconds for bulk insert of ~1,500 transactions

---

## Quick Win Approach (Most Likely Fix)

### **HYPOTHESIS**: Employee FK Constraint Rejecting Inserts

**Evidence**:
- Local extraction works (no database inserts)
- Production extraction works (logs show success)
- But 0 transactions in database
- Transactions have employee_id = None (no employee match)
- Transaction model has `employee_id: Mapped[UUID]` with `nullable=False`

**Most Likely Cause**:
```python
# Current Transaction model
employee_id: Mapped[UUID] = mapped_column(
    PGUUID(as_uuid=True),
    ForeignKey("employees.id", ondelete="CASCADE"),
    nullable=False  # ← THIS PREVENTS NULL VALUES
)
```

When we try to bulk insert transactions with `employee_id = None`, the database rejects them due to NOT NULL constraint, but the error is being swallowed somewhere.

**Quick Fix Tasks**:

1. ✅ **Make employee_id nullable** in Transaction model
2. ✅ **Run migration** to ALTER TABLE
3. ✅ **Deploy v1.0.6**
4. ✅ **Re-test** - should now save 1,500+ transactions!

---

## Execution Priority

**HIGH PRIORITY** (Do First):
- Tasks 7.1, 7.2, 7.3, 7.4 (Make employee_id nullable)
- Task 8.1 (Verify transactions saved)

**MEDIUM PRIORITY** (If above doesn't fix it):
- Tasks 1.1-1.5 (Add debug logging)
- Tasks 3.1-3.3 (Verify data flow)

**LOW PRIORITY** (For deeper investigation):
- Tasks 2.x, 4.x, 6.x (Schema checks, alternative testing)

---

## Success Criteria

When debugging is complete, we should have:
- ✅ 1,500+ transactions in database from test PDF
- ✅ Dates, amounts, merchants extracted correctly
- ✅ incomplete_flag = true (employee not resolved yet)
- ✅ Employee alias workflow functional
- ✅ Production extraction working end-to-end

**Estimated Time**: 1-2 hours to complete all debug tasks and validate
