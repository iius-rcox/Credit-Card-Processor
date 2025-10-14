#!/bin/bash
# E2E Test Monitoring Script
# Monitors both backend and celery-worker pods for upload and processing activity

echo "================================================"
echo "E2E Test Monitor - Kubernetes Shared Storage"
echo "================================================"
echo ""
echo "Monitoring namespace: credit-card-processor"
echo "Press Ctrl+C to stop"
echo ""

# Check pod status
echo "Pod Status:"
kubectl get pods -n credit-card-processor -o wide
echo ""

# Check PVC status
echo "PVC Status:"
kubectl get pvc credit-card-temp-pvc -n credit-card-processor
echo ""

# Check shared storage contents
echo "Shared Storage Contents:"
kubectl exec deployment/backend -n credit-card-processor -- sh -c "ls -lh /app/shared-temp/ 2>/dev/null || echo 'Empty'"
echo ""

echo "================================================"
echo "Starting log monitoring..."
echo "================================================"
echo ""

# Monitor logs in parallel
kubectl logs -f deployment/backend -n credit-card-processor --tail=20 | grep --line-buffered -E "\[UPLOAD\]|\[STORAGE\]|session|error|ERROR" &
BACKEND_PID=$!

kubectl logs -f deployment/celery-worker -n credit-card-processor --tail=20 | grep --line-buffered -E "session|PDF|extraction|transaction|Cleaned|error|ERROR" &
CELERY_PID=$!

# Trap Ctrl+C
trap "kill $BACKEND_PID $CELERY_PID 2>/dev/null; echo ''; echo 'Monitoring stopped'; exit 0" INT

# Wait
wait
