# Backend Testing Documentation

**Feature**: 005-lean-internal-deployment
**Test Coverage**: Contract tests (40 cases), Integration tests (pending), Unit tests (pending)

---

## 📁 Test Structure

```
backend/tests/
├── conftest.py                    # Shared fixtures and configuration
├── contract/                      # API contract tests (40 tests)
│   ├── __init__.py
│   ├── test_upload_contract.py    # 7 tests
│   ├── test_sessions_list_contract.py  # 8 tests
│   ├── test_session_detail_contract.py # 7 tests
│   ├── test_report_contract.py    # 10 tests
│   └── test_delete_contract.py    # 8 tests
├── integration/                   # End-to-end tests (not yet implemented)
│   └── __init__.py
└── unit/                         # Service unit tests (not yet implemented)
    └── __init__.py
```

---

## 🧪 Test Categories

### Contract Tests ✅ (Implemented)

**Purpose**: Validate API endpoint contracts (request/response schemas, status codes, validation)

**Coverage**: 5 endpoints × 8 average tests = 40 test cases

**Run**: `pytest tests/contract/ -v -m contract`

**What they test**:
- Request validation (file size, type, count)
- Response schemas (correct fields and types)
- Status codes (202, 200, 404, 422, etc.)
- Error handling (validation errors, not found, etc.)
- Edge cases (empty inputs, invalid formats)

### Integration Tests ⏳ (Pending - Tasks T058-T066)

**Purpose**: Test complete workflows end-to-end

**Planned Coverage**:
- Upload → Process → Results workflow
- Session retrieval and filtering
- 90-day expiration logic
- Report generation
- Database persistence

**Run**: `pytest tests/integration/ -v -m integration` (when implemented)

### Unit Tests ⏳ (Pending - Tasks T067-T069)

**Purpose**: Test individual service methods in isolation

**Planned Coverage**:
- ExtractionService methods
- MatchingService algorithms
- ReportService generation

**Run**: `pytest tests/unit/ -v -m unit` (when implemented)

---

## 🚀 Running Tests

### Quick Start

```bash
# Run all contract tests
./run_contract_tests.sh

# Or manually
pytest tests/contract/ -v
```

### Advanced Usage

```bash
# Run specific test file
pytest tests/contract/test_upload_contract.py -v

# Run specific test
pytest tests/contract/test_upload_contract.py::test_upload_valid_pdf_files -v

# Run tests matching pattern
pytest tests/contract/ -k "upload" -v

# Stop on first failure
pytest tests/contract/ -x

# Show detailed output
pytest tests/contract/ -vv --tb=long

# Run with coverage
pytest tests/contract/ --cov=src --cov-report=html
```

### Markers

Tests are organized with pytest markers:

```bash
# Run only contract tests
pytest -m contract

# Run only integration tests (when implemented)
pytest -m integration

# Run only unit tests (when implemented)
pytest -m unit

# Run slow tests
pytest -m slow
```

---

## 🔧 Test Fixtures

Located in `conftest.py`, provides:

### Database Fixtures

- `test_engine` - In-memory SQLite database
- `test_session` - Async database session
- `test_client` - HTTP client with DB override

**Usage**:
```python
@pytest.mark.asyncio
async def test_example(test_client):
    response = await test_client.get("/api/sessions")
    assert response.status_code == 200
```

### Sample Data Fixtures

- `sample_pdf_content` - Mock PDF file bytes
- `sample_session_data` - Session attributes
- `sample_employee_data` - Employee attributes
- `sample_transaction_data` - Transaction attributes
- `sample_receipt_data` - Receipt attributes
- `sample_match_result_data` - Match result attributes

**Usage**:
```python
def test_create_session(test_session, sample_session_data):
    session = Session(**sample_session_data)
    # test logic here
```

---

## 📊 Test Coverage

### Current Coverage (Contract Tests Only)

| Endpoint | Tests | Status |
|----------|-------|--------|
| POST /api/upload | 7 | ✅ |
| GET /api/sessions | 8 | ✅ |
| GET /api/sessions/{id} | 7 | ✅ |
| GET /api/sessions/{id}/report | 10 | ✅ |
| DELETE /api/sessions/{id} | 8 | ✅ |
| **Total** | **40** | **✅** |

### Target Coverage (When All Tests Implemented)

- Contract Tests: 40 tests ✅
- Integration Tests: ~9 tests (T058-T066)
- Unit Tests: ~15 tests (T067-T069)
- **Total Target**: ~64 test cases

---

## ✅ Test Quality Checklist

Each test should:

- [ ] Have a clear docstring describing what it tests
- [ ] Use descriptive test function names
- [ ] Test one specific behavior
- [ ] Include both happy path and error cases
- [ ] Use appropriate assertions
- [ ] Clean up after itself (fixtures handle this)
- [ ] Run independently (no dependencies on other tests)

---

## 🐛 Debugging Tests

### Enable Debug Logging

```bash
pytest tests/contract/ -v --log-cli-level=DEBUG
```

### Add Print Statements

```python
@pytest.mark.asyncio
async def test_example(test_client):
    response = await test_client.post("/api/upload", files=files)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.json()}")
    assert response.status_code == 202
```

### Run with PDB Debugger

```bash
pytest tests/contract/ --pdb
```

### Check Test Results

```bash
cat test_results/contract_tests.log
```

---

## 📈 Continuous Integration

### GitHub Actions (when configured)

```yaml
- name: Run Tests
  run: |
    cd backend
    pip install -r requirements.txt
    pytest tests/ -v --junitxml=test-results.xml
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
cd backend
pytest tests/contract/ -x
```

---

## 🔄 Test Development Workflow

### 1. Write Test (TDD Approach)

```python
@pytest.mark.asyncio
async def test_new_feature(test_client):
    response = await test_client.get("/api/new-endpoint")
    assert response.status_code == 200
```

### 2. Run Test (Should Fail)

```bash
pytest tests/contract/test_new_feature.py -v
# FAILED - endpoint doesn't exist yet
```

### 3. Implement Feature

```python
# src/api/routes/new_route.py
@router.get("/new-endpoint")
async def new_endpoint():
    return {"status": "ok"}
```

### 4. Run Test (Should Pass)

```bash
pytest tests/contract/test_new_feature.py -v
# PASSED ✓
```

---

## 📚 Further Reading

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Async Testing](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html#using-asyncio-with-tests)

---

**Maintained by**: Development Team
**Last Updated**: 2025-10-06
**Next Review**: After integration tests are implemented
