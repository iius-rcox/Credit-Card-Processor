#!/bin/bash
#
# Full deployment script for Credit Card Processor to AKS
# Builds and pushes both frontend and backend Docker images to ACR,
# then redeploys all components to AKS with cleanup
#

set -e  # Exit on error

# Default parameters
FRONTEND_TAG="${1:-v1.0.1}"
BACKEND_TAG="${2:-v1.0.1}"
ACR_NAME="${3:-iiusacr}"
NAMESPACE="${4:-credit-card-processor}"
AKS_CLUSTER="${5:-dev-aks}"
RESOURCE_GROUP="${6:-rg_prod}"

# Get script directory and set paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_DIR="$SCRIPT_DIR"

# Color output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Full AKS Deployment Script${NC}"
echo -e "${CYAN}  (with Database Migrations)${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "${YELLOW}Frontend Tag: ${FRONTEND_TAG}${NC}"
echo -e "${YELLOW}Backend Tag:  ${BACKEND_TAG}${NC}"
echo -e "${YELLOW}ACR:          ${ACR_NAME}${NC}"
echo -e "${YELLOW}Namespace:    ${NAMESPACE}${NC}"
echo -e "${YELLOW}AKS Cluster:  ${AKS_CLUSTER}${NC}"
echo ""

# Step 1: Ensure AKS credentials
echo -e "${GREEN}[1/11] Getting AKS credentials...${NC}"
az aks get-credentials --resource-group "$RESOURCE_GROUP" --name "$AKS_CLUSTER" --overwrite-existing
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to get AKS credentials${NC}"
    exit 1
fi

# Fix for private AKS cluster - use IP instead of DNS
echo -e "${CYAN}Fixing kubeconfig for private cluster DNS...${NC}"
CLUSTER_IP=$(nslookup $(kubectl config view -o jsonpath='{.clusters[?(@.name=="'$AKS_CLUSTER'")].cluster.server}' | sed 's|https://||' | sed 's|:443||') 2>/dev/null | grep -A1 "Name:" | tail -1 | awk '{print $2}')
if [ -n "$CLUSTER_IP" ]; then
    kubectl config set-cluster "$AKS_CLUSTER" --server="https://$CLUSTER_IP:443"
    echo -e "${GREEN}Using cluster IP: $CLUSTER_IP${NC}"
else
    echo -e "${YELLOW}Warning: Could not resolve cluster IP, using DNS name${NC}"
fi

# Step 2: Login to ACR
echo -e "${GREEN}[2/11] Logging into Azure Container Registry...${NC}"
az acr login --name "$ACR_NAME"
if [ $? -ne 0 ]; then
    echo -e "${RED}ACR login failed${NC}"
    exit 1
fi

# Step 3: Build frontend image
echo -e "${GREEN}[3/11] Building frontend Docker image...${NC}"
DOCKERFILE_PATH="${DEPLOY_DIR}/Dockerfile"
docker build -f "$DOCKERFILE_PATH" -t "${ACR_NAME}.azurecr.io/expense-frontend:${FRONTEND_TAG}" "$PROJECT_ROOT"
if [ $? -ne 0 ]; then
    echo -e "${RED}Frontend Docker build failed${NC}"
    exit 1
fi

# Step 4: Push frontend image
echo -e "${GREEN}[4/11] Pushing frontend image to ACR...${NC}"
docker push "${ACR_NAME}.azurecr.io/expense-frontend:${FRONTEND_TAG}"
if [ $? -ne 0 ]; then
    echo -e "${RED}Frontend Docker push failed${NC}"
    exit 1
fi

# Step 5: Build backend image
echo -e "${GREEN}[5/11] Building backend Docker image...${NC}"
BACKEND_DIR="${PROJECT_ROOT}/backend"
BACKEND_DOCKERFILE="${BACKEND_DIR}/Dockerfile"
docker build -t "${ACR_NAME}.azurecr.io/expense-backend:${BACKEND_TAG}" -f "$BACKEND_DOCKERFILE" "$BACKEND_DIR"
if [ $? -ne 0 ]; then
    echo -e "${RED}Backend Docker build failed${NC}"
    exit 1
fi

# Step 6: Push backend image
echo -e "${GREEN}[6/11] Pushing backend image to ACR...${NC}"
docker push "${ACR_NAME}.azurecr.io/expense-backend:${BACKEND_TAG}"
if [ $? -ne 0 ]; then
    echo -e "${RED}Backend Docker push failed${NC}"
    exit 1
fi

# Step 7: Delete existing backend pods
echo -e "${GREEN}[7/11] Deleting existing backend pods...${NC}"
kubectl delete pods -l app=backend -n "$NAMESPACE" 2>/dev/null || echo -e "${YELLOW}Warning: Failed to delete backend pods (may not exist yet)${NC}"

# Step 8: Run database migrations
echo -e "${GREEN}[8/11] Running database migrations...${NC}"
"${DEPLOY_DIR}/run-migrations.sh" "$NAMESPACE" "$BACKEND_TAG" "$ACR_NAME"
if [ $? -ne 0 ]; then
    echo -e "${RED}Database migration failed${NC}"
    exit 1
fi

# Step 9: Update backend deployment
echo -e "${GREEN}[9/11] Updating backend deployment...${NC}"
kubectl set image deployment/backend "backend=${ACR_NAME}.azurecr.io/expense-backend:${BACKEND_TAG}" -n "$NAMESPACE"
if [ $? -ne 0 ]; then
    echo -e "${RED}Backend deployment update failed${NC}"
    exit 1
fi

# Step 10: Wait for backend rollout
echo -e "${GREEN}[10/11] Waiting for backend rollout...${NC}"
kubectl rollout status deployment/backend -n "$NAMESPACE" --timeout=5m
if [ $? -ne 0 ]; then
    echo -e "${RED}Backend rollout failed or timed out${NC}"
    exit 1
fi

# Step 11: Delete existing frontend pods
echo -e "${GREEN}[11/11] Deleting existing frontend pods...${NC}"
kubectl delete pods -l app=frontend -n "$NAMESPACE" 2>/dev/null || echo -e "${YELLOW}Warning: Failed to delete frontend pods (may not exist yet)${NC}"

# Step 12: Update frontend deployment
echo -e "${GREEN}[12/11] Updating frontend deployment...${NC}"
kubectl set image deployment/frontend "frontend=${ACR_NAME}.azurecr.io/expense-frontend:${FRONTEND_TAG}" -n "$NAMESPACE"
if [ $? -ne 0 ]; then
    echo -e "${RED}Frontend deployment update failed${NC}"
    exit 1
fi

# Wait for frontend rollout
echo ""
echo -e "${CYAN}Waiting for frontend rollout...${NC}"
kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=5m

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Deployment Successful!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Frontend: ${ACR_NAME}.azurecr.io/expense-frontend:${FRONTEND_TAG}${NC}"
    echo -e "${GREEN}Backend:  ${ACR_NAME}.azurecr.io/expense-backend:${BACKEND_TAG}${NC}"

    # Show deployment status
    echo ""
    echo -e "${CYAN}Current deployments:${NC}"
    kubectl get deployments -n "$NAMESPACE"

    echo ""
    echo -e "${CYAN}Current pods:${NC}"
    kubectl get pods -n "$NAMESPACE"

    echo ""
    echo -e "${CYAN}Services:${NC}"
    kubectl get services -n "$NAMESPACE"

    echo ""
    echo -e "${GREEN}Application URL: https://credit-card.ii-us.com${NC}"
else
    echo -e "${RED}Frontend deployment rollout failed or timed out${NC}"
    exit 1
fi
