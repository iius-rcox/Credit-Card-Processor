# Local Docker Testing - Ready to Test!

**Date**: 2025-10-06
**Status**: ✅ All testing infrastructure ready

---

## 🎉 What's Been Set Up

### 1. Docker Infrastructure ✅
- **docker-compose.yml** - Updated to use new Dockerfiles
- **backend/Dockerfile** - Production-ready backend image
- **Dockerfile** - Next.js frontend with standalone build
- **.dockerignore** files - Optimized build contexts

### 2. Testing Tools ✅
- **check-docker-status.sh** - Automated diagnostics script
- **DOCKER-DIAGNOSTICS.md** - Comprehensive troubleshooting guide
- **LOCAL_TEST_PLAN.md** - Complete testing checklist
- **TESTING_SUMMARY.md** - This file

### 3. Documentation ✅
- **DEPLOYMENT.md** - Production deployment guide
- **DEPLOYMENT_READY.md** - Deployment readiness checklist

---

## 🚀 Quick Start - 3 Steps to Test

### Step 1: Start Docker Containers

```bash
cd /Users/rogercox/Credit-Card-Processor

# Stop any existing containers and clean volumes
docker-compose down -v

# Build and start all services
docker-compose up --build -d

# Wait 30 seconds for services to initialize
sleep 30
```

### Step 2: Run Diagnostics

```bash
# Make diagnostic script executable
chmod +x check-docker-status.sh

# Run diagnostics
./check-docker-status.sh
```

**Expected Output:**
```
✅ All 4 containers running
✅ Backend health: {"status": "healthy", "database": "connected"}
✅ Frontend responding on port 3000
✅ PostgreSQL initialized with tables
✅ Redis connected
```

### Step 3: Open in Chrome DevTools

```bash
# Open in default browser
open http://localhost:3000

# Or manually navigate to:
# - Frontend: http://localhost:3000
# - Upload Page: http://localhost:3000/upload
# - API Docs: http://localhost:8000/docs
# - Health Check: http://localhost:8000/health
```

**In Chrome:**
1. Press `F12` or `Cmd+Option+I` to open DevTools
2. Check **Console** tab for errors
3. Check **Network** tab for failed requests
4. Check **Application** tab for localStorage (theme)

---

## 📊 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3000 | Main application UI |
| **Upload Page** | http://localhost:3000/upload | File upload workflow |
| **Backend API** | http://localhost:8000 | FastAPI backend |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Health Check** | http://localhost:8000/health | System health status |

---

## 🧪 Quick Health Check

Run these commands to verify everything is working:

```bash
# Check backend health
curl http://localhost:8000/health

# Should return:
# {"status":"healthy","database":"connected","timestamp":"2025-10-06T..."}

# Check frontend
curl -I http://localhost:3000

# Should return:
# HTTP/1.1 200 OK

# Check containers
docker-compose ps

# Should show 4 containers with "Up" status
```

---

## 🎯 Testing Checklist

Use [LOCAL_TEST_PLAN.md](LOCAL_TEST_PLAN.md) for detailed testing steps.

### Quick Test List:

- [ ] ✅ Frontend loads (http://localhost:3000)
- [ ] ✅ No console errors in DevTools
- [ ] ✅ Backend health check passes
- [ ] ✅ API docs accessible (http://localhost:8000/docs)
- [ ] ✅ Upload page renders (http://localhost:3000/upload)
- [ ] ✅ Drag-and-drop works
- [ ] ✅ File validation works (PDF only, max 10MB)
- [ ] ✅ Theme toggle works (top-right corner)
- [ ] ✅ Dark mode persists after refresh
- [ ] ✅ Responsive design (test mobile view)

### Upload Workflow Test:

**Prerequisites:** Have 2-3 sample PDF files ready

1. Navigate to http://localhost:3000/upload
2. Drag PDFs onto drop zone
3. Click "Upload Files"
4. Watch progress in DevTools Network tab
5. Verify status polling (GET /api/sessions/{id} every 2 seconds)
6. Check results display
7. Test download buttons (XLSX/CSV)

---

## 🐛 Troubleshooting

### Containers Won't Start

```bash
# Check what's using the ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill conflicting processes
kill -9 <PID>

# Rebuild containers
docker-compose down -v
docker-compose up --build
```

### Backend Connection Errors

```bash
# Check backend logs
docker-compose logs backend --tail=50

# Check database logs
docker-compose logs postgres --tail=50

# Verify database tables exist
docker-compose exec postgres psql -U ccprocessor -d credit_card_db -c "\dt"
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend --tail=50

# Rebuild frontend
docker-compose up --build frontend
```

### Database Not Initialized

The `init.sql` file should auto-run on first startup. If tables don't exist:

```bash
# Manually initialize
docker-compose exec postgres psql -U ccprocessor -d credit_card_db -f /docker-entrypoint-initdb.d/init.sql

# Or restart with fresh database
docker-compose down -v
docker-compose up -d
```

---

## 📈 Progress Update

**Overall**: 54/72 tasks (75%) complete

**Just Completed:**
- ✅ T048: Backend Docker image
- ✅ T049: Frontend Docker image
- ✅ Local testing infrastructure

**Currently Testing:**
- 🧪 Local Docker deployment
- 🧪 End-to-end upload workflow
- 🧪 UI/UX validation

**Next Phase:**
- T050-T057: Kubernetes deployment (8 tasks)
- T058-T066: Integration tests (9 tasks)
- T067-T072: Polish (6 tasks)

---

## 🎬 Chrome DevTools Testing Guide

### 1. Console Tab
**What to Check:**
- No red error messages
- No React warnings
- No failed fetch requests

**Common DevTools Commands:**
```javascript
// Test backend health
fetch('http://localhost:8000/health').then(r => r.json()).then(console.log)

// Check localStorage theme
localStorage.getItem('theme')

// Monitor API calls
console.log('Watching network requests...')
```

### 2. Network Tab
**What to Monitor:**
- POST /api/upload (file upload)
- GET /api/sessions/{id} (status polling every 2 seconds)
- GET /api/sessions/{id}/report (download)
- All requests should return 200 OK (or 202 Accepted for upload)

**Filter by:**
- XHR/Fetch - API calls
- JS - JavaScript bundles
- CSS - Stylesheets
- Font - Web fonts

### 3. Application Tab
**What to Check:**
- **Local Storage**: `theme` key should exist
- **Session Storage**: Check if used
- **Cookies**: Should be minimal
- **Cache Storage**: Next.js caching

### 4. Performance Tab
**Record and Analyze:**
1. Click Record ⏺
2. Refresh page
3. Stop recording
4. Analyze:
   - Page load time (target: < 2s)
   - Layout shifts
   - JavaScript execution time

### 5. Lighthouse Tab
**Run Audit:**
1. Click "Generate report"
2. Check scores:
   - Performance: Target 90+
   - Accessibility: Target 90+
   - Best Practices: Target 90+
   - SEO: Target 80+

---

## 📸 Expected Screenshots

### Homepage (http://localhost:3000)
- Clean layout
- Theme toggle in top-right
- No error messages
- Footer with information

### Upload Page (http://localhost:3000/upload)
- Upload form centered
- Drag-and-drop area
- File input button
- Instructions section
- "How It Works" steps

### Upload in Progress
- Progress bar showing percentage
- Statistics cards (files, transactions, receipts)
- Processing steps with checkmarks
- Status message

### Results Panel
- Match statistics dashboard
- Download buttons (XLSX, CSV)
- Match rate percentage
- Top 5 matches preview
- Detail cards

### API Docs (http://localhost:8000/docs)
- Swagger UI interface
- 5 endpoints visible:
  - POST /api/upload
  - GET /api/sessions
  - GET /api/sessions/{id}
  - GET /api/sessions/{id}/report
  - DELETE /api/sessions/{id}

---

## ✅ Success Criteria

Before proceeding to Kubernetes deployment:

### Functional Requirements
- [x] All containers start successfully
- [ ] Backend health check passes
- [ ] Frontend loads without errors
- [ ] Upload page renders correctly
- [ ] File validation works
- [ ] Upload workflow completes
- [ ] Progress polling works
- [ ] Results display correctly
- [ ] Download buttons work
- [ ] Theme toggle works

### Non-Functional Requirements
- [ ] Page load < 2 seconds
- [ ] Upload < 30 seconds (10 files)
- [ ] No memory leaks (test with DevTools)
- [ ] Console clean (no errors)
- [ ] Mobile responsive
- [ ] Dark mode works
- [ ] Accessibility (tab navigation)

---

## 🚀 Next Steps

### If All Tests Pass ✅

1. **Document Results**
   - Take screenshots
   - Note any warnings (non-critical)
   - Measure performance metrics

2. **Proceed to Kubernetes Deployment**
   - Run `./deploy.sh` (T050-T057)
   - Deploy to Azure AKS
   - Run integration tests (T058-T066)

3. **Update Progress**
   - Mark local testing complete
   - Update tasks.md
   - Create test report

### If Issues Found ❌

1. **Document Issues**
   - Screenshot errors
   - Copy error messages
   - Note steps to reproduce

2. **Fix Issues**
   - Critical: Database connection, API errors
   - High: Upload workflow, validation
   - Medium: UI bugs, styling
   - Low: Minor improvements

3. **Re-test**
   - Fix and re-run diagnostics
   - Verify fix works
   - Complete all checklist items

---

## 📚 Resources

- **Local Testing Plan**: [LOCAL_TEST_PLAN.md](LOCAL_TEST_PLAN.md) - Detailed test cases
- **Docker Diagnostics**: [DOCKER-DIAGNOSTICS.md](DOCKER-DIAGNOSTICS.md) - Troubleshooting
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md) - Production deployment
- **Task List**: [specs/005-lean-internal-deployment/tasks.md](specs/005-lean-internal-deployment/tasks.md)
- **API Contracts**: [specs/005-lean-internal-deployment/contracts/](specs/005-lean-internal-deployment/contracts/)

---

## 🎊 Summary

✅ **Infrastructure Ready**: Docker containers configured
✅ **Diagnostics Ready**: Automated health checks
✅ **Documentation Ready**: Complete testing guides
🧪 **Testing Phase**: Run diagnostics and test with Chrome DevTools

**Current Status**: Ready for local testing!

**Time to Test**: ~15-30 minutes for complete workflow

**Commands to Run:**
```bash
cd /Users/rogercox/Credit-Card-Processor
docker-compose down -v && docker-compose up --build -d
sleep 30
./check-docker-status.sh
open http://localhost:3000
```

---

**Created**: 2025-10-06
**Version**: 1.0.0
**Progress**: 54/72 tasks (75%)
