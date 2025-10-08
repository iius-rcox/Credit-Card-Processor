# Quickstart: Better Status Updates

**Feature**: 006-better-status-updates
**Purpose**: Validate progress tracking implementation end-to-end
**Estimated Time**: 10-15 minutes

## Prerequisites

- Backend server running on `localhost:8000`
- Frontend running on `localhost:3000`
- Database migrated with progress tracking fields
- Sample PDF files available for upload

## Test Scenario: Multi-File PDF Processing with Progress Tracking

This quickstart validates the primary user story from the feature spec:
> "As a user uploading credit card statements and receipt PDFs for reconciliation, I want to see detailed progress updates during processing so that I understand what's happening and can estimate how long it will take."

---

## Step 1: Start a New Session

**Action**: Upload 2-3 PDF files to create a new session

**Backend API Call:**
```bash
curl -X POST http://localhost:8000/api/sessions/upload \
  -F "credit_card=@statement_001.pdf" \
  -F "credit_card=@statement_002.pdf" \
  -F "receipts=@receipt_001.pdf"
```

**Expected Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "uploaded_files": 3
}
```

**Validation:**
- ✅ Session created with UUID
- ✅ Files uploaded successfully
- ✅ Status is "processing"

---

## Step 2: Poll Progress During Upload Phase

**Action**: Get progress snapshot immediately after upload

**API Call:**
```bash
curl http://localhost:8000/api/sessions/{session_id}/progress
```

**Expected Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "upload",
  "overall_percentage": 10,
  "phase_details": {
    "upload": {
      "status": "in_progress",
      "percentage": 100
    },
    "processing": {
      "status": "pending",
      "percentage": 0
    }
  },
  "last_update": "2025-10-08T14:23:15Z",
  "status_message": "Uploading files: 3 of 3 complete"
}
```

**Validation:**
- ✅ `current_phase` is "upload"
- ✅ `overall_percentage` reflects upload phase (around 10%)
- ✅ Upload phase shows 100% progress
- ✅ Processing phase is pending

---

## Step 3: Monitor Page-Level Progress

**Action**: Poll progress every 3 seconds during file processing

**API Call** (repeat every 3 seconds):
```bash
curl http://localhost:8000/api/sessions/{session_id}/progress
```

**Expected Response** (during processing):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "processing",
  "overall_percentage": 45,
  "phase_details": {
    "upload": {
      "status": "completed",
      "percentage": 100,
      "completed_at": "2025-10-08T14:23:15Z"
    },
    "processing": {
      "status": "in_progress",
      "percentage": 35,
      "total_files": 3,
      "current_file_index": 2,
      "current_file": {
        "name": "statement_002.pdf",
        "total_pages": 12,
        "current_page": 5,
        "regex_matches_found": 23,
        "started_at": "2025-10-08T14:24:30Z"
      }
    },
    "matching": {
      "status": "pending",
      "percentage": 0
    }
  },
  "last_update": "2025-10-08T14:25:42Z",
  "status_message": "Processing File 2 of 3: Page 5/12"
}
```

**Validation (FR-004, FR-007, FR-018):**
- ✅ Shows page-level granularity ("Page 5 of 12")
- ✅ Displays current file being processed ("statement_002.pdf")
- ✅ Shows file index (File 2 of 3)
- ✅ Includes regex match counter (23 matches found)
- ✅ Overall percentage increases over time
- ✅ Status message is descriptive (not generic "Processing...")

---

## Step 4: Verify Progress Advances Per File

**Action**: Continue polling, observe progress when file completes

**Expected Observations:**
1. File 1 completes → `current_file_index` advances to 2
2. Page counter resets for File 2 (Page 1 of N)
3. Overall percentage increases proportionally
4. Status message updates to reflect new file

**Validation (FR-019):**
- ✅ Progress correctly transitions between files
- ✅ Page counter resets for each new file
- ✅ Aggregate percentage reflects weighted progress

---

## Step 5: Test Progress Persistence (Page Refresh)

**Action**: While processing is ongoing, simulate page refresh by calling progress API with cached session ID

**Scenario:**
1. Poll progress → Save `last_update` timestamp
2. Wait 5 seconds (simulate network disconnect)
3. Poll progress again → Compare timestamps

**Expected Behavior:**
```json
{
  "last_update": "2025-10-08T14:26:12Z"  // New timestamp, progress advanced
}
```

**Validation (FR-008, FR-013):**
- ✅ Progress state persists in database
- ✅ User can navigate away and return
- ✅ Progress is retrievable after page refresh
- ✅ No loss of progress data

---

## Step 6: Verify Update Frequency

**Action**: Measure time between progress updates

**Method:**
```bash
for i in {1..5}; do
  echo "Poll $i:"
  curl -s http://localhost:8000/api/sessions/{session_id}/progress \
    | jq '.last_update'
  sleep 3
done
```

**Expected Behavior:**
- Updates occur approximately every 2-3 seconds
- `last_update` timestamp advances consistently
- No updates faster than 2 seconds (batching working)

**Validation (FR-005, FR-011):**
- ✅ Updates batched to 2-3 second intervals
- ✅ No UI overload from rapid updates
- ✅ Progress updates automatically (no user interaction needed)

---

## Step 7: Verify Completion State

**Action**: Poll until processing completes

**Expected Final Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_phase": "completed",
  "overall_percentage": 100,
  "phase_details": null,
  "last_update": "2025-10-08T14:30:00Z",
  "status_message": "Processing complete: 3 files, 45 transactions, 12 receipts matched"
}
```

**Validation (FR-009, FR-010):**
- ✅ `overall_percentage` reaches 100%
- ✅ `current_phase` is "completed"
- ✅ `phase_details` is null (transient data cleared)
- ✅ Status message provides summary

---

## Step 8: Test Error Handling

**Action**: Upload a corrupted or empty PDF to trigger processing failure

**API Call:**
```bash
curl -X POST http://localhost:8000/api/sessions/upload \
  -F "credit_card=@corrupted.pdf"
```

**Poll Progress:**
```bash
curl http://localhost:8000/api/sessions/{session_id}/progress
```

**Expected Response (on failure):**
```json
{
  "session_id": "...",
  "current_phase": "failed",
  "overall_percentage": 32,
  "phase_details": {
    "processing": {
      "status": "failed",
      "percentage": 35
    }
  },
  "error": {
    "type": "PDFExtractionError",
    "message": "Unable to extract text from PDF",
    "context": {
      "phase": "processing",
      "file": "corrupted.pdf",
      "page": 1
    },
    "timestamp": "2025-10-08T14:27:00Z"
  },
  "last_update": "2025-10-08T14:27:00Z",
  "status_message": "Failed during file processing"
}
```

**Validation (FR-015, FR-016, FR-017):**
- ✅ Error shows which phase failed
- ✅ Error context includes file and page
- ✅ Error message is descriptive
- ✅ Progress shows percentage at time of failure
- ✅ Partial results discarded (database check)

---

## Step 9: Frontend UI Validation

**Action**: Open frontend in browser at `http://localhost:3000`

**Navigate to**: Session detail page (from upload or sessions list)

**Expected UI Elements:**
1. **Aggregate Progress Bar**
   - Large circular progress ring or bar
   - Shows overall percentage (0-100%)
   - Color changes based on status (blue=processing, green=complete, red=error)

2. **Phase Stepper**
   - Visual indicator of current phase
   - Shows: Upload → Processing → Matching → Report → Complete
   - Current phase highlighted

3. **Detailed File List** (expandable/collapsible)
   - Shows each file with mini progress bar
   - Displays page counter (Page X of Y)
   - Current file highlighted or pulsing

4. **Status Message**
   - Displayed prominently
   - Updates every 2-3 seconds
   - Descriptive (not generic)

5. **Auto-Refresh Behavior**
   - Progress updates without user action
   - Polling interval: 2-3 seconds
   - Smooth progress bar animations

**Validation (FR-011, FR-012, FR-014, FR-018, FR-019):**
- ✅ UI updates automatically
- ✅ Both aggregate and per-file progress shown
- ✅ Status messages are descriptive
- ✅ Progress display provides reassurance of activity
- ✅ User can distinguish which file is currently processing

---

## Step 10: Test Page Refresh Recovery

**Action**: While processing, hard refresh the browser (Ctrl+R or Cmd+R)

**Expected Behavior:**
1. Page reloads
2. Immediately shows cached progress (from localStorage)
3. Reconnects to backend polling
4. Progress continues from last known state
5. No loss of information

**Validation (FR-013):**
- ✅ Progress visible after navigation/refresh
- ✅ No "loading" or "unknown status" shown
- ✅ Cached state displayed immediately
- ✅ Real-time updates resume within 3 seconds

---

## Success Criteria

All tests pass if:

- ✅ **FR-001**: Distinct phases displayed (upload, processing, matching)
- ✅ **FR-002**: Percentage shown for each phase
- ✅ **FR-003**: Status updates batched every 2-3 seconds
- ✅ **FR-004**: Page-level granularity ("Page X of Y")
- ✅ **FR-005**: Updates occur at 2-3 second intervals
- ✅ **FR-006**: Current phase name displayed
- ✅ **FR-007**: Quantitative progress within phases (page counters)
- ✅ **FR-008**: Progress persists across page refresh
- ✅ **FR-009**: Overall completion percentage shown
- ✅ **FR-010**: Relative progress provided (not stuck indefinitely)
- ✅ **FR-011**: Progress updates automatically (no interaction needed)
- ✅ **FR-012**: Status messages are meaningful
- ✅ **FR-013**: Progress visible after navigation/refresh
- ✅ **FR-014**: Updates reassure user of active processing
- ✅ **FR-015**: Error indicates which phase failed
- ✅ **FR-016**: Error messages include context
- ✅ **FR-017**: Partial results discarded on failure
- ✅ **FR-018**: Both aggregate and per-file progress shown
- ✅ **FR-019**: Current file name displayed

---

## Troubleshooting

### Progress Not Updating
1. Check backend logs for errors in ProgressTracker
2. Verify database migration applied (`processing_progress` column exists)
3. Check frontend polling interval (should be 2-3 seconds)
4. Verify `last_update` timestamp is advancing

### Page Counter Not Showing
1. Check `pdfplumber` is installed and `len(pdf.pages)` works
2. Verify `current_file` object exists in progress response
3. Check `total_pages` and `current_page` fields are populated

### Progress Stuck at Same Percentage
1. Check backend processing is running (not stalled)
2. Verify progress updates are being written to database
3. Check for errors in extraction service logs
4. Ensure batching logic is emitting updates at boundaries

### Frontend Not Polling
1. Check browser console for network errors
2. Verify polling hook is initialized (`useProgress`)
3. Check API endpoint is reachable (CORS, network)
4. Verify session ID is valid and passed correctly

---

## Estimated Completion Time

- **Step 1-2**: 2 minutes (setup and initial upload)
- **Step 3-6**: 5-7 minutes (monitoring progress, multiple polls)
- **Step 7**: 1 minute (completion state)
- **Step 8**: 2 minutes (error scenario)
- **Step 9-10**: 3-5 minutes (frontend UI validation)

**Total**: 10-15 minutes for complete validation

---

## Acceptance

This quickstart validates the feature when:
1. All 10 steps complete successfully
2. All success criteria checkboxes are ✅
3. No errors in backend logs related to progress tracking
4. Frontend UI displays progress smoothly without glitches
5. Progress persists across page refresh

If any step fails, reference the data-model.md, research.md, and contract tests for expected behavior.
