# Local Docker Testing Plan with Chrome DevTools

**Date**: 2025-10-06
**Status**: Ready for Testing

---

## 🎯 Testing Objective

Test the Credit Card Reconciliation System running locally in Docker containers using Chrome DevTools to verify:
- Frontend loads correctly
- Backend API responds
- Database connectivity works
- File upload workflow functions
- UI/UX is responsive

---

## 📋 Prerequisites

### 1. Run Docker Diagnostics

```bash
cd /Users/rogercox/Credit-Card-Processor
chmod +x check-docker-status.sh
./check-docker-status.sh
```

**Expected Output:**
- All 4 containers running (postgres, redis, backend, frontend)
- Backend health: `{"status": "healthy", "database": "connected"}`
- Frontend responding on port 3000

### 2. Services Should Be Running

| Service | Container | Port | Status Check |
|---------|-----------|------|--------------|
| PostgreSQL | credit-card-postgres | 5432 | `docker-compose logs postgres` |
| Redis | credit-card-redis | 6379 | `docker-compose logs redis` |
| Backend | credit-card-backend | 8000 | `curl http://localhost:8000/health` |
| Frontend | credit-card-frontend | 3000 | `curl http://localhost:3000` |

---

## 🌐 Chrome DevTools Testing Steps

### Step 1: Open Application in Browser

**URL**: http://localhost:3000

**Expected Result:**
- Page loads successfully
- No console errors
- Theme toggle visible in top-right
- Main content displays

### Step 2: Check Network Tab

Open DevTools (F12) → Network tab

**Check for:**
- ✅ All assets load (JS, CSS, fonts)
- ✅ No 404 errors
- ✅ API proxy working (if any API calls made)

### Step 3: Check Console Tab

**Expected:**
- No JavaScript errors
- No React warnings
- No failed network requests

**Common Issues to Ignore:**
- Next.js dev mode warnings (development only)
- HMR (Hot Module Replacement) messages

### Step 4: Test Upload Page

**URL**: http://localhost:3000/upload

**Check:**
1. **Page Structure**
   - Upload form renders
   - Drag-and-drop area visible
   - File input works
   - Instructions display

2. **Drag-and-Drop**
   - Drag file over drop zone
   - Drop zone highlights (visual feedback)
   - File appears in list

3. **File Validation**
   - Upload non-PDF → Shows error
   - Upload > 10MB → Shows error
   - Upload > 100 files → Shows error
   - Upload valid PDFs → Accepted

4. **Form Submission**
   - Click "Upload Files" button
   - Progress display appears
   - Status polling starts (check Network tab)

### Step 5: Test Backend API Endpoints

Open DevTools Console and test API directly:

```javascript
// Test health endpoint
fetch('http://localhost:8000/health')
  .then(r => r.json())
  .then(console.log)

// Test API docs
window.open('http://localhost:8000/docs')
```

**Expected:**
- Health returns `{"status": "healthy", "database": "connected"}`
- Docs page loads (Swagger UI)

### Step 6: Test Upload Workflow (End-to-End)

**Prerequisites:**
- Have 2-3 sample PDF files ready (credit card statements, receipts)

**Steps:**
1. Navigate to http://localhost:3000/upload
2. Drag and drop PDFs onto upload area
3. Click "Upload Files" button
4. Observe progress display
5. Wait for processing to complete
6. Check results panel

**DevTools Monitoring:**
- **Network Tab**: Watch for POST /api/upload
- **Network Tab**: Watch for polling GET /api/sessions/{id}
- **Console Tab**: Check for errors
- **Performance Tab**: Monitor load times

### Step 7: Performance Testing

Open DevTools → Performance tab

**Record:**
1. Page load time (initial render)
2. Upload workflow (file selection → results)
3. Network waterfall (asset loading)

**Targets:**
- Page load: < 2 seconds
- File upload: < 30 seconds (for 10 files)
- UI responsiveness: < 100ms interactions

### Step 8: Responsive Design Testing

Use DevTools Device Toolbar (Ctrl+Shift+M)

**Test Viewports:**
- Desktop: 1920x1080
- Tablet: 768x1024
- Mobile: 375x667

**Check:**
- Layout adjusts properly
- Upload zone remains usable
- Buttons are touch-friendly
- Text is readable

### Step 9: Theme Toggle Testing

**Test Dark Mode:**
1. Click theme toggle icon (top-right)
2. Verify theme switches to dark
3. Check all components render correctly
4. Refresh page → theme persists

**DevTools:**
- Check localStorage for theme preference
- Verify CSS variables update

### Step 10: Error Handling Testing

**Test Error Scenarios:**

1. **Backend Down**
   ```bash
   docker-compose stop backend
   ```
   - Try to upload → Should show error
   - Error message should be user-friendly

2. **Network Failure**
   - DevTools → Network → Offline
   - Try actions → Should handle gracefully

3. **Invalid Data**
   - Upload corrupted PDF
   - Upload wrong file type
   - Check error messages

---

## 📊 Test Results Checklist

### Frontend (http://localhost:3000)

- [ ] Page loads without errors
- [ ] All assets load (no 404s)
- [ ] Console is clean (no errors)
- [ ] Theme toggle works
- [ ] Responsive on all devices
- [ ] Dark mode works correctly

### Upload Page (http://localhost:3000/upload)

- [ ] Form renders correctly
- [ ] Drag-and-drop works
- [ ] File validation works
- [ ] Error messages display
- [ ] Upload button functional

### Backend API (http://localhost:8000)

- [ ] Health endpoint responds
- [ ] API docs accessible
- [ ] Database connection works
- [ ] Redis connection works
- [ ] CORS configured correctly

### Upload Workflow

- [ ] Files upload successfully
- [ ] Progress polling works
- [ ] Status updates display
- [ ] Results panel shows data
- [ ] Download buttons work

### Performance

- [ ] Page load < 2 seconds
- [ ] Upload completes < 30 seconds
- [ ] No memory leaks
- [ ] CPU usage reasonable

---

## 🐛 Common Issues and Fixes

### Issue: Containers Not Starting

```bash
# Check logs
docker-compose logs

# Rebuild containers
docker-compose down -v
docker-compose up --build
```

### Issue: Backend Health Check Fails

```bash
# Check backend logs
docker-compose logs backend

# Check database connection
docker-compose exec postgres psql -U ccprocessor -d credit_card_db -c "SELECT 1;"
```

### Issue: Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Verify Next.js build
docker-compose exec frontend npm run build
```

### Issue: API Calls Failing (CORS)

Check backend environment:
```bash
docker-compose exec backend env | grep ALLOWED_ORIGINS
```

Should be: `ALLOWED_ORIGINS=http://localhost:3000`

### Issue: Database Not Initialized

```bash
# Check if tables exist
docker-compose exec postgres psql -U ccprocessor -d credit_card_db -c "\dt"

# Re-run init script
docker-compose down -v
docker-compose up -d postgres
# Wait 10 seconds
docker-compose up -d backend frontend
```

---

## 📝 Test Report Template

After testing, document results:

```markdown
## Test Session Report

**Date**: 2025-10-06
**Tester**: [Your Name]
**Duration**: [Test Duration]

### Environment
- OS: macOS Darwin 24.6.0
- Docker Version: [version]
- Chrome Version: [version]

### Results Summary
- Frontend: ✅ / ❌
- Backend: ✅ / ❌
- Upload Workflow: ✅ / ❌
- Performance: ✅ / ❌

### Issues Found
1. [Issue description]
   - Severity: High/Medium/Low
   - Steps to reproduce:
   - Expected behavior:
   - Actual behavior:

### Screenshots
- [Attach screenshots of any issues]

### Recommendations
- [Improvement suggestions]
```

---

## 🚀 Next Steps After Testing

### If All Tests Pass ✅

1. Document successful test run
2. Proceed with Azure AKS deployment
3. Run integration tests (T058-T066)

### If Issues Found ❌

1. Document all issues
2. Prioritize by severity
3. Fix critical issues
4. Re-test
5. Repeat until all pass

---

## 📚 Resources

- **Docker Diagnostics**: [DOCKER-DIAGNOSTICS.md](DOCKER-DIAGNOSTICS.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Documentation**: http://localhost:8000/docs
- **Task List**: [specs/005-lean-internal-deployment/tasks.md](specs/005-lean-internal-deployment/tasks.md)

---

**Created**: 2025-10-06
**Last Updated**: 2025-10-06
**Version**: 1.0.0
