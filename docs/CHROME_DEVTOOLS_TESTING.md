# Chrome DevTools Testing - Browser Lock Resolution

**Issue**: Chrome DevTools MCP browser profile is locked
**Error**: "The browser is already running for /Users/rogercox/.cache/chrome-devtools-mcp/chrome-profile"

---

## 🔧 Fix Browser Lock

### Option 1: Close Existing Chrome Windows

1. **Find all Chrome processes**:
   ```bash
   ps aux | grep -i chrome
   ```

2. **Close Chrome DevTools MCP windows**:
   - Look for Chrome windows that were opened by MCP
   - Close them completely
   - Or close all Chrome windows

3. **Kill Chrome processes** (if needed):
   ```bash
   pkill -f "chrome.*chrome-devtools-mcp"
   ```

4. **Clear the profile lock**:
   ```bash
   rm -rf /Users/rogercox/.cache/chrome-devtools-mcp/chrome-profile/SingletonLock
   ```

### Option 2: Use Manual Browser Testing

Since automated Chrome DevTools MCP testing is blocked:

1. **Manually open Chrome**
2. **Navigate to**: http://localhost:3000
3. **Open DevTools**: Press `F12` or `Cmd+Option+I`
4. **Follow the test plan**: See sections below

---

## 🧪 Manual Testing Steps

### Before Starting

**Make sure Docker containers are running**:
```bash
cd /Users/rogercox/Credit-Card-Processor
./run-full-test-sequence.sh
```

Or manually:
```bash
docker-compose up -d
docker-compose ps
curl http://localhost:8000/health
```

---

## 📋 Test Checklist

### Test 1: Homepage (http://localhost:3000)

**Steps**:
1. Open http://localhost:3000
2. Open DevTools (F12)
3. Check Console tab

**Expected**:
- ✅ Page loads successfully
- ✅ No red errors in console
- ✅ Theme toggle visible in top-right
- ✅ Page title shows "Expense App"

**Screenshot**:
- Take screenshot of homepage
- Take screenshot of console (should be clean)

---

### Test 2: Console Tab

**What to Check**:
- ❌ **No red errors** (JavaScript errors)
- ⚠️ **Yellow warnings are OK** (development mode)
- ℹ️ **Blue info messages are OK**

**Common Messages (OK)**:
- Next.js dev mode messages
- React dev mode warnings
- HMR (Hot Module Replacement) logs

**Red Flags (BAD)**:
- Network errors (failed to fetch)
- Uncaught exceptions
- CORS errors
- 404 Not Found errors

---

### Test 3: Network Tab

**Steps**:
1. Open DevTools Network tab
2. Refresh page (Cmd+R)
3. Check all requests

**Expected Requests**:
- `localhost:3000` → 200 OK (HTML)
- `/_next/static/...` → 200 OK (JS/CSS)
- `/favicon.ico` → 200 OK
- Fonts → 200 OK

**Check For**:
- ✅ All resources load (200 status)
- ❌ No 404 errors
- ❌ No 500 errors
- ❌ No failed requests (red color)

**Screenshot**: Network tab showing successful loads

---

### Test 4: Upload Page (http://localhost:3000/upload)

**Steps**:
1. Navigate to http://localhost:3000/upload
2. Check page renders

**Expected Elements**:
- ✅ Upload form visible
- ✅ Drag-and-drop zone
- ✅ "Choose Files" button
- ✅ Instructions section
- ✅ "How It Works" steps

**Check Console**:
- ❌ No new errors after navigation

**Screenshot**: Upload page with form visible

---

### Test 5: Drag-and-Drop Interaction

**Steps**:
1. Prepare a test PDF file
2. Drag PDF over drop zone
3. Observe visual feedback

**Expected**:
- ✅ Drop zone highlights when file dragged over
- ✅ Border color changes (visual feedback)
- ✅ File appears in list after drop
- ✅ File name and size displayed

**Check Console**:
- ❌ No errors during drag-and-drop

**Screenshot**: File in upload list

---

### Test 6: File Validation

**Test Invalid File Types**:
1. Try to upload a `.txt` file
2. Should show error: "Only PDF files are allowed"

**Test File Size Limit**:
1. Try to upload file > 10MB
2. Should show error: "File exceeds maximum size"

**Test Too Many Files**:
1. Try to upload > 100 files
2. Should show error: "Maximum 100 files allowed"

**Expected**:
- ✅ Error messages display in red
- ✅ Invalid files rejected
- ✅ Valid PDFs accepted

**Screenshot**: Error message example

---

### Test 7: Upload Workflow (E2E)

**Prerequisites**:
- Have 2-3 sample PDF files (credit card statements, receipts)
- Backend must be running (`curl http://localhost:8000/health`)

**Steps**:
1. Upload 2-3 valid PDF files
2. Click "Upload Files" button
3. **Watch Network tab** closely

**Expected Network Activity**:
1. **POST** `/api/upload` → 202 Accepted
   - Check request payload (multipart/form-data)
   - Check response (session ID)

2. **GET** `/api/sessions/{id}` → 200 OK (repeated every 2 seconds)
   - This is status polling
   - Should continue until status = "completed"

3. Eventually stops when processing complete

**Expected UI Changes**:
1. Progress display appears
2. Progress bar animates
3. Statistics update (files, transactions, receipts)
4. Processing steps show checkmarks
5. Results panel appears when complete

**Check Console**:
- ❌ No errors during upload
- ❌ No errors during polling
- ℹ️ Network requests are OK

**Screenshot**:
- Progress display
- Network tab showing polling requests
- Results panel

---

### Test 8: Results Display

**After Upload Completes**:

**Expected Elements**:
- ✅ Match statistics dashboard
- ✅ Match rate percentage
- ✅ Download buttons (XLSX, CSV)
- ✅ Top 5 matches preview
- ✅ Detail cards (employees, unmatched, expiry)

**Test Download Buttons**:
1. Click "Download XLSX"
   - File should download
   - Check filename format: `reconciliation_[id]_[date].xlsx`

2. Click "Download CSV"
   - File should download
   - Check filename format: `reconciliation_[id]_[date].csv`

**Check Network Tab**:
- GET `/api/sessions/{id}/report?format=xlsx` → 200 OK
- GET `/api/sessions/{id}/report?format=csv` → 200 OK
- Response type: `application/octet-stream` or similar

**Screenshot**: Results panel with download buttons

---

### Test 9: Theme Toggle

**Steps**:
1. Find theme toggle icon (top-right corner)
2. Click to switch to dark mode
3. Verify all components render correctly
4. Click again to switch back to light mode

**Expected**:
- ✅ Theme switches smoothly
- ✅ All text remains readable
- ✅ Colors adjust properly
- ✅ Icons change (sun/moon)

**Test Persistence**:
1. Switch to dark mode
2. Refresh page (Cmd+R)
3. Should still be dark mode

**Check Application Tab**:
- Open DevTools → Application → Local Storage
- Check for `theme` key
- Value should be `"dark"` or `"light"`

**Screenshot**: Dark mode and light mode comparison

---

### Test 10: Responsive Design

**Steps**:
1. Open DevTools Device Toolbar (Cmd+Shift+M)
2. Test different viewports

**Viewports to Test**:
- **Desktop**: 1920x1080
- **Tablet**: 768x1024
- **Mobile**: 375x667 (iPhone)

**Expected**:
- ✅ Layout adjusts to screen size
- ✅ Upload zone remains usable
- ✅ Buttons are touch-friendly on mobile
- ✅ Text is readable at all sizes
- ✅ No horizontal scrolling

**Screenshot**: Mobile view, tablet view

---

### Test 11: Performance

**Steps**:
1. Open DevTools → Performance tab
2. Click Record ⏺
3. Refresh page
4. Stop recording after page loads

**Check Metrics**:
- **Page Load Time**: < 2 seconds
- **First Contentful Paint (FCP)**: < 1 second
- **Largest Contentful Paint (LCP)**: < 2.5 seconds
- **Time to Interactive (TTI)**: < 3 seconds

**Screenshot**: Performance timeline

---

### Test 12: Lighthouse Audit

**Steps**:
1. Open DevTools → Lighthouse tab
2. Select:
   - ✅ Performance
   - ✅ Accessibility
   - ✅ Best Practices
   - ✅ SEO
3. Click "Analyze page load"

**Target Scores**:
- **Performance**: 90+
- **Accessibility**: 90+
- **Best Practices**: 90+
- **SEO**: 80+

**Screenshot**: Lighthouse report

---

## 📊 Test Report Template

After completing tests, fill out this report:

```markdown
# Chrome DevTools Test Report

**Date**: 2025-10-06
**Tester**: [Your Name]
**Environment**:
- Browser: Chrome [version]
- OS: macOS Darwin 24.6.0
- Docker: [version]

## Test Results

### Homepage ✅ / ❌
- Page loads: ✅
- Console clean: ✅
- Theme toggle works: ✅
- Issues: [None or list issues]

### Upload Page ✅ / ❌
- Page renders: ✅
- Form functional: ✅
- Drag-and-drop works: ✅
- Issues: [None or list issues]

### Upload Workflow ✅ / ❌
- Upload starts: ✅
- Progress displays: ✅
- Polling works: ✅
- Results show: ✅
- Issues: [None or list issues]

### Downloads ✅ / ❌
- XLSX download: ✅
- CSV download: ✅
- Issues: [None or list issues]

### Performance ✅ / ❌
- Page load time: [X seconds]
- Lighthouse score: [X/100]
- Issues: [None or list issues]

## Screenshots
[Attach screenshots of key tests]

## Critical Issues Found
1. [Issue description]
   - Severity: High/Medium/Low
   - Steps to reproduce
   - Expected vs actual behavior

## Recommendations
[Suggestions for improvements]

## Overall Status: PASS / FAIL

## Next Steps
[Based on test results]
```

---

## 🐛 Common Issues

### Issue: Page Won't Load

**Symptoms**: Connection refused, ERR_CONNECTION_REFUSED

**Fix**:
```bash
# Check Docker containers
docker-compose ps

# Start if not running
docker-compose up -d

# Check frontend logs
docker-compose logs frontend
```

### Issue: Backend API Fails

**Symptoms**: Network errors in console, 500 errors

**Fix**:
```bash
# Check backend health
curl http://localhost:8000/health

# Check backend logs
docker-compose logs backend

# Check database connection
docker-compose exec postgres psql -U ccprocessor -d credit_card_db -c "SELECT 1;"
```

### Issue: CORS Errors

**Symptoms**: "Access-Control-Allow-Origin" error in console

**Fix**:
Check backend environment in docker-compose.yml:
```yaml
ALLOWED_ORIGINS: http://localhost:3000
```

Restart backend:
```bash
docker-compose restart backend
```

### Issue: Upload Fails

**Symptoms**: Upload button doesn't work, no network request

**Fix**:
1. Check console for JavaScript errors
2. Check Network tab for failed requests
3. Verify backend is running: `curl http://localhost:8000/health`
4. Check backend logs: `docker-compose logs backend -f`

---

## ✅ After Testing

### If All Tests Pass

1. **Save test report**
2. **Take screenshots** of key features
3. **Mark tasks complete** in tasks.md
4. **Proceed to Kubernetes deployment**

### If Issues Found

1. **Document all issues** with screenshots
2. **Prioritize by severity**
3. **Fix critical issues first**
4. **Re-test after fixes**

---

## 📚 Additional Resources

- **Test Plan**: [LOCAL_TEST_PLAN.md](LOCAL_TEST_PLAN.md)
- **Diagnostics**: [DOCKER-DIAGNOSTICS.md](DOCKER-DIAGNOSTICS.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)

---

**Created**: 2025-10-06
**Status**: Ready for manual testing
