# End-to-End Validation Guide
## Kubernetes Shared Storage for PDF Processing

**Date:** October 13, 2025
**Version:** v1.0.13
**Feature:** Azure Files Shared Storage Implementation

---

## Pre-Validation Status ✅

- **Backend Pod:** Running (backend-5c7bbfbc7-wzvg5)
- **Celery Worker Pod:** Running (celery-worker-8f565f769-dv6zp)
- **Shared Storage:** Mounted at `/app/shared-temp/` (Azure Files PVC)
- **Application URL:** https://credit-card.ii-us.com
- **Storage Status:** Empty (ready for testing)

---

## Validation Steps

### Step 1: Upload Test PDFs

1. Navigate to https://credit-card.ii-us.com
2. Upload 2-3 credit card statement PDFs
3. Note the session ID displayed after upload

### Step 2: Monitor Backend Logs (Real-Time)

Open a terminal and run:
```bash
kubectl logs -f deployment/backend -n credit-card-processor | grep -E "\[UPLOAD\]|\[STORAGE\]|session"
```

**Expected Output:**
```
[UPLOAD] Saved 0000_statement.pdf (5.23 MB)
[UPLOAD] Saved 0001_receipts.pdf (12.45 MB)
[UPLOAD] Total uploaded: 17.68 MB to /app/shared-temp/credit-card-session-<uuid>
[STORAGE] Disk usage: 0.02GB / 50.00GB (0.04% used, 49.98GB free)
```

### Step 3: Verify Files in Shared Storage

```bash
# Check backend can see files
kubectl exec deployment/backend -n credit-card-processor -- sh -c "ls -lh /app/shared-temp/credit-card-session-*/  2>/dev/null || echo 'No sessions found'"

# Check celery-worker can see the SAME files
kubectl exec deployment/celery-worker -n credit-card-processor -- sh -c "ls -lh /app/shared-temp/credit-card-session-*/  2>/dev/null || echo 'No sessions found'"
```

**Expected:** Both commands show identical file listings (proves shared storage works!)

### Step 4: Monitor Celery Worker Processing

Open another terminal:
```bash
kubectl logs -f deployment/celery-worker -n credit-card-processor
```

**Expected Output:**
```
[INFO] Starting background processing for session <uuid>
[INFO] Starting extraction phase for session <uuid>
[PDF_TEXT] Processing file: 0000_statement.pdf
[REGEX_DEBUG] Found transaction: ...
[INFO] Extracted X transactions from Y PDFs
[INFO] Processing completed successfully for session <uuid>
[INFO] Cleaned up temp files for session <uuid>
```

### Step 5: Verify Transaction Extraction

Check the application UI:
- Session status should be "completed"
- Transactions count should be > 0
- Download functionality should work

### Step 6: Verify Cleanup

After processing completes:
```bash
kubectl exec deployment/backend -n credit-card-processor -- sh -c "ls -la /app/shared-temp/"
```

**Expected:** Directory is empty (files cleaned up after processing)

---

## Success Criteria Checklist

- [ ] **Upload Success:** Files uploaded successfully, session created
- [ ] **Backend Logs:** [UPLOAD] and [STORAGE] logs present
- [ ] **Shared Storage:** Both backend AND celery-worker see the same files
- [ ] **Processing Logs:** Celery worker shows PDF processing logs
- [ ] **Extraction Success:** Transactions > 0 extracted
- [ ] **Status Complete:** Session marked as "completed"
- [ ] **Download Works:** Can download reports
- [ ] **Cleanup Success:** Temp files deleted after processing

---

## Quick Monitoring Commands

### Watch Backend Logs (Uploads)
```bash
kubectl logs -f deployment/backend -n credit-card-processor --tail=100 | grep -E "\[UPLOAD\]|\[STORAGE\]|session|error|ERROR"
```

### Watch Celery Worker Logs (Processing)
```bash
kubectl logs -f deployment/celery-worker -n credit-card-processor --tail=100 | grep -E "session|PDF|extraction|transaction|error|ERROR"
```

### Check Current Sessions in Storage
```bash
kubectl exec deployment/backend -n credit-card-processor -- sh -c "find /app/shared-temp -type d -name 'credit-card-session-*' 2>/dev/null"
```

### Check Disk Usage
```bash
kubectl exec deployment/backend -n credit-card-processor -- sh -c "df -h /app/shared-temp"
```

### Get Recent Backend Activity (Last 5 minutes)
```bash
kubectl logs deployment/backend -n credit-card-processor --since=5m
```

### Get Recent Celery Activity (Last 5 minutes)
```bash
kubectl logs deployment/celery-worker -n credit-card-processor --since=5m
```

---

## Troubleshooting

### If Files Not Found in Celery Worker

**Problem:** Celery worker can't find files that backend uploaded.

**Check:**
```bash
# Verify PVC is bound
kubectl get pvc -n credit-card-processor

# Verify both pods use the same PVC
kubectl describe pod -l app=backend -n credit-card-processor | grep -A 5 "Volumes:"
kubectl describe pod -l app=celery-worker -n credit-card-processor | grep -A 5 "Volumes:"
```

**Expected:** Both show `credit-card-temp-pvc` mounted

### If Disk Usage Warning Appears

**Problem:** Log shows "High disk usage detected: >80% used"

**Action:**
```bash
# Check what's consuming space
kubectl exec deployment/backend -n credit-card-processor -- sh -c "du -sh /app/shared-temp/*"

# Manually clean if needed (should auto-clean)
kubectl exec deployment/backend -n credit-card-processor -- sh -c "rm -rf /app/shared-temp/credit-card-session-*"
```

### If Processing Hangs

**Problem:** Session stuck in "processing" status

**Check Celery Worker:**
```bash
kubectl logs deployment/celery-worker -n credit-card-processor --tail=200 | grep -i error
```

**Restart if needed:**
```bash
kubectl rollout restart deployment/celery-worker -n credit-card-processor
```

---

## Test Results Template

After completing validation, document results:

```
# E2E Validation Results - Kubernetes Shared Storage

**Date:** [Date]
**Tester:** [Name]
**Session ID:** [UUID from test]

## Results

- [ ] ✅ Upload: [Success/Failed]
  - Files: [List files uploaded]
  - Size: [Total MB]

- [ ] ✅ Shared Storage: [Success/Failed]
  - Backend sees files: [Yes/No]
  - Celery sees files: [Yes/No]

- [ ] ✅ Processing: [Success/Failed]
  - Transactions extracted: [Count]
  - Processing time: [Seconds]

- [ ] ✅ Cleanup: [Success/Failed]
  - Files removed: [Yes/No]

- [ ] ✅ Download: [Success/Failed]
  - Reports generated: [Yes/No]

## Notes

[Any issues or observations]
```

---

## Next Steps After Validation

If validation passes:
1. Mark task as complete in Archon
2. Update CLAUDE.md with new storage configuration
3. Create deployment documentation
4. Consider monitoring alerts for disk usage

If validation fails:
1. Capture all logs (backend + celery)
2. Check pod events: `kubectl describe pods -n credit-card-processor`
3. Verify PVC/PV status
4. Review error messages in detail
