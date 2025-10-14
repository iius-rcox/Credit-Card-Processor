# Deployment Guide

**Last Updated:** 2025-10-14
**Version:** Post-Refactor 008 (with migrations)

---

## 🎯 Overview

This guide covers deploying the Credit Card Processor application to Azure Kubernetes Service (AKS) with database migrations.

**Key Changes:**
- Database migrations now run automatically before deployment
- `employee_id` column is nullable (schema updated)
- Migration job ensures database schema is current

---

## 📋 Prerequisites

### Required Tools
- Azure CLI (`az`)
- Docker
- kubectl
- Access to Azure Container Registry (ACR)
- Access to AKS cluster

### Required Permissions
- ACR push/pull permissions
- AKS cluster admin access
- Kubernetes namespace access

### Environment Setup
```bash
# Login to Azure
az login

# Set subscription (if needed)
az account set --subscription "Your-Subscription-ID"

# Get AKS credentials
az aks get-credentials --resource-group rg_prod --name dev-aks
```

---

## 🚀 Deployment Methods

### Method 1: Full Deployment (Recommended)

**Use this for:** Complete deployments with frontend + backend + migrations

```bash
cd deploy

# Full deployment with default tags
./deploy-all.sh

# Or with custom tags
./deploy-all.sh v1.0.14 v1.0.14 iiusacr credit-card-processor dev-aks rg_prod
```

**What it does:**
1. Gets AKS credentials
2. Logs into ACR
3. Builds frontend Docker image
4. Pushes frontend to ACR
5. Builds backend Docker image
6. Pushes backend to ACR
7. Deletes old backend pods
8. **Runs database migrations** ⬅️ NEW
9. Updates backend deployment
10. Waits for backend rollout
11. Deletes old frontend pods
12. Updates frontend deployment

**Duration:** ~5-10 minutes

---

### Method 2: Migrations Only

**Use this for:** Running migrations without deploying code

```bash
cd deploy

# Run migrations with default settings
./run-migrations.sh

# Or with custom settings
./run-migrations.sh credit-card-processor v1.0.14 iiusacr
```

**What it does:**
1. Updates migration job with specified image tag
2. Deletes previous migration job (if exists)
3. Creates new migration job
4. Streams migration logs
5. Waits for completion
6. Reports success/failure

**When to use:**
- After merging migration PRs
- Before deploying new backend versions
- When troubleshooting database schema issues

**Duration:** ~1-2 minutes

---

### Method 3: Manual Migration (Troubleshooting)

**Use this for:** Debugging migration issues

```bash
# 1. Apply migration job manually
kubectl apply -f deploy/k8s/migration-job.yaml -n credit-card-processor

# 2. Get pod name
kubectl get pods -n credit-card-processor -l component=migration

# 3. Stream logs
kubectl logs -f <migration-pod-name> -n credit-card-processor

# 4. Check job status
kubectl get job backend-migration -n credit-card-processor

# 5. Clean up
kubectl delete job backend-migration -n credit-card-processor
```

---

## 🗄️ Database Migrations

### How Migrations Work

1. **Migration Files:** Located in `backend/migrations/versions/`
2. **Migration Job:** Kubernetes Job runs `alembic upgrade head`
3. **Automatic:** Runs before each deployment via `deploy-all.sh`

### Current Migrations

**Latest Migration:** `20251014_0516_make_employee_id_nullable.py`

**Changes:**
- Makes `employee_id` column nullable in `transactions` table
- Allows transactions with unknown/unmapped employee names
- Required for PDF extraction with incomplete data

**Previous Migrations:**
- `7833dabac7d8` - Add 'extracting' and 'matching' to session status
- `34631fc059d2` - Merge migration heads
- `34a1f65dd845` - Add employee aliases table
- `64f418bb57c8` - Add summary column to sessions
- `34992237d751` - Add progress tracking

### Creating New Migrations

```bash
# 1. Modify models in backend/src/models/
# 2. Generate migration (in backend container)
docker exec credit-card-backend alembic revision --autogenerate -m "description"

# 3. Review and edit generated migration file
# 4. Test locally
docker exec credit-card-backend alembic upgrade head

# 5. Commit migration file
git add backend/migrations/versions/
git commit -m "Add migration: description"

# 6. Deploy (migrations run automatically)
cd deploy && ./deploy-all.sh
```

---

## ✅ Verification

### Check Deployment Status

```bash
# All resources
kubectl get all -n credit-card-processor

# Deployments
kubectl get deployments -n credit-card-processor

# Pods
kubectl get pods -n credit-card-processor

# Services
kubectl get services -n credit-card-processor
```

### Check Migration Status

```bash
# Migration job status
kubectl get job backend-migration -n credit-card-processor

# Migration pod logs
kubectl logs -l component=migration -n credit-card-processor

# Database schema version
kubectl exec -it deployment/backend -n credit-card-processor -- \
  alembic current
```

### Check Backend Health

```bash
# Health endpoint
kubectl exec -it deployment/backend -n credit-card-processor -- \
  curl http://localhost:8000/api/health

# Application logs
kubectl logs -l app=backend -n credit-card-processor --tail=100

# Follow logs
kubectl logs -f deployment/backend -n credit-card-processor
```

### Verify Database Schema

```bash
# Connect to database (from AKS)
kubectl exec -it deployment/backend -n credit-card-processor -- \
  psql "$DATABASE_URL" -c "\d transactions"

# Check employee_id is nullable
kubectl exec -it deployment/backend -n credit-card-processor -- \
  psql "$DATABASE_URL" -c "\d transactions" | grep employee_id

# Expected output:
# employee_id | uuid |    |    |
# (no "not null")
```

---

## 🔧 Troubleshooting

### Migration Fails

**Problem:** Migration job fails or times out

**Steps:**
1. Check migration pod logs:
   ```bash
   kubectl logs -l component=migration -n credit-card-processor
   ```

2. Check database connectivity:
   ```bash
   kubectl exec -it deployment/backend -n credit-card-processor -- \
     psql "$DATABASE_URL" -c "SELECT 1"
   ```

3. Manually run migration:
   ```bash
   kubectl exec -it deployment/backend -n credit-card-processor -- \
     alembic upgrade head
   ```

4. Check alembic version table:
   ```bash
   kubectl exec -it deployment/backend -n credit-card-processor -- \
     psql "$DATABASE_URL" -c "SELECT * FROM alembic_version"
   ```

### Backend Pods CrashLooping

**Problem:** Backend pods restart repeatedly after deployment

**Steps:**
1. Check pod logs:
   ```bash
   kubectl logs -l app=backend -n credit-card-processor --tail=100
   ```

2. Check pod events:
   ```bash
   kubectl describe pod -l app=backend -n credit-card-processor
   ```

3. Verify database schema:
   ```bash
   # Should show latest migration
   kubectl exec -it deployment/backend -n credit-card-processor -- \
     alembic current
   ```

4. Roll back deployment:
   ```bash
   kubectl rollout undo deployment/backend -n credit-card-processor
   ```

### Schema Mismatch

**Problem:** Models don't match database schema

**Steps:**
1. Check current schema version:
   ```bash
   kubectl exec -it deployment/backend -n credit-card-processor -- \
     alembic current
   ```

2. Check for pending migrations:
   ```bash
   kubectl exec -it deployment/backend -n credit-card-processor -- \
     alembic heads
   ```

3. Run migrations manually:
   ```bash
   cd deploy && ./run-migrations.sh
   ```

4. Restart backend pods:
   ```bash
   kubectl rollout restart deployment/backend -n credit-card-processor
   ```

---

## 🔄 Rollback Procedure

### Rollback Deployment

```bash
# Rollback backend to previous version
kubectl rollout undo deployment/backend -n credit-card-processor

# Rollback to specific revision
kubectl rollout history deployment/backend -n credit-card-processor
kubectl rollout undo deployment/backend --to-revision=3 -n credit-card-processor

# Rollback frontend
kubectl rollout undo deployment/frontend -n credit-card-processor
```

### Rollback Migration

**⚠️ WARNING:** Database rollbacks can cause data loss!

```bash
# 1. Check current migration
kubectl exec -it deployment/backend -n credit-card-processor -- \
  alembic current

# 2. View migration history
kubectl exec -it deployment/backend -n credit-card-processor -- \
  alembic history

# 3. Downgrade to specific version
kubectl exec -it deployment/backend -n credit-card-processor -- \
  alembic downgrade <revision_id>

# Example: Rollback last migration
kubectl exec -it deployment/backend -n credit-card-processor -- \
  alembic downgrade -1
```

---

## 📊 Deployment Checklist

### Pre-Deployment
- [ ] Code merged to main branch
- [ ] All tests passing locally
- [ ] Database migrations tested locally
- [ ] Docker images build successfully
- [ ] ACR credentials valid
- [ ] AKS credentials valid

### During Deployment
- [ ] Monitor migration job completion
- [ ] Verify no migration errors
- [ ] Check backend pod startup
- [ ] Verify health endpoints responding
- [ ] Check application logs for errors

### Post-Deployment
- [ ] Verify deployment status (all pods Running)
- [ ] Test upload workflow in browser
- [ ] Verify database schema matches models
- [ ] Check Celery worker processing tasks
- [ ] Monitor error logs for 30 minutes
- [ ] Verify application URL accessible

---

## 📚 Related Documentation

- **Schema Fix:** `docs/COMPLETE_FIX_SUMMARY.md`
- **Feature 008:** `PRPs/refactor-pdf-extraction-to-backend.md`
- **Matching Fix:** `docs/MATCHING_STUCK_FIX.md`
- **E2E Testing:** `docs/E2E_VALIDATION_GUIDE.md`

---

## 🆘 Support

### Common Issues
- **Migration timeout:** Increase timeout in `run-migrations.sh`
- **Image pull errors:** Check ACR credentials and permissions
- **Pod startup failures:** Check resource limits and probes
- **Database connection errors:** Verify secrets and network policies

### Getting Help
1. Check pod logs: `kubectl logs <pod-name> -n credit-card-processor`
2. Check events: `kubectl get events -n credit-card-processor --sort-by='.lastTimestamp'`
3. Review documentation in `docs/` directory
4. Contact DevOps team for cluster-level issues
