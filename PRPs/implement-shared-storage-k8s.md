# Implementation Plan: Kubernetes Shared Storage for PDF Processing

## Overview
Implement Kubernetes PersistentVolume with PersistentVolumeClaim to provide shared temporary storage between backend and celery-worker pods. This fixes the critical issue where uploaded PDFs in backend pod's /tmp are not accessible to celery-worker pod, resulting in 0 transactions extracted.

## Requirements Summary
- Backend pod uploads PDFs to /tmp
- Celery worker pod needs to read PDFs from same location
- Current: Separate /tmp directories (container isolation)
- Required: Shared volume mounted to both pods
- Storage type: Temporary (can use emptyDir or Azure Files)
- Cleanup: Files should be deleted after processing

## Research Findings

### Root Cause Confirmed

**Evidence:**
```bash
# Backend pod (files exist)
/tmp/credit-card-session-88ef9590.../
  ├── 0000_Cardholder+Activity+Report+General-S-89S,DD2LJ,DFRHA (6).pdf (555KB)
  └── 0001_ReceiptImagesReportNew - 2025-04-16T092121.632.pdf (192MB)

# Celery worker pod (directory doesn't exist)
/tmp/credit-card-session-88ef9590.../ → NOT FOUND
```

**Impact:**
- Sessions complete successfully (status transitions work)
- But extraction finds 0 PDF files in temp directory
- Results in 0 transactions, 0 receipts

### Kubernetes Storage Options

**Option 1: emptyDir Volume (RECOMMENDED for temp files)**
- Shared across all pods in the deployment
- Stored on node's local disk
- Automatically cleaned up when pod deleted
- Fast (no network overhead)
- **Best for:** Temporary session files

**Option 2: Azure Files PersistentVolume**
- Persistent across pod restarts
- Shared across all nodes
- Network storage (slightly slower)
- **Best for:** Long-term storage

**Option 3: PersistentVolumeClaim with ReadWriteMany**
- Can be backed by Azure Files or NFS
- Survives pod restarts
- Shared across multiple pods
- **Best for:** Semi-permanent storage

**Selected Approach:** Use **emptyDir** for temporary storage with proper cleanup. If files need to persist beyond pod lifecycle, upgrade to Azure Files PVC.

### Technology Decisions

- **Storage Type:** emptyDir (ephemeral, shared)
- **Mount Path:** /app/shared-temp (not /tmp to avoid conflicts)
- **Size Limit:** 10Gi (configurable via sizeLimit)
- **Medium:** Default (disk) or Memory (faster but limited)
- **Cleanup Strategy:** Existing cleanup logic in upload_service.py
- **Backward Compatibility:** Update tempfile.gettempdir() path

## Implementation Tasks

### Phase 1: Create Kubernetes Volume Configuration

#### Task 1: Create emptyDir Volume in Deployment Manifests
- **Description**: Add emptyDir volume to both backend and celery-worker deployments
- **Files to modify**:
  - `deploy/k8s/backend-deployment.yaml` or equivalent
  - `deploy/k8s/celery-worker-deployment.yaml` or equivalent
- **Dependencies**: None
- **Estimated effort**: 15 minutes

**Backend Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: credit-card-processor
spec:
  replicas: 2
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: iiusacr.azurecr.io/expense-backend:v1.0.12
        ports:
        - containerPort: 8000
        env:
          # ... existing env vars ...
          - name: TEMP_STORAGE_PATH
            value: /app/shared-temp
        volumeMounts:
        - name: shared-temp-storage
          mountPath: /app/shared-temp
      volumes:
      - name: shared-temp-storage
        emptyDir:
          sizeLimit: 10Gi  # Max 10GB for temp files
```

**Celery Worker Deployment:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: celery-worker
  namespace: credit-card-processor
spec:
  replicas: 2
  selector:
    matchLabels:
      app: celery-worker
  template:
    metadata:
      labels:
        app: celery-worker
    spec:
      containers:
      - name: celery-worker
        image: iiusacr.azurecr.io/expense-backend:v1.0.12
        env:
          # ... existing env vars ...
          - name: TEMP_STORAGE_PATH
            value: /app/shared-temp
        volumeMounts:
        - name: shared-temp-storage
          mountPath: /app/shared-temp
      volumes:
      - name: shared-temp-storage
        emptyDir:
          sizeLimit: 10Gi
```

#### Task 2: Update Application Code to Use Shared Path
- **Description**: Update upload_service.py to use TEMP_STORAGE_PATH env var instead of tempfile.gettempdir()
- **Files to modify**:
  - `backend/src/services/upload_service.py:273, 416`
  - `backend/src/config.py:100-103`
- **Dependencies**: None
- **Estimated effort**: 15 minutes

**Changes:**
```python
# config.py - verify TEMP_STORAGE_PATH is configured
TEMP_STORAGE_PATH: str = Field(
    default="/tmp/credit-card-uploads",  # Default for local dev
    description="Path for temporary file storage"
)

# upload_service.py:273 - use settings instead of tempfile.gettempdir()
# BEFORE:
temp_dir = Path(tempfile.gettempdir()) / f"credit-card-session-{session_id}"

# AFTER:
from ..config import settings
temp_dir = Path(settings.TEMP_STORAGE_PATH) / f"credit-card-session-{session_id}"

# Also update line 416 (get_upload_temp_path method)
# And upload_service.py:500 (process_session_background)
```

#### Task 3: Update Docker Compose for Local Development
- **Description**: Update docker-compose.yml to use shared volume for local testing
- **Files to modify**:
  - `deploy/docker-compose.yml`
- **Dependencies**: None
- **Estimated effort**: 10 minutes

**Changes:**
```yaml
services:
  backend:
    # ... existing config ...
    environment:
      TEMP_STORAGE_PATH: /app/shared-temp
    volumes:
      - ../backend:/app
      - shared-temp:/app/shared-temp  # Add shared volume

  celery-worker:
    # ... existing config ...
    environment:
      TEMP_STORAGE_PATH: /app/shared-temp
    volumes:
      - ../backend:/app
      - shared-temp:/app/shared-temp  # Add shared volume

volumes:
  postgres_data:
    driver: local
  shared-temp:  # NEW: Shared temp storage
    driver: local
```

### Phase 2: Alternative - Azure Files PersistentVolume (If emptyDir not sufficient)

#### Task 4: Create Azure Files Storage Account (Optional)
- **Description**: Create Azure Files share for persistent shared storage
- **Dependencies**: Only if emptyDir doesn't work
- **Estimated effort**: 20 minutes

**Azure CLI:**
```bash
# Create storage account
az storage account create \
  --name ccprocessorstorage \
  --resource-group rg_prod \
  --location southcentralus \
  --sku Standard_LRS

# Create file share
az storage share create \
  --name credit-card-temp \
  --account-name ccprocessorstorage \
  --quota 50
```

#### Task 5: Create Kubernetes Secret for Storage Credentials (Optional)
- **Description**: Store Azure Files credentials as K8s secret
- **Dependencies**: Task 4 complete
- **Estimated effort**: 10 minutes

**Commands:**
```bash
# Get storage key
STORAGE_KEY=$(az storage account keys list \
  --resource-group rg_prod \
  --account-name ccprocessorstorage \
  --query '[0].value' -o tsv)

# Create secret
kubectl create secret generic azure-files-secret \
  --from-literal=azurestorageaccountname=ccprocessorstorage \
  --from-literal=azurestorageaccountkey=$STORAGE_KEY \
  -n credit-card-processor
```

#### Task 6: Create PersistentVolume and PersistentVolumeClaim (Optional)
- **Description**: Create PV and PVC using Azure Files
- **Files to create**:
  - `deploy/k8s/shared-storage-pv.yaml`
  - `deploy/k8s/shared-storage-pvc.yaml`
- **Dependencies**: Task 5 complete
- **Estimated effort**: 15 minutes

**PersistentVolume:**
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: credit-card-temp-pv
spec:
  capacity:
    storage: 50Gi
  accessModes:
    - ReadWriteMany
  azureFile:
    secretName: azure-files-secret
    shareName: credit-card-temp
    readOnly: false
  mountOptions:
  - dir_mode=0777
  - file_mode=0777
```

**PersistentVolumeClaim:**
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: credit-card-temp-pvc
  namespace: credit-card-processor
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 50Gi
  volumeName: credit-card-temp-pv
```

### Phase 3: Deploy and Test

#### Task 7: Update ConfigMap with New TEMP_STORAGE_PATH
- **Description**: Update backend-config ConfigMap with new temp path
- **Files to modify**: K8s ConfigMap
- **Dependencies**: Task 2 complete (code updated)
- **Estimated effort**: 5 minutes

**Command:**
```bash
kubectl create configmap backend-config \
  --from-literal=TEMP_STORAGE_PATH=/app/shared-temp \
  -n credit-card-processor \
  --dry-run=client -o yaml | kubectl apply -f -
```

#### Task 8: Apply Updated Deployment Manifests
- **Description**: Apply the deployment manifests with volume mounts
- **Dependencies**: Tasks 1, 3, 7 complete
- **Estimated effort**: 10 minutes

**Commands:**
```bash
# Apply backend deployment
kubectl apply -f deploy/k8s/backend-deployment.yaml

# Apply celery-worker deployment
kubectl apply -f deploy/k8s/celery-worker-deployment.yaml

# Wait for rollout
kubectl rollout status deployment/backend -n credit-card-processor
kubectl rollout status deployment/celery-worker -n credit-card-processor
```

#### Task 9: Verify Shared Storage is Mounted
- **Description**: Verify both pods can access the shared volume
- **Dependencies**: Task 8 complete
- **Estimated effort**: 10 minutes

**Verification:**
```bash
# Create test file in backend
kubectl exec deployment/backend -n credit-card-processor -- sh -c "echo 'test' > /app/shared-temp/test.txt"

# Read from celery-worker
kubectl exec deployment/celery-worker -n credit-card-processor -- sh -c "cat /app/shared-temp/test.txt"

# Should output: "test"

# Cleanup
kubectl exec deployment/backend -n credit-card-processor -- sh -c "rm /app/shared-temp/test.txt"
```

### Phase 4: Update Application Configuration

#### Task 10: Update Backend Environment Variables
- **Description**: Ensure TEMP_STORAGE_PATH is set in all environments
- **Files to modify**:
  - Local: `backend/.env`
  - Docker: `deploy/docker-compose.yml` (environment section)
  - K8s: ConfigMap or deployment env
- **Dependencies**: Task 2 complete
- **Estimated effort**: 10 minutes

#### Task 11: Test File Upload and Processing
- **Description**: Upload PDFs and verify celery worker can access them
- **Dependencies**: Tasks 8-10 complete
- **Estimated effort**: 15 minutes

**Test Steps:**
1. Upload PDFs via https://credit-card.ii-us.com
2. Check backend pod for files in /app/shared-temp
3. Check celery worker pod for same files
4. Monitor celery logs for extraction
5. Verify transactions > 0

### Phase 5: Validation and Cleanup

#### Task 12: Implement Automatic Cleanup
- **Description**: Verify existing cleanup logic works with new path
- **Files to check**:
  - `backend/src/services/upload_service.py:618-629` (cleanup_temp_files)
- **Dependencies**: Task 11 complete
- **Estimated effort**: 10 minutes

**Verification:**
- Files cleaned up after processing
- No orphaned files in /app/shared-temp
- Disk space not growing unbounded

#### Task 13: Add Monitoring for Disk Usage
- **Description**: Add logging to track temp storage disk usage
- **Files to modify**:
  - `backend/src/services/upload_service.py`
- **Dependencies**: None
- **Estimated effort**: 15 minutes

**Implementation:**
```python
async def _save_files_to_temp_with_progress(...):
    # After file save (line 289):
    logger.info(f"[UPLOAD] Saved {safe_filename} ({file_size / 1024 / 1024:.2f} MB)")

    # At end of method (after line 307):
    total_mb = total_bytes_uploaded / 1024 / 1024
    logger.info(f"[UPLOAD] Total uploaded: {total_mb:.2f} MB to {temp_dir}")

    # Check disk usage
    import shutil
    disk_usage = shutil.disk_usage(temp_dir)
    logger.info(f"[STORAGE] Disk usage: {disk_usage.used / 1024**3:.2f}GB / {disk_usage.total / 1024**3:.2f}GB")
```

#### Task 14: Production Deployment and Validation
- **Description**: Deploy v1.0.13 with shared storage and verify extraction works
- **Dependencies**: All previous tasks complete
- **Estimated effort**: 20 minutes

**Deployment:**
```bash
# Build v1.0.13 (with TEMP_STORAGE_PATH changes)
cd backend
docker build -t iiusacr.azurecr.io/expense-backend:v1.0.13 .
docker push iiusacr.azurecr.io/expense-backend:v1.0.13

# Apply deployments (with volume mounts)
kubectl apply -f deploy/k8s/backend-deployment.yaml
kubectl apply -f deploy/k8s/celery-worker-deployment.yaml

# Wait for rollout
kubectl rollout status deployment/backend -n credit-card-processor
kubectl rollout status deployment/celery-worker -n credit-card-processor
```

#### Task 15: End-to-End Validation with Real PDFs
- **Description**: Upload production PDFs and verify transactions are extracted
- **Dependencies**: Task 14 complete
- **Estimated effort**: 15 minutes

**Expected Results:**
- Session created
- Files accessible to both backend and celery-worker
- Extraction logs show [PDF_TEXT] and [REGEX_DEBUG]
- Transactions > 0 extracted
- Status: completed
- Download reports work

## Codebase Integration Points

### Files to Modify

1. **`backend/src/config.py:100-103`**
   - Ensure TEMP_STORAGE_PATH is defined
   - Default: /app/shared-temp (K8s) or /tmp/credit-card-uploads (local)

2. **`backend/src/services/upload_service.py`**
   - **Line 273**: Use settings.TEMP_STORAGE_PATH instead of tempfile.gettempdir()
   - **Line 416**: Update get_upload_temp_path()
   - **Line 500**: Update process_session_background temp_dir path

3. **`deploy/docker-compose.yml`**
   - Add shared volume definition
   - Mount to both backend and celery-worker
   - Set TEMP_STORAGE_PATH environment variable

### New Files to Create

1. **`deploy/k8s/backend-deployment.yaml`** (if doesn't exist)
   - Backend deployment with emptyDir volume mount
   - TEMP_STORAGE_PATH environment variable

2. **`deploy/k8s/celery-worker-deployment.yaml`** (if doesn't exist)
   - Celery worker deployment with emptyDir volume mount
   - TEMP_STORAGE_PATH environment variable

3. **`deploy/k8s/shared-storage-pv.yaml`** (optional, if using Azure Files)
   - PersistentVolume definition with Azure Files backend

4. **`deploy/k8s/shared-storage-pvc.yaml`** (optional, if using Azure Files)
   - PersistentVolumeClaim for shared storage

### Existing K8s Resources to Check

```bash
# Find existing deployment files
find deploy/ -name "*deployment*.yaml" -o -name "*deploy*.yaml"

# Check current deployments
kubectl get deployment -n credit-card-processor -o yaml > current-deployments.yaml
```

## Technical Design

### Current Architecture (BROKEN)

```
┌─────────────────┐         ┌──────────────────┐
│  Backend Pod    │         │ Celery Worker Pod│
│                 │         │                  │
│  /tmp/          │         │  /tmp/           │
│   └─ session-X/ │  ✗      │   └─ (empty)     │
│      ├─ pdf1    │         │                  │
│      └─ pdf2    │         │                  │
└─────────────────┘         └──────────────────┘
     ↑                              ↓
     │                              │
  Upload PDFs              Can't find PDFs!
  (saves to /tmp)          (looks in own /tmp)
```

### Fixed Architecture (WITH SHARED VOLUME)

```
┌─────────────────┐         ┌──────────────────┐
│  Backend Pod    │         │ Celery Worker Pod│
│                 │         │                  │
│  /app/shared-   │         │  /app/shared-    │
│  temp/          │  ✓      │  temp/           │
│   └─ session-X/ │◄───────►│   └─ session-X/  │
│      ├─ pdf1    │         │      ├─ pdf1     │
│      └─ pdf2    │         │      └─ pdf2     │
└─────────────────┘         └──────────────────┘
     ↑                              ↓
     │         emptyDir Volume      │
     │      (shared across pods)    │
     │                              │
  Upload PDFs              Reads same PDFs!
  (saves to shared)        (accesses shared)
```

### emptyDir Volume Characteristics

**Lifecycle:**
- Created when pod starts
- Exists as long as pod exists
- Shared among all containers in the pod
- Deleted when pod deleted
- **Important:** Each deployment replica has its own emptyDir

**Sharing Across Pods:**
- emptyDir is **per-pod**, not per-deployment
- For multi-replica deployments, files in one pod's emptyDir are NOT visible to another pod
- **Solution:** Use ReadWriteMany PVC (Azure Files) OR ensure Celery worker processes files uploaded to the SAME pod

**Best Approach for Production:**
Use **Azure Files PVC** with **ReadWriteMany** so all backend and celery-worker pods share the same storage.

### Recommended Final Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  Backend Pod 1  │         │ Celery Worker 1  │
│                 │         │                  │
│  /app/shared ───┼────┐    │  /app/shared ────┼────┐
└─────────────────┘    │    └──────────────────┘    │
                       │                             │
┌─────────────────┐    │    ┌──────────────────┐    │
│  Backend Pod 2  │    │    │ Celery Worker 2  │    │
│                 │    │    │                  │    │
│  /app/shared ───┼────┤    │  /app/shared ────┼────┤
└─────────────────┘    │    └──────────────────┘    │
                       ▼                             ▼
              ┌─────────────────────────────────────┐
              │  Azure Files Share (ReadWriteMany)  │
              │    credit-card-temp (50GB)          │
              └─────────────────────────────────────┘
```

**All pods** (backend-1, backend-2, celery-1, celery-2) share the **same** Azure Files volume.

## Dependencies and Libraries

**No new application dependencies.** Infrastructure changes only:
- Kubernetes volumes (built-in)
- Azure Files (if using PVC option)
- Environment variables (existing config system)

## Testing Strategy

### Phase 1 Testing (emptyDir)
1. Apply deployment manifests
2. Verify volume mounted in both pods
3. Test file write from backend, read from celery-worker
4. Upload PDF and verify extraction

### Phase 2 Testing (Azure Files PVC)
1. Create Azure Files share
2. Create K8s secret and PVC
3. Apply deployment manifests with PVC
4. Verify multi-pod access
5. Test with multiple concurrent uploads

### Validation Checklist
- [ ] Backend can write files to shared path
- [ ] Celery worker can read files from shared path
- [ ] Files persist during processing
- [ ] Files cleaned up after processing
- [ ] Extraction finds PDFs (count > 0)
- [ ] Transactions extracted (count > 0)
- [ ] Multiple uploads work concurrently
- [ ] Disk usage monitored

## Success Criteria

- [ ] Shared volume configured and mounted
- [ ] Both pods use same TEMP_STORAGE_PATH
- [ ] Backend writes PDFs to shared location
- [ ] Celery worker reads PDFs from shared location
- [ ] Extraction logs show [PROCESS_PDF] messages
- [ ] Transactions > 0 extracted from PDFs
- [ ] Sessions complete with data
- [ ] Download functionality works
- [ ] No orphaned files in shared storage

## Notes and Considerations

### emptyDir Limitation
**Critical:** emptyDir is **pod-specific**. With 2 backend replicas and 2 celery replicas:
- Backend Pod 1's emptyDir ≠ Backend Pod 2's emptyDir
- Celery Worker 1's emptyDir ≠ Celery Worker 2's emptyDir

**Problem:**
If upload goes to Backend Pod 1, but Celery Worker 2 picks up the task, it won't find the files!

**Solutions:**
1. **Use Azure Files PVC** (ReadWriteMany) - all pods share same storage
2. **Use sticky sessions** - ensure same backend pod handles upload and celery processing
3. **Store files in database** - upload to DB, celery reads from DB

**Recommended:** Use **Azure Files PVC** for true multi-pod sharing.

### Cost Considerations
- emptyDir: Free (uses node disk)
- Azure Files: ~$0.06/GB/month ($3/month for 50GB)

### Performance Considerations
- emptyDir: Fast (local disk)
- Azure Files: Slower (network storage) but acceptable for PDF processing

---

## Quick Reference: Implementation Steps

### Quick Win (emptyDir - Single Replica)
```bash
# 1. Scale to 1 replica (temporary)
kubectl scale deployment/backend --replicas=1 -n credit-card-processor
kubectl scale deployment/celery-worker --replicas=1 -n credit-card-processor

# 2. Add volume to deployments (edit YAML)
# 3. Apply deployments
# 4. Test
```

### Production Solution (Azure Files)
```bash
# 1. Create Azure Files share
# 2. Create K8s secret with credentials
# 3. Create PV and PVC
# 4. Update deployments to use PVC
# 5. Scale back to 2 replicas
# 6. Test multi-pod scenario
```

---

*This plan is ready for execution with `/execute-plan PRPs/implement-shared-storage-k8s.md`*
