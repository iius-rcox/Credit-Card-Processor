#!/bin/bash
#
# Deployment script for Credit Card Reconciliation System
# Deploys to Azure Kubernetes Service (AKS)
#

set -e  # Exit on error

# Get script directory and set paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="$SCRIPT_DIR"

# Color output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ACR_NAME="iiusacr"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"
BACKEND_IMAGE="${ACR_LOGIN_SERVER}/expense-backend"
FRONTEND_IMAGE="${ACR_LOGIN_SERVER}/expense-frontend"
VERSION="${1:-latest}"
NAMESPACE="credit-card-processor"
K8S_DIR="specs/005-lean-internal-deployment/contracts/k8s"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Credit Card Reconciliation - Deployment Script      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Check prerequisites
echo -e "${BLUE}[1/10]${NC} Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗${NC} Docker is not installed"
    exit 1
fi

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}✗${NC} kubectl is not installed"
    exit 1
fi

if ! command -v az &> /dev/null; then
    echo -e "${RED}✗${NC} Azure CLI is not installed"
    exit 1
fi

echo -e "${GREEN}✓${NC} All prerequisites met"

# Step 2: Azure authentication
echo -e "${BLUE}[2/10]${NC} Checking Azure authentication..."

if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠${NC}  Not logged in to Azure. Running 'az login'..."
    az login
else
    echo -e "${GREEN}✓${NC} Already logged in to Azure"
fi

# Step 3: ACR authentication
echo -e "${BLUE}[3/10]${NC} Authenticating with Azure Container Registry..."

az acr login --name ${ACR_NAME}
echo -e "${GREEN}✓${NC} ACR authentication successful"

# Step 4: Build backend Docker image
echo -e "${BLUE}[4/10]${NC} Building backend Docker image..."

docker build -t ${BACKEND_IMAGE}:${VERSION} -t ${BACKEND_IMAGE}:latest -f "${PROJECT_ROOT}/backend/Dockerfile" "${PROJECT_ROOT}/backend"

echo -e "${GREEN}✓${NC} Backend image built: ${BACKEND_IMAGE}:${VERSION}"

# Step 5: Build frontend Docker image
echo -e "${BLUE}[5/10]${NC} Building frontend Docker image..."

docker build -f "${DEPLOY_DIR}/Dockerfile" -t ${FRONTEND_IMAGE}:${VERSION} -t ${FRONTEND_IMAGE}:latest "${PROJECT_ROOT}"

echo -e "${GREEN}✓${NC} Frontend image built: ${FRONTEND_IMAGE}:${VERSION}"

# Step 6: Push images to ACR
echo -e "${BLUE}[6/10]${NC} Pushing images to Azure Container Registry..."

docker push ${BACKEND_IMAGE}:${VERSION}
docker push ${BACKEND_IMAGE}:latest
docker push ${FRONTEND_IMAGE}:${VERSION}
docker push ${FRONTEND_IMAGE}:latest

echo -e "${GREEN}✓${NC} Images pushed to ACR"

# Step 7: Get AKS credentials
echo -e "${BLUE}[7/10]${NC} Getting AKS credentials..."

az aks get-credentials --resource-group rg_prod --name dev-aks --overwrite-existing

echo -e "${GREEN}✓${NC} AKS credentials configured"

# Step 8: Create namespace if not exists
echo -e "${BLUE}[8/10]${NC} Creating namespace..."

kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✓${NC} Namespace ready: ${NAMESPACE}"

# Step 9: Apply Kubernetes manifests
echo -e "${BLUE}[9/10]${NC} Applying Kubernetes manifests..."

# Secret Provider Class (Azure Key Vault)
kubectl apply -f ${K8S_DIR}/secret-provider.yaml

# PostgreSQL
kubectl apply -f ${K8S_DIR}/postgres-statefulset.yaml
kubectl apply -f ${K8S_DIR}/postgres-service.yaml

# Wait for PostgreSQL to be ready
echo -e "${YELLOW}⏳${NC} Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n ${NAMESPACE} --timeout=300s || true

# Backend
kubectl apply -f ${K8S_DIR}/backend-deployment.yaml
kubectl apply -f ${K8S_DIR}/backend-service.yaml

# Frontend
kubectl apply -f ${K8S_DIR}/frontend-deployment.yaml
kubectl apply -f ${K8S_DIR}/frontend-service.yaml

# Ingress
kubectl apply -f ${K8S_DIR}/ingress.yaml

# CronJobs
kubectl apply -f ${K8S_DIR}/cleanup-cronjob.yaml
kubectl apply -f ${K8S_DIR}/backup-cronjob.yaml

echo -e "${GREEN}✓${NC} All manifests applied"

# Step 10: Verify deployment
echo -e "${BLUE}[10/10]${NC} Verifying deployment..."

echo ""
echo -e "${BLUE}Pods:${NC}"
kubectl get pods -n ${NAMESPACE}

echo ""
echo -e "${BLUE}Services:${NC}"
kubectl get services -n ${NAMESPACE}

echo ""
echo -e "${BLUE}Ingress:${NC}"
kubectl get ingress -n ${NAMESPACE}

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Deployment Complete!                           ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Application URL:${NC} https://credit-card.ii-us.com"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Check pod status: kubectl get pods -n ${NAMESPACE}"
echo "  2. View backend logs: kubectl logs -n ${NAMESPACE} -l app=backend --tail=50"
echo "  3. View frontend logs: kubectl logs -n ${NAMESPACE} -l app=frontend --tail=50"
echo "  4. Test health endpoint: curl -k https://credit-card.ii-us.com/api/health"
echo ""
