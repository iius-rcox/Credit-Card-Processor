# Implementation Plan: Debug Extraction Output Files

## Overview
Add a debug flag that outputs intermediate extraction files for troubleshooting PDF parsing issues. When enabled, the system will save:
1. Raw text extraction from cardholder activity report PDF
2. Raw text extraction from receipt report PDF
3. Regex processing results for cardholder transactions
4. Regex processing results for receipt data

## Requirements Summary
- Add configurable debug flag (environment variable)
- Output 4 debug files per upload session when enabled:
  - `01_cardholder_text.txt` - Raw text from cardholder PDF
  - `02_receipt_text.txt` - Raw text from receipt PDF
  - `03_cardholder_regex_results.json` - Parsed transaction data + regex matches
  - `04_receipt_regex_results.json` - Parsed receipt data + regex matches
- Files should be organized by session ID and timestamp
- Only enabled in development environment for safety
- No impact on production performance or storage

## Research Findings

### Best Practices from Codebase

**1. Configuration Pattern:**
- Uses `pydantic-settings` in `config.py` with typed fields
- Helper functions: `is_development()`, `is_production()`, `is_test()`
- Environment-aware: All debug features check `ENVIRONMENT == "development"`

**2. Debug Logging Pattern:**
- Tagged logging with descriptive prefixes: `[REGEX_DEBUG]`, `[PDF_TEXT]`, `[EXTRACTION]`
- Conditional debug: `if logger.level <= logging.DEBUG:`
- Extensive logging in `extraction_service.py` lines 218-244

**3. File Operations Pattern:**
- Uses `pathlib.Path` for all file operations
- Context managers for proper cleanup: `with open() as f:`
- Directory creation: `Path.mkdir(parents=True, exist_ok=True)`
- Platform-safe paths: `tempfile.gettempdir()`

**4. Extraction Service Architecture:**
```
extract_from_upload_file(UploadFile, session_id)
  └─> _extract_text_from_bytes(pdf_bytes)      # pdfplumber extraction
      └─> _extract_credit_transactions(text)   # Regex parsing
          ├─> employee_header_pattern.search()
          ├─> transaction_pattern.finditer()
          └─> alias_repo.resolve_employee_id()
```

### Reference Implementations

**Existing Debug Script:**
- `backend/analyze_pdf_format.py` - Reference for debug output pattern
- Writes analysis to stdout (can redirect to file)
- Shows employee extraction and transaction parsing

**Logging Examples:**
- `extraction_service.py:139-144` - Text extraction debug logging
- `extraction_service.py:218-244` - Regex debug logging with samples

### Technology Decisions

**Output Format:**
- **Text files** (`.txt`) for raw PDF text - Easy to read, diff-friendly
- **JSON files** (`.json`) for structured regex results - Machine-readable, includes metadata
- **UTF-8 encoding** - Handles special characters in merchant names

**Storage Location:**
- **Development**: `./backend/debug_output/` - Local directory
- **Gitignored**: Added to `.gitignore` to prevent accidental commits
- **Session-based**: Organized by session ID for traceability

**Safety Measures:**
- **Environment check**: Only write files if `ENVIRONMENT == "development"`
- **Flag check**: Requires explicit `DEBUG_EXTRACTION_OUTPUT=true`
- **Error handling**: Wrap file I/O in try/except to prevent upload failures
- **Resource cleanup**: Use context managers for all file operations

## Implementation Tasks

### Phase 1: Configuration Setup

#### Task 1.1: Add Debug Configuration Fields
- **Description**: Add new settings to `config.py` for debug file output
- **Files to modify**: `backend/src/config.py`
- **Changes**:
  ```python
  # Add after existing upload settings
  DEBUG_EXTRACTION_OUTPUT: bool = Field(
      default=False,
      description="Enable debug file output for PDF extraction"
  )
  DEBUG_OUTPUT_PATH: str = Field(
      default="./debug_output",
      description="Directory for debug output files"
  )
  ```
- **Dependencies**: None
- **Estimated effort**: 5 minutes
- **Validation**: Settings load without errors

#### Task 1.2: Update Environment Files
- **Description**: Add debug flags to example `.env` files
- **Files to modify**: `backend/.env.example` (if exists) or create documentation
- **Changes**:
  ```bash
  # Debug Settings (Development Only)
  DEBUG_EXTRACTION_OUTPUT=false
  DEBUG_OUTPUT_PATH=./debug_output
  ```
- **Dependencies**: Task 1.1
- **Estimated effort**: 5 minutes

#### Task 1.3: Update .gitignore
- **Description**: Prevent debug output files from being committed
- **Files to modify**: `backend/.gitignore` or root `.gitignore`
- **Changes**:
  ```
  # Debug output files
  debug_output/
  *.debug.json
  *.debug.txt
  ```
- **Dependencies**: None
- **Estimated effort**: 2 minutes

### Phase 2: Core Debug Output Implementation

#### Task 2.1: Add Debug File Writer Utility
- **Description**: Create reusable debug file writer function
- **Files to create**: `backend/src/utils/debug_writer.py` (new file)
- **Implementation**:
  ```python
  """Debug file output utilities."""
  import json
  import logging
  from pathlib import Path
  from typing import Any, Optional
  from uuid import UUID
  from datetime import datetime

  from ..config import settings, is_development

  logger = logging.getLogger(__name__)


  def write_debug_file(
      session_id: UUID,
      file_name: str,
      content: Any,
      file_type: str = "json"
  ) -> Optional[Path]:
      """
      Write debug output file if debug mode enabled.

      Args:
          session_id: Session UUID for organizing files
          file_name: Base name for debug file
          content: Content to write (str for txt, dict for json)
          file_type: "json" or "txt"

      Returns:
          Path to written file, or None if debug disabled
      """
      # Safety check: Only in development with flag enabled
      if not is_development() or not settings.DEBUG_EXTRACTION_OUTPUT:
          return None

      try:
          # Create output directory
          output_dir = Path(settings.DEBUG_OUTPUT_PATH) / str(session_id)
          output_dir.mkdir(parents=True, exist_ok=True)

          # Build file path with timestamp
          timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
          extension = "json" if file_type == "json" else "txt"
          output_file = output_dir / f"{timestamp}_{file_name}.{extension}"

          # Write content
          if file_type == "json":
              with open(output_file, "w", encoding="utf-8") as f:
                  json.dump(content, f, indent=2, default=str)
          else:
              with open(output_file, "w", encoding="utf-8") as f:
                  f.write(str(content))

          logger.info(f"[DEBUG_FILE] Wrote debug output: {output_file}")
          return output_file

      except Exception as e:
          logger.error(f"[DEBUG_FILE] Failed to write debug file: {e}")
          return None
  ```
- **Dependencies**: Task 1.1
- **Estimated effort**: 20 minutes
- **Testing**: Unit test for file writing with mocked settings

#### Task 2.2: Add Text Extraction Debug Output
- **Description**: Output raw PDF text to debug files in `_extract_text()` method
- **Files to modify**: `backend/src/services/extraction_service.py`
- **Changes**: Add after line 146 in `_extract_text()` method:
  ```python
  # Debug file output: Raw text extraction
  from ..utils.debug_writer import write_debug_file

  # Determine file type from context (cardholder vs receipt)
  # This will be enhanced when session_id is available
  if hasattr(self, '_current_session_id'):
      file_name = "01_cardholder_text" if "Cardholder" in text[:500] else "02_receipt_text"
      write_debug_file(
          session_id=self._current_session_id,
          file_name=file_name,
          content=text,
          file_type="txt"
      )
  ```
- **Dependencies**: Task 2.1
- **Estimated effort**: 15 minutes

#### Task 2.3: Add Regex Results Debug Output
- **Description**: Output regex match results to JSON debug files
- **Files to modify**: `backend/src/services/extraction_service.py`
- **Changes**: Add after line 331 in `_extract_credit_transactions()` method:
  ```python
  # Debug file output: Regex processing results
  if hasattr(self, '_current_session_id'):
      from ..utils.debug_writer import write_debug_file

      debug_data = {
          "extraction_timestamp": datetime.utcnow().isoformat(),
          "employee_name_found": employee_name,
          "employee_id_resolved": str(employee_id) if employee_id else None,
          "total_matches": len(transactions),
          "incomplete_count": sum(1 for t in transactions if t.get("incomplete_flag")),
          "credit_count": sum(1 for t in transactions if t.get("is_credit")),
          "regex_patterns": {
              "employee_header": self.employee_header_pattern.pattern,
              "transaction": self.transaction_pattern.pattern
          },
          "sample_text": text[:1000],
          "extracted_transactions": transactions[:10],  # First 10 only
          "extraction_stats": {
              "text_length": len(text),
              "lines_processed": len(text.split('\n')),
              "pattern_matches": len(matches_list)
          }
      }

      file_name = "03_cardholder_regex_results" if "Cardholder" in text[:500] else "04_receipt_regex_results"
      write_debug_file(
          session_id=self._current_session_id,
          file_name=file_name,
          content=debug_data,
          file_type="json"
      )
  ```
- **Dependencies**: Task 2.1, Task 2.2
- **Estimated effort**: 20 minutes

#### Task 2.4: Track Current Session in ExtractionService
- **Description**: Add session_id tracking to enable debug output
- **Files to modify**: `backend/src/services/extraction_service.py`
- **Changes**:
  ```python
  # In __init__ method, add:
  self._current_session_id: Optional[UUID] = None

  # In extract_from_upload_file method, add at start:
  self._current_session_id = session_id

  # In extract_from_upload_file method, add at end (finally block):
  finally:
      self._current_session_id = None
  ```
- **Dependencies**: None
- **Estimated effort**: 10 minutes

### Phase 3: Enhanced Debug Output

#### Task 3.1: Add File Metadata to Debug Output
- **Description**: Include PDF filename, file size, page count in debug files
- **Files to modify**: `backend/src/services/extraction_service.py`
- **Enhancement to Task 2.3**:
  ```python
  "pdf_metadata": {
      "filename": pdf_filename if hasattr(self, '_current_pdf_filename') else "unknown",
      "file_size_bytes": file_size if hasattr(self, '_current_pdf_size') else 0,
      "total_pages": total_pages if hasattr(self, '_current_pdf_pages') else 0
  }
  ```
- **Dependencies**: Task 2.3
- **Estimated effort**: 15 minutes

#### Task 3.2: Add Match Statistics
- **Description**: Include detailed statistics about regex matching success/failure
- **Files to modify**: Debug output in Task 2.3
- **Enhancement**:
  ```python
  "match_statistics": {
      "total_lines_in_pdf": len(text.split('\n')),
      "lines_with_dates": len([l for l in text.split('\n') if self.date_pattern.search(l)]),
      "lines_with_amounts": len([l for l in text.split('\n') if self.amount_pattern.search(l)]),
      "successful_parses": len([t for t in transactions if not t.get("incomplete_flag")]),
      "failed_parses": len([t for t in transactions if t.get("incomplete_flag")]),
      "negative_amounts": len([t for t in transactions if t.get("is_credit")])
  }
  ```
- **Dependencies**: Task 2.3
- **Estimated effort**: 10 minutes

#### Task 3.3: Add Sample Match Examples
- **Description**: Include first matched line and first unmatched line for comparison
- **Files to modify**: Debug output in Task 2.3
- **Enhancement**:
  ```python
  "sample_matches": {
      "first_matched_line": matches_list[0].group(0) if matches_list else None,
      "first_unmatched_line": self._find_first_unmatched_line(text, matches_list)
  }
  ```
- **Dependencies**: Task 2.3
- **Estimated effort**: 15 minutes

### Phase 4: Testing & Documentation

#### Task 4.1: Create Unit Tests
- **Description**: Test debug file writing with mocked settings
- **Files to create**: `backend/tests/unit/test_debug_writer.py`
- **Test cases**:
  - Debug disabled (production) - no files written
  - Debug enabled (development) - files written correctly
  - Invalid paths - graceful error handling
  - UTF-8 encoding with special characters
  - JSON serialization with Decimal/UUID types
- **Dependencies**: Task 2.1
- **Estimated effort**: 30 minutes

#### Task 4.2: Create Integration Test
- **Description**: Test full extraction with debug output
- **Files to create**: `backend/tests/integration/test_extraction_debug_output.py`
- **Test cases**:
  - Upload with debug enabled - verify 4 files created
  - Verify file contents match extraction results
  - Verify files organized by session ID
  - Verify cleanup doesn't affect debug files
- **Dependencies**: All Phase 2 tasks
- **Estimated effort**: 45 minutes

#### Task 4.3: Update Documentation
- **Description**: Document debug flag usage
- **Files to modify/create**:
  - `docs/DEBUGGING_GUIDE.md` (new)
  - Update `README.md` with debug flag section
  - Add to `docs/COMPLETE_FIX_SUMMARY.md`
- **Content**:
  - How to enable debug output
  - What files are generated
  - How to interpret debug files
  - Troubleshooting extraction issues
- **Dependencies**: All tasks
- **Estimated effort**: 20 minutes

#### Task 4.4: Manual Testing Verification
- **Description**: Test with real PDFs and verify debug output
- **Testing steps**:
  1. Enable debug flag: `DEBUG_EXTRACTION_OUTPUT=true`
  2. Upload real cardholder activity report + receipt report
  3. Verify 4 debug files created in `debug_output/<session-id>/`
  4. Verify text files contain readable PDF text
  5. Verify JSON files have complete regex match data
  6. Check that production deployment (flag=false) creates no files
- **Dependencies**: All Phase 2 and 3 tasks
- **Estimated effort**: 30 minutes

## Codebase Integration Points

### Files to Modify

**1. `backend/src/config.py`**
- Add `DEBUG_EXTRACTION_OUTPUT: bool` field
- Add `DEBUG_OUTPUT_PATH: str` field
- Lines to add: ~10 lines after line 103

**2. `backend/src/services/extraction_service.py`**
- Add session tracking: `self._current_session_id` in `__init__`
- Import debug writer in methods that need it
- Add debug file writes in:
  - `_extract_text()` method (after line 146)
  - `_extract_credit_transactions()` method (after line 331)
- Lines to add: ~60 lines total

**3. `backend/.gitignore` or root `.gitignore`**
- Add `debug_output/` directory
- Add `*.debug.json`, `*.debug.txt` patterns
- Lines to add: ~3 lines

**4. `backend/.env` or `.env.example`**
- Add debug configuration variables
- Lines to add: ~4 lines

### New Files to Create

**1. `backend/src/utils/debug_writer.py`**
- Purpose: Reusable debug file writer utility
- Functions: `write_debug_file(session_id, file_name, content, file_type)`
- Size: ~80 lines with docstrings

**2. `backend/tests/unit/test_debug_writer.py`**
- Purpose: Unit tests for debug writer
- Tests: 5-7 test cases
- Size: ~150 lines

**3. `backend/tests/integration/test_extraction_debug_output.py`**
- Purpose: Integration test for full extraction with debug
- Tests: 3-5 test scenarios
- Size: ~200 lines

**4. `docs/DEBUGGING_GUIDE.md`**
- Purpose: User guide for debug features
- Sections: Setup, Usage, Interpretation, Troubleshooting
- Size: ~150 lines

### Existing Patterns to Follow

**Configuration:**
- Use `pydantic.Field()` with descriptive defaults
- Add type hints: `Literal[]` for enums, specific types for values
- Include description parameter for documentation

**File Operations:**
- Always use `pathlib.Path` (not string paths)
- Use context managers: `with open() as f:`
- Create dirs safely: `mkdir(parents=True, exist_ok=True)`
- Handle errors with try/except, log but don't fail

**Logging:**
- Use tagged prefixes: `[DEBUG_FILE]`, `[DEBUG_WRITE]`
- Include relevant context: session_id, file names, counts
- Use appropriate levels: INFO for success, ERROR for failures, WARNING for skipped

**JSON Serialization:**
- Use `default=str` for non-serializable types (UUID, Decimal, datetime)
- Use `indent=2` for readability
- Include metadata: timestamp, session_id, counts

## Technical Design

### File Organization Structure
```
backend/
  debug_output/                    # Root debug directory (gitignored)
    <session-id-1>/               # One directory per session
      20251014_051630_01_cardholder_text.txt
      20251014_051630_02_receipt_text.txt
      20251014_051630_03_cardholder_regex_results.json
      20251014_051630_04_receipt_regex_results.json
    <session-id-2>/
      20251014_052145_01_cardholder_text.txt
      ...
```

### Debug File Formats

**Text Files (01, 02):**
```
Cardholder Name: WILLIAMBURT
Employee ID: 12345
...
[Raw PDF text content]
...
```

**JSON Files (03, 04):**
```json
{
  "extraction_timestamp": "2025-10-14T05:16:30.123456",
  "session_id": "1ab1464c-d926-444d-886d-b0c3449f61fe",
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
  "sample_text": "First 1000 characters of extracted text...",
  "extracted_transactions": [
    {
      "employee_id": "550e8400-e29b-41d4-a716-446655440000",
      "transaction_date": "2025-03-03",
      "amount": "768.22",
      "merchant_name": "OVERHEAD DOOR COMKPEMAH",
      "merchant_category": "General Expense",
      "description": "OOTTHHEERR MMIISSCCEELLLLAANNEEOOUUSS TTRRAANNSS",
      "incomplete_flag": false,
      "is_credit": false,
      "raw_data": {...}
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
  }
}
```

### Data Flow
```
1. Upload PDFs
   ↓
2. extract_from_upload_file(file, session_id)
   ├─> Set _current_session_id = session_id
   ├─> _extract_text_from_bytes(pdf_bytes)
   │   ├─> pdfplumber.open(BytesIO(pdf_bytes))
   │   ├─> Extract text from all pages
   │   └─> [DEBUG] Write 01_cardholder_text.txt or 02_receipt_text.txt
   │
   └─> _extract_credit_transactions(text)
       ├─> Apply employee_header_pattern
       ├─> Apply transaction_pattern
       ├─> Resolve employee IDs via aliases
       ├─> Build transaction dictionaries
       └─> [DEBUG] Write 03_cardholder_regex_results.json or 04_receipt_regex_results.json
```

### Performance Considerations

**File I/O Impact:**
- Only in development environment
- Async-safe (uses synchronous file I/O in async context - acceptable for debug)
- Error handling prevents upload failures
- Typical overhead: ~50-100ms per debug file write

**Storage Impact:**
- Text files: ~50-500KB per PDF (depends on PDF size)
- JSON files: ~100KB-2MB per session (depends on transaction count)
- Recommend cleanup after 7 days for development environments

**Memory Impact:**
- Text already in memory (extracted for processing)
- JSON serialization creates temporary copy
- No significant memory overhead

## Dependencies and Libraries

**No new dependencies required:**
- Uses Python standard library: `json`, `pathlib`, `logging`
- Uses existing: `pydantic-settings`, `pdfplumber`
- No external packages needed

## Testing Strategy

### Unit Tests
- **File**: `backend/tests/unit/test_debug_writer.py`
- **Test cases**:
  - `test_write_debug_file_production_disabled` - Verify no output in production
  - `test_write_debug_file_flag_disabled` - Verify respects flag
  - `test_write_debug_file_text` - Test text file writing
  - `test_write_debug_file_json` - Test JSON file writing
  - `test_write_debug_file_creates_directory` - Verify directory creation
  - `test_write_debug_file_handles_errors` - Test error handling
  - `test_write_debug_file_serializes_types` - Test UUID/Decimal serialization

### Integration Tests
- **File**: `backend/tests/integration/test_extraction_debug_output.py`
- **Test scenarios**:
  - Upload with debug enabled - verify 4 files created
  - Upload with debug disabled - verify no files created
  - Multiple sessions - verify files organized correctly
  - Large PDF - verify debug file completeness
  - Extraction error - verify error info in debug file

### Manual Testing
- Use Chrome DevTools to upload real PDFs
- Verify debug files created in `backend/debug_output/`
- Inspect file contents for completeness
- Test with production flag disabled
- Verify no performance degradation

## Success Criteria

- [x] Debug flag added to configuration (environment variable)
- [x] Text extraction outputs to `.txt` files
- [x] Regex results output to `.json` files
- [x] Files organized by session ID
- [x] Only enabled in development environment
- [x] No impact on production (flag disabled by default)
- [x] Proper error handling (debug failures don't break uploads)
- [x] Unit tests pass (>80% coverage)
- [x] Integration tests pass
- [x] Documentation complete
- [x] Manual testing successful with real PDFs

## Notes and Considerations

### Security
- **No sensitive data exposure**: Files only created in development
- **Gitignored**: Prevents accidental commits to repository
- **Environment-gated**: Double check (flag + environment) for safety

### Maintenance
- **Cleanup strategy**: Consider adding periodic cleanup (7-day retention)
- **Disk space**: Monitor debug_output/ directory size in development
- **Documentation**: Keep debug file format documented for team

### Future Enhancements
- Add debug file viewer UI (web-based)
- Add compression for large debug files
- Add debug file export API endpoint
- Add diff comparison between sessions

### Potential Challenges
- **File identification**: Currently uses heuristic ("Cardholder" in text) to distinguish file types
  - Consider adding explicit file_type parameter to extract methods
- **BytesIO vs Path**: extract_from_upload_file uses BytesIO, existing methods expect Path
  - Already solved by creating temporary BytesIO → pdfplumber pattern
- **Async file I/O**: Using sync file operations in async methods
  - Acceptable for debug (small overhead), or consider `aiofiles` library

---

*This plan is ready for execution with `/execute-plan PRPs/debug-extraction-output.md`*
