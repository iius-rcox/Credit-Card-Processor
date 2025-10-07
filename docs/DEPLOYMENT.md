# Deployment Guide - Credit Card Reconciliation System

**Target Platform**: Azure Kubernetes Service (AKS)
**Namespace**: `credit-card-processor`
**URL**: https://credit-card.ii-us.com

---

## Prerequisites

### Required Tools

1. **Docker** (20.10+)
   ```bash
   docker --version
   ```

2. **kubectl** (1.28+)
   ```bash
   kubectl version --client
   ```

3. **Azure CLI** (2.50+)
   ```bash
   az --version
   ```

### Azure Resources Required

- **Azure Container Registry (ACR)**: `iiusacr.azurecr.io`
- **AKS Cluster**: `dev-aks` in resource group `rg_prod`
- **Azure Key Vault**: For database credentials
- **Service Principal**: With ACR pull permissions

### Local Setup

1. **Clone the repository**
   ```bash
   cd /Users/rogercox/Credit-Card-Processor
   ```

2. **Make deployment script executable**
   ```bash
   chmod +x deploy.sh
   ```

---

## Deployment Methods

### Method 1: Automated Deployment (Recommended)

The `deploy.sh` script automates the entire deployment process:

```bash
# Deploy with 'latest' tag
./deploy.sh

# Deploy with specific version
./deploy.sh v1.0.0
```

**What it does:**
1. ✓ Checks prerequisites (Docker, kubectl, Azure CLI)
2. ✓ Authenticates with Azure and ACR
3. ✓ Builds backend Docker image
4. ✓ Builds frontend Docker image
5. ✓ Pushes images to ACR
6. ✓ Gets AKS credentials
7. ✓ Creates namespace
8. ✓ Applies all Kubernetes manifests
9. ✓ Verifies deployment

---

### Method 2: Manual Step-by-Step Deployment

If you prefer manual control or troubleshooting:

#### Step 1: Azure Authentication

```bash
# Login to Azure
az login

# Set subscription (if needed)
az account set --subscription <subscription-id>

# Login to ACR
az acr login --name iiusacr
```

#### Step 2: Build Docker Images

**Backend:**
```bash
cd backend
docker build -t iiusacr.azurecr.io/expense-backend:latest .
cd ..
```

**Frontend:**
```bash
docker build -t iiusacr.azurecr.io/expense-frontend:latest .
```

#### Step 3: Push Images to ACR

```bash
docker push iiusacr.azurecr.io/expense-backend:latest
docker push iiusacr.azurecr.io/expense-frontend:latest
```

#### Step 4: Configure kubectl

```bash
az aks get-credentials --resource-group rg_prod --name dev-aks
```

#### Step 5: Create Namespace

```bash
kubectl create namespace credit-card-processor
```

#### Step 6: Apply Kubernetes Manifests

**In this exact order:**

```bash
cd specs/005-lean-internal-deployment/contracts/k8s

# 1. Secret Provider (Azure Key Vault integration)
kubectl apply -f secret-provider.yaml

# 2. PostgreSQL Database
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n credit-card-processor --timeout=300s

# 3. Initialize Database (if needed)
# See "Database Initialization" section below

# 4. Backend API
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml

# 5. Frontend Web App
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml

# 6. Ingress (HTTPS)
kubectl apply -f ingress.yaml

# 7. CronJobs (cleanup + backup)
kubectl apply -f cleanup-cronjob.yaml
kubectl apply -f backup-cronjob.yaml
```

---

## Database Initialization

### Option A: Automatic (via Alembic)

If Alembic migrations are set up:

```bash
# Get backend pod name
BACKEND_POD=$(kubectl get pods -n credit-card-processor -l app=backend -o jsonpath='{.items[0].metadata.name}')

# Run migrations
kubectl exec -n credit-card-processor $BACKEND_POD -- alembic upgrade head
```

### Option B: Manual SQL

If using raw SQL schema:

```bash
# Copy init.sql to PostgreSQL pod
kubectl cp backend/init.sql credit-card-processor/postgres-0:/tmp/init.sql

# Execute schema
kubectl exec -n credit-card-processor postgres-0 -- \
  psql -U ccprocessor -d credit_card_db -f /tmp/init.sql

# Verify tables created
kubectl exec -n credit-card-processor postgres-0 -- \
  psql -U ccprocessor -d credit_card_db -c "\dt"
```

**Expected tables:**
- `sessions`
- `employees`
- `transactions`
- `receipts`
- `match_results`

---

## Verification

### 1. Check Pod Status

```bash
kubectl get pods -n credit-card-processor
```

**Expected output:**
```
NAME                        READY   STATUS    RESTARTS   AGE
backend-xxx                 1/1     Running   0          2m
frontend-xxx                1/1     Running   0          2m
postgres-0                  1/1     Running   0          5m
```

### 2. Check Services

```bash
kubectl get services -n credit-card-processor
```

**Expected output:**
```
NAME               TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)
backend-service    ClusterIP   10.0.x.x       <none>        8000/TCP
frontend-service   ClusterIP   10.0.x.x       <none>        3000/TCP
postgres-service   ClusterIP   10.0.x.x       <none>        5432/TCP
```

### 3. Check Ingress

```bash
kubectl get ingress -n credit-card-processor
```

**Expected output:**
```
NAME      CLASS                                HOSTS                      ADDRESS
ingress   webapprouting.kubernetes.azure.com   credit-card.ii-us.com      x.x.x.x
```

### 4. Test Health Endpoint

```bash
curl -k https://credit-card.ii-us.com/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-06T..."
}
```

### 5. Test Frontend

```bash
curl -k https://credit-card.ii-us.com
```

Should return HTML content with `<title>Expense App</title>`.

---

## Monitoring

### View Logs

**Backend:**
```bash
kubectl logs -n credit-card-processor -l app=backend --tail=50 -f
```

**Frontend:**
```bash
kubectl logs -n credit-card-processor -l app=frontend --tail=50 -f
```

**PostgreSQL:**
```bash
kubectl logs -n credit-card-processor postgres-0 --tail=50 -f
```

### Check Resource Usage

```bash
kubectl top pods -n credit-card-processor
```

### Check CronJob Status

```bash
# List CronJobs
kubectl get cronjobs -n credit-card-processor

# View cleanup job history
kubectl get jobs -n credit-card-processor | grep cleanup

# View backup job history
kubectl get jobs -n credit-card-processor | grep backup
```

### Manually Trigger CronJobs (for testing)

**Cleanup:**
```bash
kubectl create job --from=cronjob/data-cleanup test-cleanup-$(date +%s) -n credit-card-processor
```

**Backup:**
```bash
kubectl create job --from=cronjob/postgres-backup test-backup-$(date +%s) -n credit-card-processor
```

---

## Configuration

### Environment Variables

**Backend** (`backend-deployment.yaml`):
- `DATABASE_URL`: PostgreSQL connection string (from Key Vault)
- `REDIS_URL`: Redis connection string
- `ENVIRONMENT`: `production`
- `LOG_LEVEL`: `info`
- `ALLOWED_ORIGINS`: `https://credit-card.ii-us.com`

**Frontend** (`frontend-deployment.yaml`):
- `NEXT_PUBLIC_API_URL`: `http://backend-service:8000`
- `NODE_ENV`: `production`
- `NEXT_TELEMETRY_DISABLED`: `1`

### Secrets (Azure Key Vault)

The application uses Azure Key Vault CSI driver for secrets:

- **Secret Provider Class**: `azure-keyvault-secrets`
- **Mounted at**: `/mnt/secrets-store`
- **Secrets**:
  - `DATABASE_URL`: PostgreSQL connection string
  - Additional secrets as configured in Key Vault

---

## Scaling

### Manual Scaling

**Backend:**
```bash
kubectl scale deployment backend -n credit-card-processor --replicas=2
```

**Frontend:**
```bash
kubectl scale deployment frontend -n credit-card-processor --replicas=2
```

**Note**: Current configuration targets 1 replica for cost optimization (<$10/month).

---

## Updates and Rollbacks

### Deploy New Version

```bash
# Build and push new images with version tag
./deploy.sh v1.1.0

# Update deployments to use new version
kubectl set image deployment/backend -n credit-card-processor \
  backend=iiusacr.azurecr.io/expense-backend:v1.1.0

kubectl set image deployment/frontend -n credit-card-processor \
  frontend=iiusacr.azurecr.io/expense-frontend:v1.1.0
```

### Rollback to Previous Version

```bash
# View rollout history
kubectl rollout history deployment/backend -n credit-card-processor

# Rollback
kubectl rollout undo deployment/backend -n credit-card-processor
kubectl rollout undo deployment/frontend -n credit-card-processor
```

---

## Backup and Restore

### Manual Backup

```bash
# Get PostgreSQL pod
POSTGRES_POD=postgres-0

# Create backup
kubectl exec -n credit-card-processor $POSTGRES_POD -- \
  pg_dump -U ccprocessor credit_card_db > backup_$(date +%Y%m%d).sql

# Copy backup locally
kubectl cp credit-card-processor/$POSTGRES_POD:/backup_$(date +%Y%m%d).sql \
  ./backups/backup_$(date +%Y%m%d).sql
```

### Restore from Backup

```bash
# Copy backup to pod
kubectl cp ./backups/backup_20251006.sql \
  credit-card-processor/postgres-0:/tmp/restore.sql

# Restore
kubectl exec -n credit-card-processor postgres-0 -- \
  psql -U ccprocessor -d credit_card_db -f /tmp/restore.sql
```

### Automated Backups

The `backup-cronjob.yaml` runs weekly backups:
- **Schedule**: Every Sunday at 2 AM UTC
- **Destination**: Azure Blob Storage
- **Retention**: 30 days

---

## Troubleshooting

### Pod Crashes

```bash
# Check pod status
kubectl describe pod <pod-name> -n credit-card-processor

# Check recent logs
kubectl logs <pod-name> -n credit-card-processor --previous
```

### Database Connection Issues

```bash
# Test database connection from backend pod
kubectl exec -n credit-card-processor <backend-pod> -- \
  python -c "import asyncpg; print('DB check')"

# Check database secrets
kubectl get secret postgres-secrets -n credit-card-processor -o yaml
```

### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress ingress -n credit-card-processor

# Check ingress controller logs
kubectl logs -n kube-system -l app=nginx-ingress
```

### Image Pull Errors

```bash
# Verify ACR credentials
az acr login --name iiusacr

# Check image pull secret
kubectl get secret acr-secret -n credit-card-processor -o yaml

# Re-create pull secret if needed
kubectl create secret docker-registry acr-secret \
  --docker-server=iiusacr.azurecr.io \
  --docker-username=<acr-username> \
  --docker-password=<acr-password> \
  -n credit-card-processor
```

---

## Cost Monitoring

Target: **<$10/month**

### Resource Costs

- **PostgreSQL PVC**: ~$2.40/month (10Gi Premium LRS)
- **Backend Pod**: ~$1.50/month (200m CPU, 512Mi RAM)
- **Frontend Pod**: ~$0.75/month (100m CPU, 256Mi RAM)
- **ACR Storage**: <$0.50/month (minimal images)

**Total**: ~$5/month (within budget)

### Monitor Usage

```bash
# Check resource consumption
kubectl top pods -n credit-card-processor
kubectl top nodes

# View persistent volume usage
kubectl get pvc -n credit-card-processor
```

---

## Cleanup (Uninstall)

### Delete Application

```bash
# Delete all resources except PostgreSQL
kubectl delete deployment backend frontend -n credit-card-processor
kubectl delete service backend-service frontend-service -n credit-card-processor
kubectl delete ingress ingress -n credit-card-processor
kubectl delete cronjob data-cleanup postgres-backup -n credit-card-processor
```

### Delete Everything (including data)

```bash
# ⚠️ WARNING: This deletes all data permanently
kubectl delete namespace credit-card-processor
```

---

## Support and Documentation

- **Specification**: [specs/005-lean-internal-deployment/spec.md](specs/005-lean-internal-deployment/spec.md)
- **Implementation Plan**: [specs/005-lean-internal-deployment/plan.md](specs/005-lean-internal-deployment/plan.md)
- **API Contracts**: [specs/005-lean-internal-deployment/contracts/](specs/005-lean-internal-deployment/contracts/)
- **Task List**: [specs/005-lean-internal-deployment/tasks.md](specs/005-lean-internal-deployment/tasks.md)

---

**Last Updated**: 2025-10-06
**Version**: 1.0.0
**Deployed By**: Internal IT Team
