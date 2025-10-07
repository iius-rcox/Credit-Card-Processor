# Deployment Scripts

This directory contains all deployment and Docker-related files for the Credit Card Processor application.

## Files

### Docker Configuration
- **Dockerfile** - Frontend Next.js application Docker image
- **docker-compose.yml** - Local development multi-container setup
- **.dockerignore** - Files to exclude from Docker builds

### Deployment Scripts

#### Local Development
- **start_containers.sh** - Start Docker containers for local testing
  ```bash
  cd deploy
  ./start_containers.sh
  ```

- **check-docker-status.sh** - Check status of running containers
  ```bash
  cd deploy
  ./check-docker-status.sh
  ```

- **run-full-test-sequence.sh** - Full test sequence with health checks
  ```bash
  cd deploy
  ./run-full-test-sequence.sh
  ```

#### Azure Deployment
- **deploy.sh** - Full deployment to Azure Kubernetes Service (AKS)
  ```bash
  cd deploy
  ./deploy.sh [version]
  ```

- **deploy-all.ps1** - PowerShell script for full AKS deployment
  ```powershell
  cd deploy
  ./deploy-all.ps1 -FrontendTag "v1.0.1" -BackendTag "v1.0.1"
  ```

- **deploy-frontend.ps1** - PowerShell script for frontend-only deployment
  ```powershell
  cd deploy
  ./deploy-frontend.ps1 -ImageTag "v1.0.1"
  ```

## Usage Notes

### Running Scripts from Any Directory
All deployment scripts can now be run from **any directory** - they automatically detect their location and use correct absolute paths:
- Backend source: `<project-root>/backend`
- Frontend/project root: `<project-root>`
- Docker Compose: `<project-root>/deploy/docker-compose.yml`
- Frontend Dockerfile: `<project-root>/deploy/Dockerfile`

**Examples:**

Run from project root:
```powershell
./deploy/deploy-all.ps1 -FrontendTag "v1.0.1"
./deploy/deploy.sh v1.0.1
```

Or from deploy directory:
```powershell
cd deploy
./deploy-all.ps1 -FrontendTag "v1.0.1"
./deploy.sh v1.0.1
```

Both work the same way!

### Docker Compose Services
The docker-compose.yml defines:
- **postgres** - PostgreSQL 16 database
- **redis** - Redis cache
- **backend** - FastAPI Python backend
- **frontend** - Next.js React frontend

### Prerequisites
- Docker and Docker Compose
- Azure CLI (for AKS deployment)
- kubectl (for Kubernetes)
- Node.js 20+ (for local development)

## Path Changes
**Note**: These scripts were updated after reorganizing the project structure. Docker and deployment files moved from root to `deploy/` directory.
