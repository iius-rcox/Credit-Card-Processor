# Azure Files Cleanup Commands

## Overview

This document contains commands to clean up Azure Files resources that are no longer needed after refactoring PDF extraction to run inline during upload (Feature 008).

**⚠️ IMPORTANT: Do not execute these commands until the new architecture has been validated in production!**

## Prerequisites

- Ensure the new inline extraction architecture is deployed and working correctly
- Verify that no active sessions are using shared storage
- Confirm that all recent uploads have completed successfully without shared storage

## Cleanup Steps

### Step 1: Delete Kubernetes PersistentVolumeClaim

```bash
kubectl delete pvc credit-card-temp-pvc -n credit-card-processor
```

**What this does**: Removes the PVC that binds to the Azure Files share. This will prevent pods from mounting the shared storage.

### Step 2: Delete Kubernetes PersistentVolume

```bash
kubectl delete pv credit-card-temp-pv
```

**What this does**: Removes the PersistentVolume definition from the cluster.

### Step 3: Delete Kubernetes Secret

```bash
kubectl delete secret azure-files-secret -n credit-card-processor
```

**What this does**: Removes the secret containing Azure Storage Account credentials.

### Step 4: Delete Azure Files Share

```bash
az storage share delete --name credit-card-temp --account-name ccproctemp2025
```

**What this does**: Deletes the file share itself from Azure Storage.

### Step 5: Delete Azure Storage Account (Optional)

```bash
az storage account delete --name ccproctemp2025 --resource-group rg_prod --yes
```

**What this does**: Completely removes the storage account. Only do this if the storage account is not used for anything else.

**⚠️ WARNING**: This is irreversible and will delete all data in the storage account!

## Verification

After cleanup, verify that:

1. **Pods are running correctly**:
   ```bash
   kubectl get pods -n credit-card-processor
   ```

2. **Backend deployment has no volume mounts**:
   ```bash
   kubectl describe deployment backend -n credit-card-processor | grep -A 10 "Mounts"
   ```

3. **Celery worker deployment has no volume mounts**:
   ```bash
   kubectl describe deployment celery-worker -n credit-card-processor | grep -A 10 "Mounts"
   ```

4. **No PVCs exist**:
   ```bash
   kubectl get pvc -n credit-card-processor
   ```

5. **Storage account is deleted** (if you deleted it):
   ```bash
   az storage account show --name ccproctemp2025 --resource-group rg_prod
   # Should return: ResourceNotFound
   ```

## Rollback Plan

If you need to rollback to the old architecture:

1. **Recreate the Azure Storage Account and File Share**:
   ```bash
   # Create storage account
   az storage account create \
     --name ccproctemp2025 \
     --resource-group rg_prod \
     --location eastus \
     --sku Standard_LRS

   # Create file share
   az storage share create \
     --name credit-card-temp \
     --account-name ccproctemp2025 \
     --quota 10
   ```

2. **Recreate the Kubernetes Secret**:
   ```bash
   STORAGE_KEY=$(az storage account keys list \
     --account-name ccproctemp2025 \
     --resource-group rg_prod \
     --query "[0].value" -o tsv)

   kubectl create secret generic azure-files-secret \
     --namespace credit-card-processor \
     --from-literal=azurestorageaccountname=ccproctemp2025 \
     --from-literal=azurestorageaccountkey=$STORAGE_KEY
   ```

3. **Reapply the old deployment manifests** with volume mounts

4. **Revert code changes** to use temp storage

## Cost Savings

After cleanup, you will save:
- **Azure Files storage**: ~$0.06/GB/month
- **Transaction costs**: Reduced by ~90% (no file I/O)
- **Bandwidth**: Minimal savings

Estimated monthly savings for 10GB storage + 10k transactions: **~$1-2/month**

## Timeline

Recommended cleanup timeline after deployment:

1. **Day 1**: Deploy new architecture
2. **Day 2-7**: Monitor for any issues
3. **Day 8**: Delete PVC, PV, and Secret
4. **Day 15**: Delete Azure Files share
5. **Day 30**: Delete Storage Account (if not needed)

## Related Documentation

- Implementation Plan: `PRPs/refactor-pdf-extraction-to-backend.md`
- Shared Storage Implementation: `docs/SHARED_STORAGE_IMPLEMENTATION_REPORT.md`
- Deployment Guide: `docs/E2E_VALIDATION_GUIDE.md`
