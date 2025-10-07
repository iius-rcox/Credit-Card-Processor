# Quick Start: Testing the Backend

**Time to test**: ~5 minutes

---

## 🚀 Fast Track (3 Commands)

```bash
# 1. Go to backend directory
cd /Users/rogercox/Credit-Card-Processor/backend

# 2. Install dependencies (if not already done)
pip install -r requirements.txt

# 3. Run contract tests
chmod +x run_contract_tests.sh && ./run_contract_tests.sh
```

**Expected Result**: Green checkmarks ✓ for all tests, or clear error messages if something needs fixing.

---

## 📊 What Gets Tested

Running the contract tests validates:

✅ **POST /api/upload** - File upload with validation (7 tests)
✅ **GET /api/sessions** - Pagination and filtering (8 tests)
✅ **GET /api/sessions/{id}** - Detail retrieval (7 tests)
✅ **GET /api/sessions/{id}/report** - Report generation (10 tests)
✅ **DELETE /api/sessions/{id}** - Deletion and cascade (8 tests)

**Total**: 40 test cases covering all API endpoints

---

## 🔍 Reading the Results

### ✅ Success Looks Like This:

```
tests/contract/test_upload_contract.py::test_upload_valid_pdf_files PASSED
tests/contract/test_upload_contract.py::test_upload_file_size_validation PASSED
...
✓ All contract tests passed!
```

### ❌ Failure Looks Like This:

```
FAILED tests/contract/test_upload_contract.py::test_upload_valid_pdf_files
AssertionError: assert 500 == 202
```

**What to do**: Check `backend/test_results/contract_tests.log` for details.

---

## 🐛 Common Issues & Fixes

### Issue 1: "ModuleNotFoundError: No module named 'pytest'"

**Fix**:
```bash
pip install -r requirements.txt
```

### Issue 2: "Database error" or "SQLAlchemy error"

**Fix**: The tests use in-memory SQLite, which should work automatically. If you see database errors, check that `conftest.py` exists in `backend/tests/`.

### Issue 3: "404 Not Found" errors

**Fix**: The backend routes might not be registered. This would indicate an issue with `main.py` router includes. Check the test output for which endpoint is failing.

### Issue 4: Tests taking too long

**Normal**: Tests should complete in under 30 seconds. If they take longer, there might be a timeout issue.

---

## 📁 Where Are the Results?

After running tests:

```
backend/test_results/
├── contract_tests.log      # Full output (read this for errors)
├── contract_tests.xml      # JUnit format
└── contract_tests.html     # Visual report (if pytest-html installed)
```

**View the log**:
```bash
cat backend/test_results/contract_tests.log
```

**View HTML report** (if available):
```bash
open backend/test_results/contract_tests.html
```

---

## ✅ After Tests Pass

Once all tests are green, you have three options:

### Option A: Test the Full System Locally

```bash
# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up -d

# Check backend health
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs
```

### Option B: Build the Frontend

Proceed to implement the frontend components (tasks T043-T047):
- Upload page
- Progress display
- Results panel

### Option C: Deploy to Kubernetes

Follow the deployment tasks (T048-T057):
- Build Docker images
- Deploy to AKS
- Configure ingress

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `./run_contract_tests.sh` | Run all contract tests |
| `./run_all_tests.sh` | Run contract + integration + unit tests |
| `pytest tests/contract/ -v` | Run contract tests (manual) |
| `pytest tests/contract/ -x` | Stop on first failure |
| `pytest tests/contract/ -k upload` | Run only upload tests |

---

## 💡 Pro Tips

1. **Run tests before committing**: Ensure nothing breaks
2. **Check the HTML report**: Visual summary is easier to read
3. **Test individual files**: Faster debugging with `-k` flag
4. **Use `-x` flag**: Stop on first failure to fix issues incrementally
5. **Read the log file**: Contains full error details

---

**Time Investment**: 5 minutes to run, 15-30 minutes to fix issues if any

**Next Step**: See [TEST_VALIDATION_GUIDE.md](TEST_VALIDATION_GUIDE.md) for comprehensive testing instructions.
