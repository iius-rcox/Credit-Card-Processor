# Research: Lean Internal Deployment

## Executive Summary

This research covers deployment architecture for a Next.js 15 + FastAPI expense reconciliation system to Azure Kubernetes Service (AKS) with PostgreSQL StatefulSet, Azure Key Vault integration, 90-day data lifecycle, and a cost target of <$10/month. The system is designed for 1-2 internal users with minimal traffic.

---

## 1. PostgreSQL StatefulSet on AKS

### Decision
Use PostgreSQL 16 StatefulSet with Azure Disk Premium LRS storage class for persistent volume claims (PVC), running with resource limits of 500m CPU and 1Gi RAM.

### Rationale
- **Persistent Data**: StatefulSet guarantees stable network identity and persistent storage across pod restarts
- **Automatic Provisioning**: Azure Disk CSI driver automatically provisions and attaches disks
- **Cost-Effective**: Premium LRS offers balanced IOPS (120 baseline) and cost for database workloads
- **Single-User Scale**: Low traffic pattern doesn't justify managed Azure Database for PostgreSQL (~$30/month minimum)
- **Control**: Full control over schema migrations, backups, and database configuration

### Alternatives Considered

| Option | Cost | Pros | Cons | Verdict |
|--------|------|------|------|---------|
| Azure Database for PostgreSQL | $30-50/month | Managed backups, HA | Exceeds budget by 3-5x | ❌ Rejected |
| Azure Files | ~$2/month | Shared storage | 50-100x slower for DB workloads | ❌ Rejected |
| Local Storage (emptyDir) | $0 | Fast | Data loss on pod restart | ❌ Rejected |
| Azure Disk Premium LRS | ~$2/month | Good IOPS, persistent | Single-zone availability | ✅ **Selected** |
| Azure Disk Standard SSD | ~$1/month | Cheaper | Lower IOPS (500 vs 120) | ⚠️ Acceptable fallback |

### Implementation Notes

**Storage Class Configuration**:
```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: postgres-premium-lrs
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_LRS
  kind: Managed
reclaimPolicy: Retain  # Prevent accidental deletion
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

**Best Practices**:
1. **Init Containers**: Use init container for schema migration before PostgreSQL starts
   ```yaml
   initContainers:
   - name: schema-migration
     image: migrate/migrate
     command: ['migrate', '-path', '/migrations', '-database', 'postgres://...', 'up']
   ```

2. **Resource Limits**: Conservative limits for 1-2 users
   - CPU: 500m (burst to 1 core if node available)
   - Memory: 1Gi (sufficient for connection pool + query cache)
   - Storage: 10Gi (90 days × 1000 sessions × ~500KB avg = ~5GB, 2x headroom)

3. **Connection Limits**: Set `max_connections=20` in postgresql.conf (default 100 is wasteful)

4. **Readiness/Liveness Probes**: Use `pg_isready` command for health checks
   ```yaml
   livenessProbe:
     exec:
       command: ['pg_isready', '-U', 'postgres']
     initialDelaySeconds: 30
     periodSeconds: 10
   ```

5. **Backup Strategy**: Use pg_dump in CronJob to Azure Blob Storage (covered in section 6)

### Performance Expectations
- Premium LRS 10GB disk: 120 IOPS baseline, 500 IOPS burst
- Query latency: <10ms for indexed queries (sessions by ID, date range)
- Write throughput: 50-100 inserts/sec (far exceeds 1-2 user needs)

---

## 2. Azure Key Vault + AKS Workload Identity

### Decision
Use Azure Key Vault Secrets Store CSI Driver with workload identity federation, exposing secrets as mounted volumes via SecretProviderClass. No Kubernetes secrets stored in manifests or etcd.

### Rationale
- **Existing Infrastructure**: Key Vault already provisioned (matches n8n pattern)
- **Enhanced Security**: Secrets never stored in Kubernetes etcd, only mounted at runtime
- **Automatic Sync**: CSI driver polls Key Vault every 2 minutes for secret rotation
- **No Code Changes**: Applications read secrets from file paths (e.g., `/mnt/secrets/db-password`)
- **Audit Trail**: All secret access logged in Azure Monitor

### Alternatives Considered

| Option | Security | Complexity | Verdict |
|--------|----------|------------|---------|
| Kubernetes Secrets (base64) | Low | Low | ❌ Secrets in etcd, not encrypted at rest |
| Sealed Secrets | Medium | Medium | ❌ Requires SealedSecret CRD, extra tooling |
| External Secrets Operator | High | High | ❌ Additional controller overhead |
| Managed Identity (aad-pod-identity) | High | Medium | ❌ Deprecated in favor of workload identity |
| **Workload Identity + CSI** | **High** | **Medium** | ✅ **Selected** - Azure best practice |

### Setup Steps

**1. Enable AKS Workload Identity**:
```bash
az aks update \
  --resource-group insulations-rg \
  --name insulations-aks \
  --enable-oidc-issuer \
  --enable-workload-identity
```

**2. Create Managed Identity**:
```bash
az identity create \
  --resource-group insulations-rg \
  --name expense-reconciliation-identity

IDENTITY_CLIENT_ID=$(az identity show --name expense-reconciliation-identity \
  --resource-group insulations-rg --query clientId -o tsv)
```

**3. Grant Key Vault Access**:
```bash
az keyvault set-policy \
  --name insulations-keyvault \
  --object-id $(az identity show --name expense-reconciliation-identity \
    --resource-group insulations-rg --query principalId -o tsv) \
  --secret-permissions get list
```

**4. Create Federated Credential**:
```bash
OIDC_ISSUER=$(az aks show --resource-group insulations-rg \
  --name insulations-aks --query oidcIssuerProfile.issuerUrl -o tsv)

az identity federated-credential create \
  --name expense-reconciliation-fedcred \
  --identity-name expense-reconciliation-identity \
  --resource-group insulations-rg \
  --issuer $OIDC_ISSUER \
  --subject system:serviceaccount:default:expense-reconciliation-sa
```

**5. Annotate Service Account**:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: expense-reconciliation-sa
  namespace: default
  annotations:
    azure.workload.identity/client-id: "<IDENTITY_CLIENT_ID>"
```

**6. Deploy SecretProviderClass**:
```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: expense-reconciliation-secrets
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "false"
    clientID: "<IDENTITY_CLIENT_ID>"
    keyvaultName: insulations-keyvault
    tenantId: "<TENANT_ID>"
    objects: |
      array:
        - |
          objectName: postgres-password
          objectType: secret
          objectVersion: ""
        - |
          objectName: nextauth-secret
          objectType: secret
          objectVersion: ""
```

**7. Mount in Pod**:
```yaml
spec:
  serviceAccountName: expense-reconciliation-sa
  volumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: expense-reconciliation-secrets
  containers:
  - name: api
    volumeMounts:
    - name: secrets-store
      mountPath: "/mnt/secrets"
      readOnly: true
```

### Implementation Notes

**Secret Access Pattern**:
```python
# FastAPI - Read DB password from file
def get_db_password() -> str:
    with open('/mnt/secrets/postgres-password', 'r') as f:
        return f.read().strip()

DATABASE_URL = f"postgresql+asyncpg://postgres:{get_db_password()}@postgres:5432/expenses"
```

**Graceful Degradation**:
If CSI driver fails to mount (rare), pod will remain in `ContainerCreating` state. Monitor with:
```bash
kubectl describe pod <pod-name> | grep "FailedMount"
```

**Rotation Handling**:
- CSI driver polls every 2 minutes by default
- Application must re-read file on connection failure (SQLAlchemy handles automatically on reconnect)
- No pod restart required for secret rotation

**Cost**: ~$0.05/month for Key Vault secret operations (6 secrets × 720 reads/month × $0.03/10,000 operations)

---

## 3. SQLAlchemy Async with FastAPI

### Decision
Use SQLAlchemy 2.0+ async mode with `asyncpg` driver, connection pooling (pool_size=5, max_overflow=10), and repository pattern for data access. Async sessions injected via FastAPI dependency injection.

### Rationale
- **Non-Blocking**: Async I/O prevents blocking FastAPI event loop during database queries
- **Efficient Resource Usage**: Small pool size (5) sufficient for 1-2 concurrent users
- **Connection Reuse**: Pooling reduces connection overhead (PostgreSQL connection ~10ms handshake)
- **Modern SQLAlchemy**: 2.0+ style with async/await is the recommended approach
- **Type Safety**: Works seamlessly with Pydantic models and FastAPI validation

### Alternatives Considered

| Option | Concurrency | Complexity | Performance | Verdict |
|--------|-------------|------------|-------------|---------|
| Sync SQLAlchemy | Blocking | Low | Acceptable for 1-2 users | ❌ Blocks event loop |
| Raw asyncpg | Non-blocking | High | Fastest | ❌ No ORM, manual SQL |
| Tortoise ORM | Non-blocking | Medium | Good | ❌ Less mature ecosystem |
| **SQLAlchemy Async** | **Non-blocking** | **Medium** | **Good** | ✅ **Selected** - Industry standard |
| Higher pool (20+) | Non-blocking | Medium | Wasteful | ❌ Overkill for low traffic |

### Implementation Pattern

**Database Session Factory**:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

# Read password from Key Vault mount
def get_db_url() -> str:
    with open('/mnt/secrets/postgres-password', 'r') as f:
        password = f.read().strip()
    return f"postgresql+asyncpg://postgres:{password}@postgres:5432/expenses"

# Create engine with connection pool
engine = create_async_engine(
    get_db_url(),
    echo=False,  # Set to True for SQL logging in dev
    pool_size=5,  # Max 5 persistent connections
    max_overflow=10,  # Allow 10 additional connections on burst
    pool_pre_ping=True,  # Verify connection before checkout
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Allow access to objects after commit
)
```

**Dependency Injection**:
```python
from typing import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

**Repository Pattern**:
```python
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, data: dict) -> Session:
        session = Session(**data)
        self.db.add(session)
        await self.db.flush()  # Get ID without committing
        return session

    async def get_session_by_id(self, session_id: int) -> Session | None:
        result = await self.db.execute(
            select(Session).where(Session.id == session_id)
        )
        return result.scalar_one_or_none()

    async def list_sessions(self, limit: int = 100) -> list[Session]:
        result = await self.db.execute(
            select(Session).order_by(Session.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def delete_expired_sessions(self, days: int = 90) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.db.execute(
            delete(Session).where(Session.created_at < cutoff)
        )
        return result.rowcount
```

**FastAPI Route Example**:
```python
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    repo = SessionRepository(db)
    session = await repo.create_session(data.dict())
    return session

@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    repo = SessionRepository(db)
    sessions = await repo.list_sessions(limit)
    return sessions
```

### Connection Pool Sizing

**Formula**: `pool_size + max_overflow ≥ max_concurrent_requests`

For 1-2 users:
- Typical concurrent requests: 1-2 (upload + list view)
- Peak concurrent requests: 5 (upload + multiple tabs)
- Pool size: 5 persistent + 10 overflow = **15 total**

**PostgreSQL Configuration**:
```conf
# postgresql.conf
max_connections = 20  # pool_size + overflow + buffer for migrations
shared_buffers = 256MB  # 25% of RAM (1Gi)
effective_cache_size = 768MB  # 75% of RAM
```

### Performance Expectations
- Connection checkout: <1ms (from pool)
- Simple query (by ID): 1-5ms
- Complex query (join 3 tables): 10-50ms
- Insert with indexes: 5-10ms

### Error Handling
```python
from sqlalchemy.exc import IntegrityError, OperationalError

try:
    session = await repo.create_session(data)
except IntegrityError as e:
    raise HTTPException(status_code=400, detail="Duplicate session ID")
except OperationalError as e:
    # Connection lost, pool will retry
    raise HTTPException(status_code=503, detail="Database unavailable")
```

---

## 4. Next.js 15 App Router + FastAPI

### Decision
Use Next.js 15 App Router with Server Components for data fetching (session list) and Client Components for interactive forms (upload). API communication via native `fetch` with error boundaries and loading states.

### Rationale
- **Optimized Data Fetching**: Server Components fetch data on the server, reducing client bundle and improving initial load
- **Client Interactivity**: Upload form with progress tracking requires client-side state management
- **Reduced Bundle Size**: Server Components don't ship JavaScript to the client (30-40% reduction)
- **Built-in Streaming**: App Router supports streaming SSR for faster perceived performance
- **No Extra Dependencies**: Native fetch API replaces axios (saves 20KB gzipped)

### Alternatives Considered

| Option | Bundle Size | Performance | Complexity | Verdict |
|--------|-------------|-------------|------------|---------|
| All Client Components | Large | Slower SSR | Low | ❌ Unnecessary JS |
| All Server Components | Small | Faster | High | ❌ No interactivity |
| **Hybrid (Server + Client)** | **Medium** | **Optimal** | **Medium** | ✅ **Selected** |
| Pages Router (Next.js 12) | Medium | Good | Low | ❌ Legacy pattern |
| axios for API calls | Large | Good | Low | ❌ Extra dependency |
| **Native fetch** | **Small** | **Good** | **Low** | ✅ **Selected** |

### Architecture Pattern

**App Structure**:
```
app/
├── layout.tsx              # Root layout (Server Component)
├── page.tsx               # Dashboard (Server Component)
├── sessions/
│   ├── page.tsx          # Session list (Server Component)
│   └── [id]/
│       └── page.tsx      # Session detail (Server Component)
└── upload/
    └── page.tsx          # Upload form (Client Component)

components/
├── upload-form.tsx        # Client Component (file upload)
├── progress-display.tsx   # Client Component (progress bar)
├── results-panel.tsx      # Client Component (results table)
└── session-list.tsx       # Server Component (read-only list)
```

### Server Component Pattern (Data Fetching)

**Session List Page**:
```typescript
// app/sessions/page.tsx
import { SessionList } from '@/components/session-list'

async function getSessions() {
  const res = await fetch('http://api:8000/sessions', {
    cache: 'no-store',  // Always fetch fresh data
    headers: {
      'Accept': 'application/json',
    },
  })

  if (!res.ok) {
    throw new Error('Failed to fetch sessions')
  }

  return res.json()
}

export default async function SessionsPage() {
  const sessions = await getSessions()

  return (
    <div className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Expense Sessions</h1>
      <SessionList sessions={sessions} />
    </div>
  )
}
```

**Server Component Benefits**:
- Fetch data directly on server (no API key exposure)
- Use internal service name (`http://api:8000`)
- Zero JavaScript shipped for read-only content
- Automatic error boundaries

### Client Component Pattern (Interactivity)

**Upload Form**:
```typescript
// app/upload/page.tsx
'use client'

import { useState } from 'react'
import { UploadForm } from '@/components/upload-form'
import { ProgressDisplay } from '@/components/progress-display'
import { ResultsPanel } from '@/components/results-panel'

export default function UploadPage() {
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState(null)

  const handleUpload = async (files: File[]) => {
    setUploading(true)
    setProgress(0)

    const formData = new FormData()
    files.forEach((file) => formData.append('files', file))

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) throw new Error('Upload failed')

      const data = await res.json()
      setResults(data)
    } catch (error) {
      console.error('Upload error:', error)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="container mx-auto py-8">
      <UploadForm onUpload={handleUpload} disabled={uploading} />
      {uploading && <ProgressDisplay progress={progress} />}
      {results && <ResultsPanel data={results} />}
    </div>
  )
}
```

### API Client Configuration

**Environment Variables**:
```bash
# .env.local (development)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Kubernetes ConfigMap (production)
NEXT_PUBLIC_API_URL=http://api:8000
```

**API Helper**:
```typescript
// lib/api-client.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`

  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail)
  }

  return res.json()
}

// Usage
const sessions = await apiRequest<Session[]>('/sessions')
```

### Error Handling

**Error Boundary**:
```typescript
// app/error.tsx
'use client'

export default function Error({
  error,
  reset,
}: {
  error: Error
  reset: () => void
}) {
  return (
    <div className="container mx-auto py-8">
      <h2 className="text-2xl font-bold text-red-600">Something went wrong!</h2>
      <p className="mt-4">{error.message}</p>
      <button
        onClick={reset}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded"
      >
        Try again
      </button>
    </div>
  )
}
```

**Loading States**:
```typescript
// app/sessions/loading.tsx
export default function Loading() {
  return (
    <div className="container mx-auto py-8">
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded"></div>
          ))}
        </div>
      </div>
    </div>
  )
}
```

### Build Optimization

**Next.js Config**:
```javascript
// next.config.js
module.exports = {
  output: 'standalone',  // Minimal Docker image
  experimental: {
    serverActions: true,  // Enable server actions
  },
  images: {
    unoptimized: true,  // No external image optimization
  },
}
```

**Docker Multi-Stage Build**:
```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
```

### Performance Expectations
- Server Component render: 20-50ms
- Client hydration: 100-200ms
- API request (internal): 10-30ms
- Total page load (Server Component): 200-400ms
- Total page load (Client Component): 500-800ms

---

## 5. webapprouting Ingress (AKS)

### Decision
Use AKS webapprouting addon with Application Gateway Ingress Controller (AGIC), configured for HTTPS redirect and TLS termination using existing Azure certificate. Matches n8n ingress pattern.

### Rationale
- **Existing Infrastructure**: webapprouting already enabled in AKS cluster (confirmed from n8n pattern)
- **Azure-Native**: AGIC integrates tightly with Azure Application Gateway (Layer 7 load balancer)
- **Managed Certificates**: Azure Key Vault certificate automatically synced to Application Gateway
- **HTTPS Enforcement**: Simple annotation for HTTP→HTTPS redirect
- **No Extra Cost**: Application Gateway already provisioned for n8n

### Alternatives Considered

| Option | Cost | Complexity | Integration | Verdict |
|--------|------|------------|-------------|---------|
| nginx Ingress Controller | $0 | Medium | Manual cert management | ❌ Duplicate solution |
| Traefik | $0 | Medium | Not in AKS | ❌ Extra deployment |
| Azure Front Door | $35+/month | Low | Excellent | ❌ Exceeds budget |
| **webapprouting (AGIC)** | **$0** | **Low** | **Native** | ✅ **Selected** - Matches n8n |

### Implementation

**Ingress Manifest**:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: expense-reconciliation
  namespace: default
  annotations:
    # HTTPS redirect
    appgw.ingress.kubernetes.io/ssl-redirect: "true"
    # Use existing certificate
    appgw.ingress.kubernetes.io/appgw-ssl-certificate: "insulations-cert"
    # Backend protocol
    appgw.ingress.kubernetes.io/backend-protocol: "http"
    # Health probe path
    appgw.ingress.kubernetes.io/health-probe-path: "/api/health"
    # Timeout for long uploads
    appgw.ingress.kubernetes.io/request-timeout: "300"
spec:
  ingressClassName: webapprouting.kubernetes.azure.com
  tls:
  - hosts:
    - expenses.insulations.com
    secretName: insulations-cert-secret  # Synced from Key Vault
  rules:
  - host: expenses.insulations.com
    http:
      paths:
      # Next.js frontend
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
      # FastAPI backend
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 8000
```

### Certificate Management

**Existing Certificate in Key Vault**:
```bash
# Verify certificate exists
az keyvault certificate show \
  --vault-name insulations-keyvault \
  --name insulations-cert

# Output shows:
# - Subject: CN=*.insulations.com
# - Valid: 365 days
# - Auto-renewal enabled
```

**Certificate Sync to Application Gateway**:
Application Gateway automatically syncs certificates from Key Vault when referenced in ingress annotations. No manual steps required.

### DNS Configuration

**Azure DNS Zone**:
```bash
# Get Application Gateway public IP
APPGW_IP=$(az network public-ip show \
  --resource-group insulations-rg \
  --name appgw-public-ip \
  --query ipAddress -o tsv)

# Create A record
az network dns record-set a add-record \
  --resource-group insulations-rg \
  --zone-name insulations.com \
  --record-set-name expenses \
  --ipv4-address $APPGW_IP
```

### Path Routing Strategy

**Frontend (Next.js)**:
- Root path `/` → Frontend service (port 3000)
- Static assets `/_next/*` → Frontend service
- API routes `/api/*` → Backend service (see below)

**Backend (FastAPI)**:
- API prefix `/api` → API service (port 8000)
- Swagger docs `/api/docs` → API service
- Health check `/api/health` → API service

**Path Rewrite (Not Required)**:
AGIC forwards full path to backend. FastAPI app should mount at `/api` prefix:
```python
app = FastAPI(root_path="/api")  # All routes prefixed with /api
```

### Health Checks

**Application Gateway Probe**:
```yaml
# Annotation in ingress
appgw.ingress.kubernetes.io/health-probe-path: "/api/health"
appgw.ingress.kubernetes.io/health-probe-interval: "30"
appgw.ingress.kubernetes.io/health-probe-timeout: "5"
appgw.ingress.kubernetes.io/health-probe-unhealthy-threshold: "3"
```

**FastAPI Health Endpoint**:
```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
```

### HTTPS Redirect Flow

1. User requests `http://expenses.insulations.com`
2. Application Gateway receives request
3. AGIC annotation triggers 301 redirect to `https://expenses.insulations.com`
4. User browser follows redirect
5. HTTPS request terminates at Application Gateway
6. Backend communication over HTTP (internal cluster network)

### Request Timeout Configuration

**Upload Timeout**:
```yaml
# Ingress annotation
appgw.ingress.kubernetes.io/request-timeout: "300"  # 5 minutes
```

**Why 5 Minutes**:
- Credit card statement PDFs: 1-5MB each
- Upload 10 files: 10-50MB total
- Slow connection (1 Mbps): 50MB × 8 bits / 1 Mbps = 400 seconds
- 300 seconds = reasonable timeout for 3-4 files on slow connection

### Cost Analysis

**Application Gateway**:
- Already provisioned for n8n: $0 incremental
- Shared capacity: Standard_v2 SKU
- Data processing: ~1GB/month (1-2 users) = negligible

**DNS**:
- Azure DNS A record: $0.50/month per million queries
- Expected queries: ~1,000/month = $0.0005 (negligible)

**Total Ingress Cost**: ~$0 incremental

### Troubleshooting

**Check Ingress Status**:
```bash
kubectl describe ingress expense-reconciliation
# Look for:
# - Events: Certificate synced, backend configured
# - Address: Application Gateway public IP assigned
```

**Test HTTPS Redirect**:
```bash
curl -I http://expenses.insulations.com
# Expect: HTTP/1.1 301 Moved Permanently
# Location: https://expenses.insulations.com
```

**Test Backend Routing**:
```bash
curl https://expenses.insulations.com/api/health
# Expect: {"status":"healthy","timestamp":"..."}
```

---

## 6. 90-Day TTL Data Lifecycle

### Decision
Use Kubernetes CronJob for daily hard delete of sessions older than 90 days, with weekly pg_dump backup to Azure Blob Storage before cleanup. No soft delete or archive (middleware staging environment).

### Rationale
- **Definitive Expiration**: Hard delete ensures data is fully removed (GDPR compliance if needed)
- **Backup Safety Net**: Weekly backup provides 4-week recovery window
- **Simple Implementation**: SQL DELETE statement with date filter (idempotent)
- **No Archive Complexity**: Middleware staging system doesn't require long-term data retention
- **Cost-Effective**: Blob Storage backups ~$0.10/month (200MB × 4 weeks)

### Alternatives Considered

| Option | Storage Cost | Complexity | Recovery | Verdict |
|--------|--------------|------------|----------|---------|
| Soft Delete (deleted_at) | Same | Low | Easy | ❌ Data still in DB |
| Archive to Blob Storage | $0.10/month | Medium | Medium | ❌ Overkill for staging |
| Archive to Azure SQL | $5-10/month | High | Easy | ❌ Exceeds budget |
| **Hard Delete + Backup** | **$0.10/month** | **Low** | **Medium** | ✅ **Selected** |
| No Backup | $0 | Low | None | ❌ Too risky |

### Cleanup CronJob

**Manifest**:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-expired-sessions
  namespace: default
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM UTC
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 5
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: expense-reconciliation-sa
          restartPolicy: OnFailure
          containers:
          - name: cleanup
            image: <your-registry>/expense-api:latest
            command:
            - python
            - -c
            - |
              import asyncio
              from app.database import AsyncSessionLocal
              from app.repositories import SessionRepository

              async def cleanup():
                  async with AsyncSessionLocal() as db:
                      repo = SessionRepository(db)
                      deleted = await repo.delete_expired_sessions(days=90)
                      print(f"Deleted {deleted} expired sessions")
                      await db.commit()

              asyncio.run(cleanup())
            env:
            - name: POSTGRES_HOST
              value: postgres
            - name: POSTGRES_DB
              value: expenses
            volumeMounts:
            - name: secrets-store
              mountPath: "/mnt/secrets"
              readOnly: true
          volumes:
          - name: secrets-store
            csi:
              driver: secrets-store.csi.k8s.io
              readOnly: true
              volumeAttributes:
                secretProviderClass: expense-reconciliation-secrets
```

**SQL Implementation** (in SessionRepository):
```python
async def delete_expired_sessions(self, days: int = 90) -> int:
    """Delete sessions older than specified days. Returns count deleted."""
    from datetime import datetime, timedelta

    cutoff = datetime.utcnow() - timedelta(days=days)

    # Hard delete with cascade (deletes line_items, reconciliations)
    result = await self.db.execute(
        delete(Session).where(Session.created_at < cutoff)
    )

    return result.rowcount
```

### Backup CronJob

**Manifest**:
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup-postgres
  namespace: default
spec:
  schedule: "0 1 * * 0"  # Weekly on Sunday at 1 AM UTC
  successfulJobsHistoryLimit: 4  # Keep 4 weeks
  failedJobsHistoryLimit: 2
  jobTemplate:
    spec:
      template:
        spec:
          serviceAccountName: expense-reconciliation-sa
          restartPolicy: OnFailure
          containers:
          - name: backup
            image: postgres:16-alpine
            command:
            - sh
            - -c
            - |
              # Create backup file with timestamp
              TIMESTAMP=$(date +%Y%m%d_%H%M%S)
              BACKUP_FILE="/tmp/expenses_backup_${TIMESTAMP}.sql.gz"

              # Run pg_dump and compress
              pg_dump -h postgres -U postgres -d expenses | gzip > $BACKUP_FILE

              # Upload to Azure Blob Storage using azcopy
              azcopy copy $BACKUP_FILE \
                "https://insulationsstorage.blob.core.windows.net/backups/${BACKUP_FILE}?${SAS_TOKEN}"

              echo "Backup completed: $BACKUP_FILE"
            env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-password
                  key: password
            - name: SAS_TOKEN
              valueFrom:
                secretKeyRef:
                  name: azure-storage-sas
                  key: token
```

**Azure Blob Storage Setup**:
```bash
# Create container for backups
az storage container create \
  --name backups \
  --account-name insulationsstorage \
  --public-access off

# Generate SAS token (valid 1 year, write-only)
az storage container generate-sas \
  --name backups \
  --account-name insulationsstorage \
  --permissions w \
  --expiry $(date -u -d "+1 year" '+%Y-%m-%dT%H:%MZ') \
  --output tsv

# Store SAS token in Key Vault
az keyvault secret set \
  --vault-name insulations-keyvault \
  --name azure-storage-sas \
  --value "<SAS_TOKEN>"
```

### Lifecycle Policy

**Azure Blob Lifecycle Management**:
```bash
# Create lifecycle policy (delete backups after 28 days)
az storage account management-policy create \
  --account-name insulationsstorage \
  --policy @lifecycle-policy.json
```

**lifecycle-policy.json**:
```json
{
  "rules": [
    {
      "name": "DeleteOldBackups",
      "enabled": true,
      "type": "Lifecycle",
      "definition": {
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["backups/"]
        },
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterModificationGreaterThan": 28
            }
          }
        }
      }
    }
  ]
}
```

### Idempotency Guarantees

**Cleanup Job**:
- WHERE clause with timestamp: `created_at < NOW() - INTERVAL '90 days'`
- Safe to re-run: Deletes only rows matching criteria
- No state stored: Each run is independent

**Backup Job**:
- Unique filename with timestamp: `expenses_backup_20250106_010000.sql.gz`
- No overwrites: Each backup is separate file
- Safe to re-run: Creates new backup file

### Monitoring

**Check CronJob Status**:
```bash
# List recent cleanup jobs
kubectl get jobs -l job-name=cleanup-expired-sessions --sort-by=.metadata.creationTimestamp

# View logs from last cleanup
kubectl logs job/cleanup-expired-sessions-<timestamp>

# Expected output:
# Deleted 42 expired sessions
```

**Check Backup Status**:
```bash
# List recent backups
kubectl get jobs -l job-name=backup-postgres --sort-by=.metadata.creationTimestamp

# View backup files in Azure
az storage blob list \
  --container-name backups \
  --account-name insulationsstorage \
  --query "[].{Name:name, Size:properties.contentLength, Modified:properties.lastModified}" \
  --output table
```

### Recovery Procedure

**Restore from Backup**:
```bash
# Download backup file
az storage blob download \
  --container-name backups \
  --name expenses_backup_20250106_010000.sql.gz \
  --account-name insulationsstorage \
  --file backup.sql.gz

# Port-forward to PostgreSQL pod
kubectl port-forward svc/postgres 5432:5432

# Restore database
gunzip -c backup.sql.gz | psql -h localhost -U postgres -d expenses

# Verify restoration
psql -h localhost -U postgres -d expenses -c "SELECT COUNT(*) FROM sessions;"
```

### Cost Breakdown

**Blob Storage**:
- Backup size: ~200MB compressed (estimate 10,000 sessions × 20KB avg)
- Retention: 4 weeks (4 backups)
- Total storage: 800MB = 0.8GB
- Cost: 0.8GB × $0.02/GB/month = **$0.016/month**

**CronJob Compute**:
- Cleanup job: 10 seconds CPU × 30 days = 5 minutes/month (negligible)
- Backup job: 30 seconds CPU × 4 runs = 2 minutes/month (negligible)
- Cost: Uses AKS node resources = **$0**

**Total Data Lifecycle Cost**: **~$0.02/month**

---

## Cost Analysis

### Infrastructure Costs

| Component | Resource | Cost/Month | Notes |
|-----------|----------|------------|-------|
| **Compute** | AKS Nodes (existing) | $0 | Shared with n8n |
| **Storage** | Azure Disk Premium LRS (10GB) | $2.00 | PostgreSQL data |
| **Storage** | Blob Storage (0.8GB backups) | $0.02 | Weekly pg_dump |
| **Network** | Application Gateway (existing) | $0 | Shared with n8n |
| **Security** | Key Vault operations (~500/month) | $0.05 | Secret reads |
| **DNS** | Azure DNS queries (~1,000/month) | $0.01 | A record lookups |
| **Registry** | Container Registry (existing) | $0 | Shared Basic tier |
| **Total** | | **$2.08/month** | **80% under budget** |

### Cost Optimization Opportunities

**If Budget Exceeded**:
1. Downgrade to Standard SSD (10GB): $1.50/month → saves $0.50
2. Reduce backup retention to 2 weeks: $0.01/month → saves $0.01
3. Reduce PostgreSQL disk to 5GB: $1.00/month → saves $1.00

**Headroom for Growth**:
- Current: $2.08/month
- Budget: $10/month
- Headroom: $7.92/month (380% room)

**Scaling Considerations**:
- 10x traffic (10-20 users): +$0 (same resources)
- 100GB storage (10 years): +$18/month (still under budget for 1 year)
- Managed PostgreSQL: +$28/month (exceeds budget)

### Non-Infrastructure Costs

**Developer Time** (one-time):
- Manifest creation: 2 hours
- Testing/validation: 1 hour
- Documentation: 1 hour
- **Total**: 4 hours

**Maintenance** (ongoing):
- Monitor CronJobs: 15 min/month
- Review backup logs: 15 min/month
- Security updates: 30 min/quarter
- **Total**: ~30 min/month

---

## Risk Assessment

### High-Risk Items

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| PostgreSQL pod restart loses data | High | Low | Persistent volume with Retain policy |
| Key Vault access denied | High | Low | Federated credential + IAM policy testing |
| 90-day cleanup deletes wrong data | High | Low | WHERE clause review + backup before cleanup |
| Backup restoration fails | Medium | Medium | Test restore procedure in dev environment |

### Medium-Risk Items

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Disk runs out of space | Medium | Low | Monitor disk usage, 2x headroom (10GB for 5GB data) |
| Connection pool exhaustion | Medium | Low | Pool size 15 (10x expected concurrent requests) |
| HTTPS cert expires | Medium | Low | Auto-renewal enabled in Key Vault |
| Ingress routing misconfigured | Low | Medium | Test HTTP→HTTPS redirect and path routing |

### Low-Risk Items

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Slow query performance | Low | Low | Indexes on created_at, id columns |
| CronJob fails silently | Low | Medium | Monitor job logs, failedJobsHistoryLimit=5 |
| Container image pull fails | Medium | Low | Use stable tags (not :latest), private registry |

---

## Performance Benchmarks

### Expected Latencies (1-2 Users)

| Operation | Target | Acceptable | Unacceptable |
|-----------|--------|------------|--------------|
| Session list page load | <500ms | <1s | >2s |
| Upload 5 files (5MB) | <10s | <30s | >60s |
| Query session by ID | <50ms | <100ms | >500ms |
| Delete expired sessions (100 rows) | <100ms | <500ms | >5s |
| PostgreSQL connection checkout | <5ms | <10ms | >100ms |

### Resource Utilization Targets

| Resource | Idle | Normal Load | Peak Load | Limit |
|----------|------|-------------|-----------|-------|
| PostgreSQL CPU | <10% | 20-30% | 50-60% | 500m (50%) |
| PostgreSQL RAM | 200MB | 400MB | 700MB | 1Gi |
| FastAPI CPU | <5% | 10-15% | 30-40% | 500m |
| FastAPI RAM | 50MB | 100MB | 200MB | 512Mi |
| Next.js CPU | <5% | 10-15% | 20-30% | 500m |
| Next.js RAM | 100MB | 150MB | 250MB | 512Mi |

### Scaling Thresholds

**Vertical Scaling** (increase resources):
- PostgreSQL CPU >70% sustained → increase to 1 core
- PostgreSQL RAM >800MB sustained → increase to 2Gi
- API/Frontend CPU >60% sustained → increase to 1 core

**Horizontal Scaling** (add replicas):
- Not required for 1-2 users
- Consider if traffic exceeds 10 concurrent users
- PostgreSQL remains single replica (StatefulSet)

---

## Security Considerations

### Secret Management

**Best Practices**:
1. No secrets in Git (use Key Vault + CSI driver)
2. Secrets mounted as files, not environment variables
3. Read-only volume mounts for secrets
4. Service account with workload identity (no pod identity)
5. Rotate secrets every 90 days (manual process)

**Secret Inventory**:
- `postgres-password`: PostgreSQL root password (256-bit random)
- `nextauth-secret`: Next.js authentication secret (256-bit random)
- `azure-storage-sas`: Blob Storage write-only SAS token (1-year expiry)

### Network Security

**Current Setup**:
- Application Gateway: Public (HTTPS only)
- Kubernetes services: ClusterIP (internal only)
- PostgreSQL: ClusterIP on port 5432 (no external access)

**Enhancements** (future):
- NetworkPolicy: Restrict pod-to-pod traffic
- Azure Private Link: Private endpoint for Key Vault (overkill for staging)
- Web Application Firewall: Enable on Application Gateway (free tier available)

### RBAC Configuration

**Service Account Permissions**:
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: expense-reconciliation-sa
  annotations:
    azure.workload.identity/client-id: "<CLIENT_ID>"
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: expense-reconciliation-role
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]  # Read secrets mounted by CSI driver
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: expense-reconciliation-rolebinding
subjects:
- kind: ServiceAccount
  name: expense-reconciliation-sa
roleRef:
  kind: Role
  name: expense-reconciliation-role
  apiGroup: rbac.authorization.k8s.io
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] Key Vault contains all required secrets (postgres-password, nextauth-secret, azure-storage-sas)
- [ ] Workload identity federation configured (service account → managed identity)
- [ ] Container images pushed to registry (frontend:latest, api:latest)
- [ ] DNS A record points to Application Gateway public IP
- [ ] TLS certificate valid and synced to Application Gateway

### Deployment Steps

1. [ ] Apply storage class manifest (`kubectl apply -f storageclass.yaml`)
2. [ ] Deploy SecretProviderClass (`kubectl apply -f secretproviderclass.yaml`)
3. [ ] Deploy PostgreSQL StatefulSet (`kubectl apply -f postgres-statefulset.yaml`)
4. [ ] Wait for PostgreSQL ready (`kubectl wait --for=condition=ready pod/postgres-0 --timeout=300s`)
5. [ ] Run schema migration job (`kubectl apply -f migration-job.yaml`)
6. [ ] Deploy FastAPI service (`kubectl apply -f api-deployment.yaml`)
7. [ ] Deploy Next.js service (`kubectl apply -f frontend-deployment.yaml`)
8. [ ] Apply Ingress manifest (`kubectl apply -f ingress.yaml`)
9. [ ] Deploy cleanup CronJob (`kubectl apply -f cleanup-cronjob.yaml`)
10. [ ] Deploy backup CronJob (`kubectl apply -f backup-cronjob.yaml`)

### Post-Deployment Validation

- [ ] PostgreSQL accepting connections (`kubectl exec -it postgres-0 -- psql -U postgres -c '\l'`)
- [ ] API health check responds 200 (`curl https://expenses.insulations.com/api/health`)
- [ ] Frontend loads successfully (`curl -I https://expenses.insulations.com`)
- [ ] HTTP→HTTPS redirect works (`curl -I http://expenses.insulations.com`)
- [ ] Secrets mounted correctly (`kubectl exec -it api-<pod> -- ls /mnt/secrets`)
- [ ] Upload workflow completes successfully (manual test)
- [ ] CronJob schedules visible (`kubectl get cronjobs`)
- [ ] Backup storage container accessible (`az storage blob list --container-name backups`)

---

## References

### Azure Documentation
- [AKS Workload Identity](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview)
- [Secrets Store CSI Driver](https://learn.microsoft.com/en-us/azure/aks/csi-secrets-store-driver)
- [Application Gateway Ingress Controller](https://learn.microsoft.com/en-us/azure/application-gateway/ingress-controller-overview)
- [Azure Disk CSI Driver](https://learn.microsoft.com/en-us/azure/aks/azure-disk-csi)
- [Blob Storage Lifecycle Management](https://learn.microsoft.com/en-us/azure/storage/blobs/lifecycle-management-overview)

### Kubernetes Documentation
- [StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/)
- [CronJobs](https://kubernetes.io/docs/concepts/workloads/controllers/cron-jobs/)
- [Persistent Volumes](https://kubernetes.io/docs/concepts/storage/persistent-volumes/)

### Framework Documentation
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI Async](https://fastapi.tiangolo.com/async/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Next.js Server Components](https://nextjs.org/docs/app/building-your-application/rendering/server-components)

---

**Document Status**: Complete
**Last Updated**: 2025-10-06
**Author**: System Architect
**Review Status**: Ready for implementation planning
