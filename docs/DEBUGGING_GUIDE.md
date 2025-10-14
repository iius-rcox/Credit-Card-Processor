# PDF Extraction Debugging Guide

**Last Updated:** 2025-10-14
**Feature:** 009-debug-extraction-output

---

## 🎯 Overview

This guide explains how to use the debug file output feature for troubleshooting PDF extraction issues.

When enabled, the system outputs 4 debug files per upload session:
1. **01_cardholder_text.txt** - Raw text extracted from cardholder activity report
2. **02_receipt_text.txt** - Raw text extracted from receipt report
3. **03_cardholder_regex_results.json** - Parsed transaction data with regex match details
4. **04_receipt_regex_results.json** - Parsed receipt data with regex match details

---

## 🔧 Setup

### Enable Debug Output

**Local Development:**
```bash
# In backend/.env file
DEBUG_EXTRACTION_OUTPUT=true
DEBUG_OUTPUT_PATH=./debug_output
ENVIRONMENT=development
```

**Docker Compose:**
```yaml
# In deploy/docker-compose.yml
backend:
  environment:
    DEBUG_EXTRACTION_OUTPUT: "true"
    DEBUG_OUTPUT_PATH: /app/debug_output
    ENVIRONMENT: development
```

**Kubernetes (NOT RECOMMENDED):**
```yaml
# Only for debugging in dev/staging clusters
env:
  - name: DEBUG_EXTRACTION_OUTPUT
    value: "true"
  - name: DEBUG_OUTPUT_PATH
    value: /app/debug_output
```

### Safety Requirements

Debug output only works when **BOTH** conditions are met:
- ✅ `ENVIRONMENT=development`
- ✅ `DEBUG_EXTRACTION_OUTPUT=true`

**Production Safety:**
- Debug is **automatically disabled** in production environments
- Setting `DEBUG_EXTRACTION_OUTPUT=true` in production has **no effect**

---

## 📁 File Organization

Debug files are organized by session ID and timestamp:

```
backend/debug_output/
  <session-id-1>/
    20251014_061630_01_cardholder_text.txt
    20251014_061630_02_receipt_text.txt
    20251014_061630_03_cardholder_regex_results.json
    20251014_061630_04_receipt_regex_results.json
  <session-id-2>/
    20251014_062145_01_cardholder_text.txt
    ...
```

**Naming Convention:**
- Format: `<timestamp>_<file_name>.<extension>`
- Timestamp: `YYYYMMDD_HHMMSS` (UTC)
- Session ID: UUID directory for organization

---

## 📄 Debug File Contents

### Text Files (01, 02)

**Purpose:** Raw text extracted from PDF via pdfplumber

**Example - 01_cardholder_text.txt:**
```
Cardholder Name: WILLIAMBURT
Employee ID: 12345
Card Number: **** **** **** 1234

Trans Date  Posted Date  Lvl  Transaction #  Merchant Name...
03/03/2025  03/04/2025   N    000425061     OVERHEAD DOOR COMKPEMAH, TX...
03/04/2025  03/06/2025   F    000127739     SHELL OIL129799150 MONTGOMERY, TX...
```

**What to Check:**
- Is the text readable? (If not, PDF may be scanned image)
- Do you see "Cardholder Name:" header?
- Are transaction lines visible?
- Any unusual formatting or character issues?

### JSON Files (03, 04)

**Purpose:** Structured extraction results with statistics and regex match details

**Example - 03_cardholder_regex_results.json:**
```json
{
  "extraction_timestamp": "2025-10-14T06:16:30.123456",
  "session_id": "be318a20-43b9-4102-a75a-7cabd10d1eb2",

  "pdf_metadata": {
    "filename": "Cardholder+Activity+Report.pdf",
    "file_size_bytes": 1234567,
    "total_pages": 15
  },

  "employee_name_found": "WILLIAMBURT",
  "employee_id_resolved": "550e8400-e29b-41d4-a716-446655440000",

  "total_matches": 1518,
  "incomplete_count": 0,
  "credit_count": 3,

  "regex_patterns": {
    "employee_header": "Cardholder Name:\\s*([A-Z]+)",
    "transaction": "^(\\d{2}/\\d{2}/\\d{4})\\s+..."
  },

  "sample_text": "First 1000 characters...",

  "extracted_transactions": [
    {
      "transaction_date": "2025-03-03",
      "amount": "768.22",
      "merchant_name": "OVERHEAD DOOR COMKPEMAH",
      "incomplete_flag": false
    }
  ],

  "extraction_stats": {
    "text_length": 123456,
    "lines_processed": 2543,
    "pattern_matches": 1518
  },

  "match_statistics": {
    "total_lines_in_pdf": 2543,
    "lines_with_dates": 1520,
    "lines_with_amounts": 1519,
    "successful_parses": 1518,
    "failed_parses": 0,
    "negative_amounts": 3
  },

  "sample_matches": {
    "first_matched_line": "03/03/2025 03/04/2025 N 000425061...",
    "first_10_lines": [...]
  }
}
```

---

## 🔍 Interpreting Results

### No Transactions Extracted

**Check:**
1. **Text file** - Is text readable?
2. **JSON file** - Check `extraction_stats.pattern_matches`
3. **JSON file** - Check `regex_patterns` vs actual text format
4. **JSON file** - Check `sample_matches.first_10_lines`

**Common Issues:**
- PDF is scanned image (no text extractable)
- Transaction format doesn't match regex pattern
- Missing expected headers ("Cardholder Name:")

### Employee Name Not Found

**Check JSON:**
- `employee_name_found`: null or empty?
- `sample_text`: Does it contain "Cardholder Name:"?
- `regex_patterns.employee_header`: Does pattern match your PDF format?

**Solution:**
- Update `employee_header_pattern` in `extraction_service.py`
- Or add employee alias mapping

### Low Match Count

**Check JSON:**
- `match_statistics.lines_with_dates` vs `total_matches`
- `match_statistics.successful_parses` vs `failed_parses`
- `sample_matches.first_10_lines` - Do they match expected format?

**Solution:**
- Compare `first_matched_line` with sample lines
- Adjust regex pattern to match your format
- Check for extra spaces, tabs, or special characters

### High Incomplete Count

**Check JSON:**
- `incomplete_count` - How many transactions flagged?
- `extracted_transactions[].incomplete_flag` - Which fields missing?
- `employee_id_resolved` - Is employee mapped?

**Common Causes:**
- Employee name not in database or aliases
- Date parsing failures
- Amount parsing failures
- Missing merchant names

---

## 🛠️ Troubleshooting Workflow

### Step 1: Upload and Get Session ID
```
1. Upload PDFs via UI
2. Note the session ID from response or UI
3. Check for debug files in debug_output/<session-id>/
```

### Step 2: Check Text Extraction
```bash
# View raw text file
cat backend/debug_output/<session-id>/20251014_*_01_cardholder_text.txt | head -50

# What to look for:
- Readable text (not garbled or empty)
- Expected headers and structure
- Transaction lines with dates and amounts
```

### Step 3: Check Regex Matching
```bash
# View JSON results
cat backend/debug_output/<session-id>/20251014_*_03_cardholder_regex_results.json | python -m json.tool

# Key metrics:
- total_matches: Should be > 0
- extraction_stats.pattern_matches: Should match transaction count
- match_statistics.successful_parses: Should be high percentage
```

### Step 4: Compare Patterns
```python
# Extract regex pattern from JSON
pattern = debug_data["regex_patterns"]["transaction"]

# Test against sample lines
import re
sample = debug_data["sample_matches"]["first_10_lines"][0]
match = re.search(pattern, sample, re.MULTILINE)
print(f"Match: {match}")
```

### Step 5: Iterate and Fix
```
1. Update regex patterns in extraction_service.py
2. Restart backend
3. Upload again
4. Compare new debug files with previous ones
5. Repeat until extraction works
```

---

## 📊 Performance Impact

**File Sizes:**
- Text files: 50-500KB per PDF
- JSON files: 100KB-2MB per session

**Write Time:**
- ~50-100ms total overhead per upload
- Negligible impact on upload performance

**Storage:**
- Recommend periodic cleanup (7-day retention)
- Add to cleanup scripts or cron jobs

---

## 🧹 Cleanup

### Manual Cleanup
```bash
# Remove all debug files
rm -rf backend/debug_output/

# Remove old debug files (7+ days)
find backend/debug_output/ -type f -mtime +7 -delete
find backend/debug_output/ -type d -empty -delete
```

### Docker Container Cleanup
```bash
# From host (volume mounted)
rm -rf backend/debug_output/

# From inside container
docker exec credit-card-backend rm -rf /app/debug_output/
```

---

## 🔐 Security Notes

**Safe Practices:**
- Debug files contain raw PDF content - may include sensitive data
- Only enabled in development environments
- Directory is gitignored (won't be committed)
- Clean up debug files before sharing environments

**Production:**
- Debug automatically disabled (environment check)
- No debug files created even if flag is true
- No performance impact from disabled feature

---

## 📚 Related Documentation

- **Implementation Plan:** `PRPs/debug-extraction-output.md`
- **Debug Writer Code:** `backend/src/utils/debug_writer.py`
- **Extraction Service:** `backend/src/services/extraction_service.py`
- **Configuration:** `backend/src/config.py`

---

## 🆘 Common Questions

**Q: Why are no debug files created?**
A: Check:
- `ENVIRONMENT=development` (not production)
- `DEBUG_EXTRACTION_OUTPUT=true`
- PDF has extractable text (not scanned image)
- Container has write permissions to debug_output/

**Q: Can I enable debug in production?**
A: No - debug is hard-coded to only work in `ENVIRONMENT=development`

**Q: How do I share debug files with the team?**
A: Zip the session directory and share via secure channel. Remove sensitive data first if needed.

**Q: Debug files are huge - how to reduce size?**
A: JSON files only include first 10 transactions by default. Text files contain full PDF text (necessary for debugging).

**Q: Can I change the output format?**
A: Yes - modify `debug_writer.py` or extraction service debug output sections.

---

## ✅ Verification Checklist

After enabling debug output:
- [ ] Environment is set to `development`
- [ ] `DEBUG_EXTRACTION_OUTPUT=true` in config
- [ ] Backend restarted with new settings
- [ ] Upload test PDF with real content
- [ ] Check `debug_output/<session-id>/` directory created
- [ ] Verify 4 files created (2 txt + 2 json)
- [ ] Text files contain readable PDF content
- [ ] JSON files have complete extraction data
- [ ] Check logs for `[DEBUG_FILE]` messages
- [ ] Verify production flag=false creates no files
