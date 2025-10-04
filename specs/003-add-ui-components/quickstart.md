# Quickstart: Session Management UI Components

## Prerequisites
- Next.js development environment running
- Backend API server available at `http://localhost:8000`
- Modern browser with localStorage support
- Sample PDF files for testing

## Test Files
Create these test files in project root for validation:
```bash
# Create test expense reports
echo "Test expense report January 2024" > test-expenses-jan-2024.pdf
echo "Test expense report February 2024" > test-expenses-feb-2024.pdf
echo "Updated expense report January 2024" > test-expenses-jan-2024-updated.pdf
```

## Validation Scenarios

### Scenario 1: Create and Manage Multiple Sessions

**Objective**: Verify multi-session creation and management capabilities

**Steps**:
1. Navigate to session management page: `/sessions`
2. Click "Create New Session" button
3. Enter session name: "January 2024 Expenses"
4. Upload credit card statement and expense report
5. Wait for processing to complete
6. Repeat steps 2-5 with name "February 2024 Expenses"
7. Verify both sessions appear in session browser
8. Check session status indicators show "Complete"

**Expected Results**:
- Two distinct sessions visible in browser
- Each session shows correct name and creation date
- Session status indicators reflect processing state
- Active session switches correctly between sessions

### Scenario 2: Session Renaming

**Objective**: Verify session naming functionality

**Steps**:
1. Open session browser
2. Locate "January 2024 Expenses" session
3. Click rename action (pencil icon or context menu)
4. Change name to "Q1 2024 January Processing"
5. Confirm rename operation
6. Verify updated name appears in session browser

**Expected Results**:
- Rename dialog opens with current name pre-filled
- Name validation prevents empty or invalid names
- Updated name persists after page refresh
- Session functionality unaffected by rename

### Scenario 3: Receipt Update Workflow

**Objective**: Verify receipt update capability for existing sessions

**Steps**:
1. Open "Q1 2024 January Processing" session
2. Navigate to session details page
3. Click "Update Receipts" button
4. Select `test-expenses-jan-2024-updated.pdf` file
5. Verify file validation accepts expense reports only
6. Submit update and monitor progress
7. Wait for re-processing to complete
8. Check updated reports are available for download

**Expected Results**:
- File upload only accepts PDF expense reports
- Credit card statement uploads are rejected with clear error
- Progress indicator shows update processing
- Original session data preserved on upload failure
- New reports generated after successful update

### Scenario 4: Historical Report Access

**Objective**: Verify historical data access without re-processing

**Steps**:
1. Complete Scenario 1 to have processed sessions
2. Navigate to session browser
3. Select "February 2024 Expenses" session
4. Click "Download Excel Report" button
5. Verify Excel file downloads immediately
6. Click "Download CSV Export" button
7. Verify CSV file downloads immediately
8. Check report content matches session data

**Expected Results**:
- Reports download without re-processing delay
- Excel and CSV formats both available
- Downloaded files contain accurate session data
- Multiple downloads work consistently

### Scenario 5: Session Storage Limits

**Objective**: Verify 24-session limit and retention policies

**Steps**:
1. Create 22 additional sessions (for 24 total)
2. Verify warning appears when approaching limit
3. Attempt to create 25th session
4. Check system behavior at limit
5. Modify one session's creation date to 13 months ago
6. Trigger cleanup operation
7. Verify expired session removed automatically

**Expected Results**:
- Warning displays when approaching 24 session limit
- 25th session creation blocked or oldest session removed
- Expired sessions automatically purged
- Storage limit maintained consistently

### Scenario 6: Error Handling and Recovery

**Objective**: Verify robust error handling

**Steps**:
1. Start receipt update on existing session
2. Disconnect from internet during upload
3. Verify error message appears
4. Reconnect to internet
5. Verify original session data unchanged
6. Retry update operation
7. Upload invalid file type (non-PDF)
8. Verify file validation error

**Expected Results**:
- Network errors display helpful messages
- Original session data never corrupted
- Invalid file types rejected with clear feedback
- Retry mechanisms work properly
- Error states don't break application

### Scenario 7: Session Independence

**Objective**: Verify sessions don't interfere with each other

**Steps**:
1. Open January session in one browser tab
2. Open February session in another tab
3. Update receipts in January session
4. Switch to February session tab
5. Verify February session unchanged
6. Perform operations in both sessions
7. Check data integrity maintained

**Expected Results**:
- Sessions maintain independent state
- Updates to one session don't affect others
- Multiple sessions can be used concurrently
- Session switching preserves context

## Performance Validation

### Load Testing
1. Create maximum 24 sessions
2. Verify session browser remains responsive
3. Test search and filtering with full session list
4. Measure UI interaction response times

**Targets**:
- Session browser loads in <200ms
- Search results update in <100ms
- Session switching completes in <150ms

### Memory Usage
1. Monitor browser memory with 24 sessions
2. Verify no memory leaks during session operations
3. Check localStorage size remains reasonable

**Targets**:
- localStorage usage <5MB total
- No persistent memory growth
- Efficient session data storage

## Accessibility Testing

### Keyboard Navigation
1. Navigate entire session interface using only keyboard
2. Verify all interactive elements are reachable
3. Test screen reader compatibility

### Visual Accessibility
1. Test with high contrast mode enabled
2. Verify color-blind accessibility
3. Check focus indicators are visible

## Browser Compatibility

Test on:
- Chrome 111+ (primary target)
- Safari 15.4+ (OKLCH support)
- Firefox 113+ (OKLCH support)
- Edge (Chromium-based)

Verify:
- localStorage persistence works
- OKLCH colors display correctly
- File upload functionality works
- Component interactions function properly

## Integration Points

### Backend API Integration
1. Verify existing `/api/session/{id}` endpoint works
2. Test `/api/session/{id}/update` receipt updates
3. Confirm `/api/reports/{id}` report downloads
4. Check error responses handled correctly

### Existing UI Integration
1. Navigate from main expense processing page
2. Return to main page from session browser
3. Verify theme consistency maintained
4. Check navigation breadcrumbs work

## Troubleshooting

### Common Issues
- **Sessions not persisting**: Check localStorage quotas and browser settings
- **File uploads failing**: Verify PDF format and file size <50MB
- **Reports not downloading**: Check backend API connectivity
- **Session limit errors**: Clear expired sessions or oldest sessions

### Debug Information
- Open browser DevTools → Application → Local Storage
- Check `expense_sessions` key for session data
- Monitor Network tab for API calls
- Check Console for JavaScript errors