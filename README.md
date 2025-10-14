# Credit Card Expense Reconciliation System

Automated expense reconciliation system that matches credit card transactions with receipt reports, streamlining the expense approval process.

---

## 🎯 What This Does

The Credit Card Processor automatically reconciles employee credit card transactions with receipt submissions:

1. **Upload PDFs** - Upload credit card statements and receipt reports
2. **Automatic Extraction** - System extracts transaction data and receipt information
3. **Intelligent Matching** - Matches transactions with receipts based on date, amount, and merchant
4. **Generate Reports** - Creates reconciliation reports showing matched/unmatched items
5. **Track Compliance** - Identifies missing receipts and incomplete documentation

**Key Benefits:**
- ⚡ Processes 1000+ transactions in seconds
- 🎯 Reduces manual reconciliation time by 90%
- 📊 Provides detailed compliance tracking
- 🔍 Flags incomplete submissions automatically
- 📈 Exports to Excel/CSV for accounting systems

---

## 🏗️ Architecture

**Frontend:**
- Next.js 15 + React 19
- Real-time progress tracking with Server-Sent Events (SSE)
- Responsive UI with dark mode support

**Backend:**
- FastAPI (Python 3.11+)
- PostgreSQL database
- Celery for background task processing
- Redis for task queue and caching

**PDF Processing:**
- pdfplumber for text extraction
- Regex-based transaction parsing
- Employee alias resolution
- Inline extraction (no temporary storage)

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Run with Docker Compose

```bash
# Clone the repository
git clone <repository-url>
cd Credit-Card-Processor

# Start all services
cd deploy
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Local Development

**Backend:**
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn src.main:app --reload --port 8000
```

**Frontend:**
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
```

---

## 📋 How to Use

### 1. Upload PDFs

Upload two types of PDFs:
- **Cardholder Activity Report** - Credit card statement with all transactions
- **Receipt Report** - Scanned receipts for submitted expenses

**Supported Format:**
- WEX Fleet card format
- PDF text-based (not scanned images)
- Maximum 100 files, 300MB per file

### 2. Monitor Processing

The system processes uploads in phases:
1. **Extracting** - Parsing PDF text and extracting data
2. **Matching** - Matching transactions with receipts
3. **Completed** - Ready to view results

**Real-time progress:**
- Upload progress bar
- Current phase indicator
- File/page progress tracking

### 3. Review Results

**Reconciliation Summary:**
- Total employees processed
- Complete vs incomplete employees
- Missing receipts count
- Missing GL codes count

**Employee Details:**
- Transaction list per employee
- Match status for each transaction
- Missing receipt indicators
- Incomplete transaction flags

### 4. Export Reports

**Excel Report:**
- Complete reconciliation data
- Formatted for accounting review
- Includes all transaction details

**CSV Export:**
- Raw data export
- Compatible with accounting systems
- Easy to import into Excel/Google Sheets

---

## 🐛 Debugging PDF Extraction Issues

When PDFs don't extract correctly, use the built-in debug output feature.

### Enable Debug Mode

**Docker Compose:**
```bash
# Edit deploy/docker-compose.yml
backend:
  environment:
    DEBUG_EXTRACTION_OUTPUT: "true"
    DEBUG_OUTPUT_PATH: /app/debug_output
    ENVIRONMENT: development

# Restart backend
docker-compose restart backend
```

**Local Development:**
```bash
# Edit backend/.env
DEBUG_EXTRACTION_OUTPUT=true
DEBUG_OUTPUT_PATH=./debug_output
ENVIRONMENT=development

# Restart server
```

### Debug Output Files

When debug is enabled, 4 files are created per upload session:

**Text Extraction Files:**
1. `01_cardholder_text.txt` - Raw text from cardholder PDF
2. `02_receipt_text.txt` - Raw text from receipt PDF

**Regex Processing Files:**
3. `03_cardholder_regex_results.json` - Transaction parsing results + statistics
4. `04_receipt_regex_results.json` - Receipt parsing results + statistics

**File Location:**
```
backend/debug_output/
  <session-id>/
    20251014_061630_01_cardholder_text.txt
    20251014_061630_02_receipt_text.txt
    20251014_061630_03_cardholder_regex_results.json
    20251014_061630_04_receipt_regex_results.json
```

### Analyze Debug Files

**1. Check Raw Text Extraction:**
```bash
# View extracted text
cat backend/debug_output/<session-id>/*_01_cardholder_text.txt | head -50

# What to look for:
✓ Readable text (not garbled)
✓ "Cardholder Name:" header present
✓ Transaction lines with dates/amounts
✗ Empty or unreadable = scanned PDF (not supported)
```

**2. Check Regex Matching:**
```bash
# View JSON results
cat backend/debug_output/<session-id>/*_03_cardholder_regex_results.json | python -m json.tool

# Key metrics to check:
{
  "total_matches": 1518,           // Should be > 0
  "incomplete_count": 0,            // Low is good
  "extraction_stats": {
    "pattern_matches": 1518         // Should match transaction count
  },
  "match_statistics": {
    "successful_parses": 1518,      // High percentage = good
    "failed_parses": 0              // Low is good
  }
}
```

**3. Troubleshoot Extraction Issues:**

**No transactions extracted?**
- Check `sample_text` in JSON - does it contain expected data?
- Compare `regex_patterns.transaction` with `first_10_lines`
- Look for format differences (extra spaces, missing columns)

**Employee not found?**
- Check `employee_name_found` in JSON
- Verify "Cardholder Name:" appears in text file
- Add employee alias if name format differs

**Low match rate?**
- Compare `first_matched_line` with sample lines
- Check `match_statistics` for patterns
- Adjust regex in `backend/src/services/extraction_service.py`

**Complete Guide:** See `docs/DEBUGGING_GUIDE.md` for detailed troubleshooting workflow

### Disable Debug Mode

```bash
# Set flag to false
DEBUG_EXTRACTION_OUTPUT=false

# Restart backend
docker-compose restart backend

# Clean up debug files (optional)
rm -rf backend/debug_output/
```

**Important:** Debug is automatically disabled in production (even if flag is true)

---

## 🗄️ Database Schema

**Core Tables:**
- `sessions` - Upload sessions with status tracking
- `employees` - Employee records
- `employee_aliases` - Maps PDF names to employee records
- `transactions` - Credit card transactions (nullable employee_id)
- `receipts` - Receipt submissions
- `matchresults` - Transaction-receipt matches

**Key Features:**
- Nullable `employee_id` allows transactions with unknown employees
- `incomplete_flag` tracks data quality issues
- `is_credit` identifies refunds/credits (negative amounts)
- Bulk insert optimization for 10k+ transactions

---

## 🔄 Deployment

### Docker Compose (Development)

```bash
cd deploy
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

### Kubernetes (Production)

```bash
cd deploy

# Run database migrations
./run-migrations.sh

# Deploy all components
./deploy-all.sh v1.0.14 v1.0.14

# Check deployment
kubectl get pods -n credit-card-processor
kubectl get services -n credit-card-processor
```

**See full deployment guide:** `docs/DEPLOYMENT_GUIDE.md`

---

## 🧪 Testing

**Run Unit Tests:**
```bash
cd backend
python -m pytest tests/unit/ -v
```

**Run Integration Tests:**
```bash
python -m pytest tests/integration/ -v
```

**Test Coverage:**
```bash
python -m pytest --cov=src --cov-report=html
```

**Manual Testing:**
```bash
# Upload test
python test_matching.py

# With real PDFs via UI
# Navigate to http://localhost:3000
```

---

## 🛠️ Configuration

### Environment Variables

**Required:**
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=credit_card_db
POSTGRES_USER=ccprocessor
POSTGRES_PASSWORD=your-password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
```

**Optional:**
```bash
# Application
ENVIRONMENT=development         # development|production|test
LOG_LEVEL=DEBUG                # DEBUG|INFO|WARNING|ERROR
MAX_UPLOAD_SIZE_MB=300
MAX_UPLOAD_COUNT=100

# Debug (Development Only)
DEBUG_EXTRACTION_OUTPUT=true   # Enable debug file output
DEBUG_OUTPUT_PATH=./debug_output

# CORS
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
```

**See:** `backend/.env.example` for complete configuration template

---

## 📚 Documentation

**User Guides:**
- `docs/DEBUGGING_GUIDE.md` - PDF extraction debugging
- `docs/DEPLOYMENT_GUIDE.md` - Deployment instructions
- `docs/E2E_VALIDATION_GUIDE.md` - End-to-end testing

**Technical Documentation:**
- `PRPs/refactor-pdf-extraction-to-backend.md` - Architecture overview
- `docs/COMPLETE_FIX_SUMMARY.md` - Recent fixes and improvements
- `docs/MATCHING_STUCK_FIX.md` - Troubleshooting guide

**Feature Plans:**
- `PRPs/debug-extraction-output.md` - Debug feature implementation plan
- `specs/` - Feature specifications and design documents

---

## 🔧 Development

### Project Structure

```
Credit-Card-Processor/
├── backend/                    # FastAPI backend
│   ├── src/
│   │   ├── api/               # API routes
│   │   ├── models/            # SQLAlchemy models
│   │   ├── repositories/      # Data access layer
│   │   ├── services/          # Business logic
│   │   ├── utils/             # Utilities (including debug_writer)
│   │   └── tasks.py           # Celery tasks
│   ├── tests/                 # Test suite
│   ├── migrations/            # Alembic migrations
│   └── requirements.txt       # Python dependencies
│
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/               # Next.js app directory
│   │   ├── components/        # React components
│   │   └── services/          # API client services
│   └── package.json
│
├── deploy/                     # Deployment configuration
│   ├── docker-compose.yml     # Local development
│   ├── k8s/                   # Kubernetes manifests
│   ├── deploy-all.sh          # Full deployment script
│   └── run-migrations.sh      # Migration script
│
├── docs/                       # Documentation
├── PRPs/                       # Plans and proposals
└── specs/                      # Feature specifications
```

### Adding New Features

1. **Create Feature Branch:**
   ```bash
   .specify/scripts/bash/create-new-feature.sh --json "feature description"
   ```

2. **Implement Changes:**
   - Follow existing patterns in codebase
   - Add unit tests for new functionality
   - Update documentation

3. **Test Thoroughly:**
   ```bash
   python -m pytest tests/
   ```

4. **Commit and Deploy:**
   ```bash
   git add .
   git commit -m "Add feature: description"
   cd deploy && ./deploy-all.sh
   ```

---

## 🐛 Troubleshooting

### Common Issues

**Problem: Sessions stuck on "processing"**
- **Solution:** See `docs/MATCHING_STUCK_FIX.md`
- Check Celery worker logs: `docker logs credit-card-celery-worker`
- Verify only `match_session_task` is running (not deprecated tasks)

**Problem: PDF extraction fails**
- **Solution:** Enable debug output (see Debugging section above)
- Check if PDF is text-based (not scanned image)
- Verify PDF format matches expected structure
- Check `docs/DEBUGGING_GUIDE.md` for detailed troubleshooting

**Problem: Database constraint errors**
- **Solution:** Run migrations
  ```bash
  docker exec credit-card-backend alembic upgrade head
  ```
- Check `docs/DEPLOYMENT_GUIDE.md` for migration procedures

**Problem: Employee name not resolved**
- **Solution:** Add employee alias
  ```bash
  # Via UI: Navigate to /reconciliation/aliases
  # Or via API: POST /api/aliases
  ```
- See employee_aliases table documentation

### Getting Help

1. **Check Logs:**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f celery-worker
   ```

2. **Enable Debug Logging:**
   ```bash
   LOG_LEVEL=DEBUG
   ```

3. **Enable Debug File Output:**
   ```bash
   DEBUG_EXTRACTION_OUTPUT=true
   ```

4. **Review Documentation:**
   - `docs/` directory for guides
   - `PRPs/` for feature plans
   - GitHub issues for known problems

---

## 🔐 Security

**Production Safety:**
- Environment-based configuration
- Secret management via Azure Key Vault
- CORS protection
- Input validation and sanitization
- SQL injection prevention (SQLAlchemy ORM)
- Debug features auto-disabled in production

**Data Privacy:**
- Debug files only in development
- Temporary data automatically cleaned up
- Session expiration (90 days)
- Secure database connections

---

## 📊 Performance

**Typical Performance:**
- Small PDFs (100 transactions): < 2 seconds
- Large PDFs (1500+ transactions): 6-12 seconds
- Matching: < 0.1 seconds
- Export generation: 1-3 seconds

**Scalability:**
- Bulk insert optimization for 10k+ transactions
- Async database operations
- Background task processing
- Horizontal scaling ready (Kubernetes)

---

## 🤝 Contributing

### Development Workflow

1. Create feature branch
2. Implement changes following existing patterns
3. Add/update tests (maintain >80% coverage)
4. Update documentation
5. Test locally with Docker Compose
6. Create pull request

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Docstrings for all public methods
- Async/await for I/O operations

**TypeScript/React:**
- Follow React best practices
- Use TypeScript strict mode
- Component-based architecture
- Responsive design

### Testing Requirements

- Unit tests for business logic
- Integration tests for workflows
- Manual testing with real PDFs
- Chrome DevTools browser testing

---

## 📝 Recent Updates

**Feature 009 - Debug Extraction Output (2025-10-14):**
- Added debug file output for PDF extraction troubleshooting
- Outputs raw text and regex results to files
- Comprehensive debugging guide
- 100% test coverage

**Feature 008 - Refactor PDF Extraction (2025-10-13):**
- Inline PDF extraction during upload (no temp storage)
- Matching-only Celery tasks
- Improved error handling and status tracking

**Database Schema Fix (2025-10-14):**
- Made `employee_id` nullable in transactions table
- Allows transactions with unmapped employee names
- Added migration for schema sync

**Matching Workflow Fix (2025-10-14):**
- Fixed stuck sessions issue
- Deprecated old Celery tasks
- Streamlined task flow

---

## 📞 Support

**Documentation:**
- **User Guide:** `docs/DEBUGGING_GUIDE.md`
- **Deployment:** `docs/DEPLOYMENT_GUIDE.md`
- **Troubleshooting:** `docs/COMPLETE_FIX_SUMMARY.md`

**Technical Support:**
- Check GitHub Issues
- Review `docs/` directory
- Enable debug output for extraction issues
- Check Celery worker logs for background task issues

---

## 📄 License

[Your License Here]

---

## 🙏 Acknowledgments

Built with:
- FastAPI - Modern Python web framework
- Next.js - React framework
- pdfplumber - PDF text extraction
- PostgreSQL - Reliable database
- Celery - Background task processing
- Docker - Containerization

---

**Version:** 1.0.14
**Last Updated:** 2025-10-14
**Status:** Production Ready
