# Kubernetes Manifests for Credit Card Processor

## Overview

Production-ready Kubernetes manifests for deploying the Expense Reconciliation System to Azure Kubernetes Service (AKS) cluster `dev-aks`.

**Cluster**: dev-aks
**Namespace**: credit-card-processor
**Domain**: credit-card.ii-us.com
**ACR**: iiusacr.azurecr.io

## Prerequisites

1. Azure Key Vault with secrets:
   - `postgres-db` - Database name
   - `postgres-user` - Database username
   - `postgres-password` - Database password
   - `database-url` - Full connection string

2. Azure Storage Account for backups

3. Workload Identity configured:
   - Service Account: `credit-card-processor-sa`
   - Client ID and Tenant ID set

4. ACR credentials configured:
   - Secret name: `acr-secret`

5. TLS certificate:
   - Secret name: `credit-card-tls-cert`

## Deployment Order

Deploy manifests in this order to ensure dependencies are satisfied:

### 1. Namespace and RBAC (if not exists)
```bash
kubectl create namespace credit-card-processor
```

### 2. Secrets and Configuration
```bash
# Create ACR pull secret
kubectl create secret docker-registry acr-secret \
  --docker-server=iiusacr.azurecr.io \
  --docker-username=<ACR_USERNAME> \
  --docker-password=<ACR_PASSWORD> \
  --namespace=credit-card-processor

# Apply Secret Provider Class and Service Account
kubectl apply -f secret-provider.yaml
```

### 3. Database
```bash
# Deploy PostgreSQL StatefulSet
kubectl apply -f postgres-statefulset.yaml

# Deploy PostgreSQL Service
kubectl apply -f postgres-service.yaml

# Wait for PostgreSQL to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n credit-card-processor --timeout=300s
```

### 4. Backend API
```bash
# Deploy backend
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml

# Wait for backend to be ready
kubectl wait --for=condition=ready pod -l app=backend -n credit-card-processor --timeout=300s
```

### 5. Frontend
```bash
# Deploy frontend
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml

# Wait for frontend to be ready
kubectl wait --for=condition=ready pod -l app=frontend -n credit-card-processor --timeout=300s
```

### 6. Ingress
```bash
# Deploy ingress
kubectl apply -f ingress.yaml

# Verify ingress
kubectl get ingress -n credit-card-processor
```

### 7. Maintenance Jobs
```bash
# Deploy backup and cleanup CronJobs
kubectl apply -f backup-cronjob.yaml
kubectl apply -f cleanup-cronjob.yaml

# Verify CronJobs
kubectl get cronjob -n credit-card-processor
```

## Environment Variables to Configure

Before deploying, replace these placeholders:

### secret-provider.yaml
- `${AZURE_KEYVAULT_NAME}` - Your Azure Key Vault name
- `${AZURE_TENANT_ID}` - Your Azure tenant ID
- `${AZURE_WORKLOAD_IDENTITY_CLIENT_ID}` - Workload identity client ID

### backup-cronjob.yaml
- `${AZURE_STORAGE_ACCOUNT_NAME}` - Storage account for backups

## Resource Allocations

### PostgreSQL
- CPU: 500m request, 1000m limit
- Memory: 1Gi request, 2Gi limit
- Storage: 10Gi Premium_LRS

### Backend (FastAPI)
- CPU: 200m request, 500m limit
- Memory: 512Mi request, 1Gi limit
- Replicas: 1

### Frontend (Next.js)
- CPU: 100m request, 300m limit
- Memory: 256Mi request, 512Mi limit
- Replicas: 1

## Health Checks

All deployments include:
- **Liveness probes** - Restart unhealthy containers
- **Readiness probes** - Remove from service load balancing
- **Startup probes** - Allow slow initialization

## Maintenance

### Backup Schedule
- **Frequency**: Weekly (Sunday 1:00 AM UTC)
- **Retention**: 12 weeks (84 days)
- **Storage**: Azure Blob Storage container `postgres-backups`

### Cleanup Schedule
- **Frequency**: Daily (2:00 AM UTC)
- **Retention**: 90 days
- **Tables**: sessions, transactions, uploaded_files, processing_logs

## Monitoring Commands

```bash
# Check pod status
kubectl get pods -n credit-card-processor

# View logs
kubectl logs -f deployment/backend -n credit-card-processor
kubectl logs -f deployment/frontend -n credit-card-processor
kubectl logs -f statefulset/postgres -n credit-card-processor

# Check ingress
kubectl describe ingress credit-card-ingress -n credit-card-processor

# View CronJob history
kubectl get jobs -n credit-card-processor

# Check resource usage
kubectl top pods -n credit-card-processor
```

## Rollback Procedure

```bash
# Rollback backend deployment
kubectl rollout undo deployment/backend -n credit-card-processor

# Rollback frontend deployment
kubectl rollout undo deployment/frontend -n credit-card-processor

# Check rollout status
kubectl rollout status deployment/backend -n credit-card-processor
```

## Manual Backup Trigger

```bash
# Trigger backup job manually
kubectl create job --from=cronjob/postgres-backup manual-backup-$(date +%Y%m%d-%H%M%S) -n credit-card-processor
```

## Manual Cleanup Trigger

```bash
# Trigger cleanup job manually
kubectl create job --from=cronjob/data-cleanup manual-cleanup-$(date +%Y%m%d-%H%M%S) -n credit-card-processor
```

## Security Features

1. **Non-root containers** - All containers run as non-root users
2. **Read-only root filesystem** - Where applicable
3. **Dropped capabilities** - All unnecessary Linux capabilities dropped
4. **Network policies** - Restrict pod-to-pod communication (to be added)
5. **Secrets management** - Azure Key Vault integration via CSI driver
6. **TLS termination** - HTTPS enforced at ingress level
7. **Security headers** - X-Frame-Options, X-Content-Type-Options, etc.

## Troubleshooting

### PostgreSQL Won't Start
```bash
# Check PVC status
kubectl get pvc -n credit-card-processor

# Check logs
kubectl logs -f statefulset/postgres -n credit-card-processor

# Verify secrets
kubectl get secret postgres-secrets -n credit-card-processor -o yaml
```

### Backend Can't Connect to Database
```bash
# Verify DATABASE_URL secret
kubectl exec -it deployment/backend -n credit-card-processor -- env | grep DATABASE

# Test connection from backend pod
kubectl exec -it deployment/backend -n credit-card-processor -- curl postgres-service:5432
```

### Ingress Not Working
```bash
# Check ingress controller
kubectl get ingressclass

# Verify TLS certificate
kubectl get secret credit-card-tls-cert -n credit-card-processor

# Check ingress events
kubectl describe ingress credit-card-ingress -n credit-card-processor
```

## Files Overview

| File | Purpose |
|------|---------|
| `postgres-statefulset.yaml` | PostgreSQL database with persistent storage |
| `postgres-service.yaml` | Headless service for PostgreSQL |
| `backend-deployment.yaml` | FastAPI backend application |
| `backend-service.yaml` | ClusterIP service for backend |
| `frontend-deployment.yaml` | Next.js frontend application |
| `frontend-service.yaml` | ClusterIP service for frontend |
| `ingress.yaml` | HTTPS ingress with routing rules |
| `secret-provider.yaml` | Azure Key Vault integration |
| `backup-cronjob.yaml` | Weekly database backups |
| `cleanup-cronjob.yaml` | Daily 90-day data cleanup |

## Support

For issues or questions, contact the DevOps team or refer to the main project documentation.
