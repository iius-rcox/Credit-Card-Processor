# Test Validation Guide - Feature 005

**Purpose**: Validate the backend implementation before proceeding with frontend and deployment.

**Status**: Backend complete (47/72 tasks), ready for testing.

---

## 🧪 Test Execution

### Prerequisites

1. **Install Dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Verify Installation**
   ```bash
   python -c "import pytest, httpx, sqlalchemy; print('✓ Dependencies OK')"
   ```

### Option 1: Quick Contract Tests (Recommended)

Run just the contract tests to validate API behavior:

```bash
cd backend
chmod +x run_contract_tests.sh
./run_contract_tests.sh
```

**Expected Output**: All tests should pass (or fail with clear reasons if there are issues)

### Option 2: Complete Test Suite

Run all available tests:

```bash
cd backend
chmod +x run_all_tests.sh
./run_all_tests.sh
```

### Option 3: Manual Test Execution

Run specific test files:

```bash
cd backend

# Single test file
pytest tests/contract/test_upload_contract.py -v

# All contract tests
pytest tests/contract/ -v -m contract

# With detailed output
pytest tests/contract/ -vv --tb=long

# Stop on first failure
pytest tests/contract/ -x
```

---

## 📊 Understanding Test Results

### Success Indicators

✅ **All tests pass**: Backend implementation matches contracts
✅ **Green output**: No failures or errors
✅ **Exit code 0**: Tests completed successfully

### Common Issues

❌ **ImportError**: Missing dependencies → Run `pip install -r requirements.txt`
❌ **Database errors**: SQLite not configured → Check conftest.py
❌ **404 errors**: Endpoints not registered → Check main.py router includes
❌ **422 errors**: Schema validation failing → Check API schemas

---

## 🔍 Test Coverage Breakdown

### Contract Tests (40 test cases)

#### `test_upload_contract.py` (7 tests)
- ✓ Valid PDF file upload
- ✓ File size validation (10MB limit)
- ✓ File count validation (100 files max)
- ✓ File type validation (PDFs only)
- ✓ No files rejection
- ✓ Response schema validation
- ✓ Status code validation (202 Accepted)

#### `test_sessions_list_contract.py` (8 tests)
- ✓ Default pagination (page=1, page_size=50)
- ✓ Custom pagination parameters
- ✓ 90-day window filtering
- ✓ Empty result handling
- ✓ Response schema validation
- ✓ Invalid page parameter handling
- ✓ Page size limit (max 100)

#### `test_session_detail_contract.py` (7 tests)
- ✓ Valid session ID retrieval
- ✓ 404 for non-existent session
- ✓ 422 for invalid UUID
- ✓ Expired session handling
- ✓ Response schema with nested data
- ✓ Relationship inclusion (employees, transactions, receipts, matches)

#### `test_report_contract.py` (10 tests)
- ✓ XLSX format download
- ✓ CSV format download
- ✓ Default format (xlsx)
- ✓ Invalid format rejection
- ✓ 404 for non-existent session
- ✓ Invalid UUID handling
- ✓ Streaming response support
- ✓ Filename format validation
- ✓ Both formats available

#### `test_delete_contract.py` (8 tests)
- ✓ Successful deletion (204 No Content)
- ✓ 404 for non-existent session
- ✓ Invalid UUID handling
- ✓ Cascade deletion verification
- ✓ Idempotency (second delete returns 404)
- ✓ Verification after deletion
- ✓ No content body on success
- ✓ Method validation (405 for PUT/PATCH)

---

## 📝 Test Results Locations

After running tests, results are saved in:

```
backend/test_results/
├── contract_tests.log       # Full test output
├── contract_tests.xml       # JUnit XML format
├── contract_tests.html      # HTML report (if pytest-html installed)
├── contract.xml             # Contract tests only
├── integration.xml          # Integration tests (when implemented)
└── unit.xml                 # Unit tests (when implemented)
```

**View HTML Report**:
```bash
open test_results/contract_tests.html  # macOS
xdg-open test_results/contract_tests.html  # Linux
```

---

## 🐛 Debugging Failed Tests

### Step 1: Identify the Failure

Look for lines with `FAILED` in the output:

```
FAILED tests/contract/test_upload_contract.py::test_upload_valid_pdf_files - AssertionError
```

### Step 2: Read the Traceback

The test output shows:
- **What was expected**: `assert response.status_code == 202`
- **What was received**: `response.status_code = 500`
- **Error details**: Exception messages, stack traces

### Step 3: Run Single Test with Verbose Output

```bash
pytest tests/contract/test_upload_contract.py::test_upload_valid_pdf_files -vv --tb=long
```

### Step 4: Check Common Issues

1. **Database not configured**: Check `conftest.py` fixture setup
2. **Routes not registered**: Verify `main.py` includes all routers
3. **Dependency injection failing**: Check `dependencies.py`
4. **Schema mismatch**: Compare `schemas.py` with test expectations
5. **Missing imports**: Check for circular imports or missing modules

### Step 5: Add Debug Logging

Temporarily add print statements in the test:

```python
response = await client.post("/api/upload", files=files)
print(f"Status: {response.status_code}")
print(f"Body: {response.json()}")
assert response.status_code == 202
```

---

## ✅ Validation Checklist

Before proceeding to frontend/deployment, verify:

- [ ] All 40 contract tests pass
- [ ] No import errors or dependency issues
- [ ] Test execution completes in reasonable time (<30 seconds)
- [ ] Test results saved to `test_results/`
- [ ] HTML report generated (if pytest-html installed)
- [ ] No warnings about deprecated features
- [ ] Database fixtures working correctly
- [ ] Async tests executing properly

---

## 🚀 Next Steps After Validation

### If All Tests Pass ✅

**Option A: Continue with Frontend**
- Implement upload page (T043-T047)
- Create UI components
- Integrate with backend API

**Option B: Deploy to Development**
- Test with Docker Compose
- Verify local environment
- Prepare for Kubernetes deployment

**Option C: Add More Tests**
- Write integration tests (T058-T066)
- Add unit tests for services (T067-T069)
- Improve test coverage

### If Tests Fail ❌

**Priority 1: Fix Critical Failures**
- 500 errors indicate server issues
- 404 errors suggest routing problems
- Fix these before proceeding

**Priority 2: Fix Validation Failures**
- Schema mismatches
- Response format issues
- Header validation problems

**Priority 3: Improve Test Coverage**
- Add missing test cases
- Handle edge cases
- Improve error scenarios

---

## 📞 Support

### Test Failures

If tests fail unexpectedly:

1. Check the full error in `test_results/contract_tests.log`
2. Review the specific test file that failed
3. Compare expected vs actual behavior
4. Check backend implementation in corresponding route file

### Environment Issues

If setup fails:

1. Verify Python version: `python --version` (need 3.11+)
2. Check dependencies: `pip list | grep -E "(pytest|httpx|sqlalchemy)"`
3. Try clean install: `pip install -r requirements.txt --force-reinstall`

---

## 📈 Test Metrics

**Target Coverage**:
- Contract Tests: 100% of API endpoints ✅ (5/5 endpoints covered)
- Integration Tests: 0% (not yet implemented)
- Unit Tests: 0% (not yet implemented)

**Current Status**:
- **40 contract test cases** covering all 5 API endpoints
- **~4,000 lines of code** to test (backend)
- **Expected test runtime**: <30 seconds

---

**Last Updated**: 2025-10-06
**Feature**: 005-lean-internal-deployment
**Phase**: Validation (between development and deployment)
