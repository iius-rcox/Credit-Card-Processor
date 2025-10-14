#!/bin/bash
#
# Run database migrations in Kubernetes
# This script should be run before deploying new backend versions
#

set -e  # Exit on error

# Default parameters
NAMESPACE="${1:-credit-card-processor}"
BACKEND_TAG="${2:-v1.0.13}"
ACR_NAME="${3:-iiusacr}"

# Color output
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Running Database Migrations${NC}"
echo -e "${CYAN}========================================${NC}"
echo -e "${YELLOW}Namespace:    ${NAMESPACE}${NC}"
echo -e "${YELLOW}Backend Tag:  ${BACKEND_TAG}${NC}"
echo -e "${YELLOW}ACR:          ${ACR_NAME}${NC}"
echo ""

# Step 1: Update migration job manifest with new image tag
echo -e "${GREEN}[1/4] Updating migration job image...${NC}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MIGRATION_JOB="${SCRIPT_DIR}/k8s/migration-job.yaml"

# Create a temporary copy with updated image
TEMP_JOB=$(mktemp)
sed "s|image: ${ACR_NAME}.azurecr.io/expense-backend:.*|image: ${ACR_NAME}.azurecr.io/expense-backend:${BACKEND_TAG}|" "$MIGRATION_JOB" > "$TEMP_JOB"

# Step 2: Delete existing migration job if it exists
echo -e "${GREEN}[2/4] Cleaning up previous migration job...${NC}"
kubectl delete job backend-migration -n "$NAMESPACE" 2>/dev/null || echo -e "${YELLOW}No previous migration job found${NC}"

# Step 3: Create and run migration job
echo -e "${GREEN}[3/4] Starting migration job...${NC}"
kubectl apply -f "$TEMP_JOB"
rm -f "$TEMP_JOB"

# Step 4: Wait for migration to complete
echo -e "${GREEN}[4/4] Waiting for migration to complete...${NC}"
echo -e "${CYAN}Watching migration job logs...${NC}"
echo ""

# Wait for pod to be created
sleep 5

# Get the pod name
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l component=migration --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}' 2>/dev/null)

if [ -z "$POD_NAME" ]; then
    echo -e "${RED}Failed to find migration pod${NC}"
    exit 1
fi

echo -e "${CYAN}Migration pod: ${POD_NAME}${NC}"
echo ""

# Stream logs
kubectl logs -f "$POD_NAME" -n "$NAMESPACE" 2>/dev/null || echo -e "${YELLOW}Waiting for pod to start...${NC}"

# Wait for job completion
kubectl wait --for=condition=complete --timeout=5m job/backend-migration -n "$NAMESPACE"

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Migrations Completed Successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"

    # Show migration job status
    echo ""
    echo -e "${CYAN}Migration job status:${NC}"
    kubectl get job backend-migration -n "$NAMESPACE"

    echo ""
    echo -e "${GREEN}✓ Database schema is now up to date${NC}"
    echo -e "${GREEN}✓ Ready to deploy backend version ${BACKEND_TAG}${NC}"
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  Migration Failed!${NC}"
    echo -e "${RED}========================================${NC}"

    # Show pod logs for debugging
    echo ""
    echo -e "${YELLOW}Recent pod logs:${NC}"
    kubectl logs "$POD_NAME" -n "$NAMESPACE" --tail=50

    # Show pod status
    echo ""
    echo -e "${YELLOW}Pod status:${NC}"
    kubectl describe pod "$POD_NAME" -n "$NAMESPACE"

    exit 1
fi
