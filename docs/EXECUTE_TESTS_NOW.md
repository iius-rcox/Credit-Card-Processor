# Execute Tests Now - Manual Steps

**Status**: ⚠️ Unable to execute bash commands or control Chrome browser directly
**Action Required**: Manual execution by user

---

## 🚨 Current Situation

I've prepared all testing infrastructure but cannot execute bash commands or control the Chrome browser instance directly due to environment limitations. You'll need to run the tests manually.

---

## ✅ What's Already Prepared

1. **Test Scripts**:
   - ✅ `run-full-test-sequence.sh` - Complete automated test
   - ✅ `check-docker-status.sh` - Diagnostic checks

2. **Documentation**:
   - ✅ `LOCAL_TEST_PLAN.md` - Detailed test plan
   - ✅ `TESTING_SUMMARY.md` - Quick start guide
   - ✅ `DOCKER-DIAGNOSTICS.md` - Troubleshooting

3. **Docker Infrastructure**:
   - ✅ `docker-compose.yml` - Updated with new Dockerfiles
   - ✅ `Dockerfile` - Frontend build
   - ✅ `backend/Dockerfile` - Backend build

---

## 🚀 Execute Tests - Copy/Paste These Commands

### Option 1: Automated Full Test (Recommended)

```bash
# Open Terminal and run:
cd /Users/rogercox/Credit-Card-Processor
chmod +x run-full-test-sequence.sh
./run-full-test-sequence.sh
```

This single script will:
1. ✅ Stop and clean existing containers
2. ✅ Build and start all 4 containers
3. ✅ Wait 30 seconds for initialization
4. ✅ Check container status
5. ✅ Test health endpoints
6. ✅ Run full diagnostics
7. ✅ Generate summary report

**Expected Duration**: ~2-3 minutes

---

### Option 2: Step-by-Step Manual Execution

If you prefer manual control:

#### Step 1: Clean Environment
```bash
cd /Users/rogercox/Credit-Card-Processor
docker-compose down -v
```

#### Step 2: Build and Start Containers
```bash
docker-compose up --build -d
```

#### Step 3: Wait for Services
```bash
sleep 30
```

#### Step 4: Check Container Status
```bash
docker-compose ps
```

**Expected Output**:
```
NAME                      STATUS
credit-card-postgres      Up (healthy)
credit-card-redis         Up (healthy)
credit-card-backend       Up
credit-card-frontend      Up
```

#### Step 5: Test Backend Health
```bash
curl http://localhost:8000/health
```

**Expected Response**:
```json
{"status":"healthy","database":"connected","timestamp":"2025-10-06T..."}
```

#### Step 6: Test Frontend
```bash
curl -I http://localhost:3000
```

**Expected Response**:
```
HTTP/1.1 200 OK
```

#### Step 7: Run Full Diagnostics
```bash
chmod +x check-docker-status.sh
./check-docker-status.sh
```

---

## 🌐 Chrome DevTools Testing

After containers are running:

### Step 1: Open Browser
```bash
open http://localhost:3000
```

Or manually navigate to: **http://localhost:3000**

### Step 2: Open DevTools
- Press `F12` or `Cmd+Option+I`
- Or right-click → Inspect

### Step 3: Check Console Tab
Look for:
- ❌ Red errors (should be none)
- ⚠️ Yellow warnings (minor, acceptable)
- ℹ️ Info messages (normal)

### Step 4: Check Network Tab
1. Refresh page (`Cmd+R`)
2. Watch for:
   - All resources load (200 OK)
   - No 404 errors
   - API proxy working

### Step 5: Navigate to Upload Page
```
http://localhost:3000/upload
```

Check:
- ✅ Form renders correctly
- ✅ Drag-and-drop zone visible
- ✅ Instructions display
- ✅ No console errors

### Step 6: Test Upload Workflow

**You'll need sample PDF files for this test.**

1. **Drag PDFs** onto upload zone
2. **Watch Network Tab** for:
   - POST `/api/upload` - File upload request
   - Response should be 202 Accepted
   - GET `/api/sessions/{id}` - Status polling (every 2 seconds)
3. **Observe Progress Display**:
   - Progress bar moves
   - Statistics update
   - Processing steps show checkmarks
4. **Check Results Panel**:
   - Match statistics display
   - Download buttons appear
   - Top matches preview shows

### Step 7: Test Downloads
1. Click "Download XLSX" button
2. Click "Download CSV" button
3. Verify files download correctly

---

## 📊 Test Results to Capture

Create a text file with results:

```bash
# Save test results
cd /Users/rogercox/Credit-Card-Processor
./run-full-test-sequence.sh > test-results-$(date +%Y%m%d-%H%M%S).txt 2>&1
```

**What to Document**:
- ✅ All containers running
- ✅ Health check passing
- ✅ Frontend accessible
- ✅ Upload workflow works
- ✅ No critical errors
- ⚠️ Any warnings or issues found

---

## 🐛 Troubleshooting

### Issue: Containers Won't Start

```bash
# Check what's using ports
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis

# Kill processes if needed
kill -9 <PID>

# Try again
docker-compose down -v
docker-compose up --build -d
```

### Issue: Backend Health Fails

```bash
# Check backend logs
docker-compose logs backend --tail=100

# Check database logs
docker-compose logs postgres --tail=50

# Verify database initialized
docker-compose exec postgres psql -U ccprocessor -d credit_card_db -c "\dt"
```

### Issue: Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend --tail=100

# Verify Next.js build
docker-compose exec frontend ls -la .next/

# Restart frontend
docker-compose restart frontend
```

### Issue: Upload Fails

**Check Backend Logs**:
```bash
docker-compose logs backend -f
```

Then try upload again and watch for errors.

**Common Issues**:
- CORS error → Check ALLOWED_ORIGINS in docker-compose.yml
- 500 error → Backend crash, check logs
- Timeout → Database not connected, check postgres health

---

## ✅ Success Checklist

After running tests, verify:

### Container Status
- [ ] Postgres container: Up (healthy)
- [ ] Redis container: Up (healthy)
- [ ] Backend container: Up
- [ ] Frontend container: Up

### Health Checks
- [ ] Backend `/health` returns 200 OK
- [ ] Backend database connection: "connected"
- [ ] Frontend returns 200 OK
- [ ] No critical errors in logs

### Frontend Testing
- [ ] Homepage loads without errors
- [ ] Console is clean (no red errors)
- [ ] Theme toggle works
- [ ] Dark mode persists

### Upload Workflow
- [ ] Upload page renders
- [ ] Drag-and-drop works
- [ ] File validation works (PDF only, max 10MB)
- [ ] Upload starts successfully
- [ ] Progress polling works (Network tab)
- [ ] Results display correctly
- [ ] Download buttons work

### Performance
- [ ] Page load < 2 seconds
- [ ] Upload completes < 30 seconds (for ~10 files)
- [ ] No memory leaks (check DevTools Memory tab)
- [ ] Responsive on mobile (DevTools Device Mode)

---

## 📈 Expected Test Results

### Container Status
```
NAME                      STATUS        PORTS
credit-card-postgres      Up (healthy)  0.0.0.0:5432->5432/tcp
credit-card-redis         Up (healthy)  0.0.0.0:6379->6379/tcp
credit-card-backend       Up            0.0.0.0:8000->8000/tcp
credit-card-frontend      Up            0.0.0.0:3000->3000/tcp
```

### Backend Health Response
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-06T12:34:56.789Z"
}
```

### Frontend Response
```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
```

### Database Tables
```
             List of relations
 Schema |      Name      | Type  |    Owner
--------+----------------+-------+-------------
 public | sessions       | table | ccprocessor
 public | employees      | table | ccprocessor
 public | transactions   | table | ccprocessor
 public | receipts       | table | ccprocessor
 public | match_results  | table | ccprocessor
```

---

## 🎯 Next Steps After Testing

### If All Tests Pass ✅

1. **Create Test Report**:
   ```bash
   echo "Test Date: $(date)" > TEST_REPORT.txt
   echo "Status: PASSED" >> TEST_REPORT.txt
   echo "All containers running" >> TEST_REPORT.txt
   echo "Health checks passing" >> TEST_REPORT.txt
   echo "Upload workflow functional" >> TEST_REPORT.txt
   ```

2. **Update Progress**:
   - Mark T048-T049 as complete ✅
   - Ready for Kubernetes deployment (T050-T057)

3. **Proceed to Deployment**:
   ```bash
   ./deploy.sh v1.0.0
   ```

### If Issues Found ❌

1. **Document Issues**:
   ```bash
   echo "Test Date: $(date)" > TEST_ISSUES.txt
   docker-compose logs >> TEST_ISSUES.txt
   ```

2. **Share Output**: Send test results for debugging

3. **Wait for Fixes**: Don't proceed to deployment until all tests pass

---

## 📞 Need Help?

If you encounter issues:

1. **Capture Logs**:
   ```bash
   docker-compose logs > full-logs.txt
   ```

2. **Check Diagnostics Guide**: [DOCKER-DIAGNOSTICS.md](DOCKER-DIAGNOSTICS.md)

3. **Review Test Plan**: [LOCAL_TEST_PLAN.md](LOCAL_TEST_PLAN.md)

---

## 🎬 Quick Command Reference

```bash
# Start everything
cd /Users/rogercox/Credit-Card-Processor
./run-full-test-sequence.sh

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop everything
docker-compose down

# Clean restart
docker-compose down -v && docker-compose up --build -d

# Open in browser
open http://localhost:3000
open http://localhost:8000/docs
```

---

## ⏱️ Estimated Timeline

- **Container startup**: 1-2 minutes
- **Health checks**: 30 seconds
- **Manual testing**: 10-15 minutes
- **Total**: ~15-20 minutes

---

**Created**: 2025-10-06
**Status**: Ready for manual execution
**Action**: Run `./run-full-test-sequence.sh` in terminal
