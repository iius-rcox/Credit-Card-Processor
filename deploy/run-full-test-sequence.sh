#!/bin/bash

# Credit Card Reconciliation System - Full Testing Sequence
# Working directory: /Users/rogercox/Credit-Card-Processor

set -e

echo "=========================================="
echo "Credit Card Reconciliation System"
echo "Local Testing Sequence"
echo "=========================================="
echo ""

# Step 1: Stop and clean existing containers
echo "STEP 1: Stop and clean existing containers"
echo "--------------------------------------------"
echo "Running: docker-compose down -v"
docker-compose down -v
echo "✓ Containers stopped and cleaned"
echo ""

# Step 2: Build and start all containers
echo "STEP 2: Build and start all containers"
echo "----------------------------------------"
echo "Running: docker-compose up --build -d"
docker-compose up --build -d
echo "✓ Containers built and started"
echo ""

# Step 3: Wait for services to initialize
echo "STEP 3: Wait for services to initialize"
echo "-----------------------------------------"
echo "Waiting 30 seconds for services to start..."
for i in {30..1}; do
  echo -ne "Time remaining: $i seconds\r"
  sleep 1
done
echo ""
echo "✓ Wait period complete"
echo ""

# Step 4: Check container status
echo "STEP 4: Check container status"
echo "--------------------------------"
echo "Running: docker-compose ps"
echo ""
docker-compose ps
echo ""

# Step 5: Run health checks
echo "STEP 5: Run health checks"
echo "--------------------------"
echo ""
echo "Backend Health Check (http://localhost:8000/health):"
echo "------------------------------------------------------"
BACKEND_HEALTH=$(curl -s -w "\nHTTP_CODE:%{http_code}\n" http://localhost:8000/health || echo "ERROR: Backend health check failed")
echo "$BACKEND_HEALTH"
echo ""

echo "Frontend Status Check (http://localhost:3000):"
echo "------------------------------------------------"
FRONTEND_STATUS=$(curl -sI http://localhost:3000 | head -10 || echo "ERROR: Frontend check failed")
echo "$FRONTEND_STATUS"
echo ""

# Step 6: Make diagnostic script executable and run it
echo "STEP 6: Run diagnostic script"
echo "-------------------------------"
echo "Running: chmod +x check-docker-status.sh && ./check-docker-status.sh"
echo ""
chmod +x check-docker-status.sh
./check-docker-status.sh

# Generate summary report
echo ""
echo "=========================================="
echo "SUMMARY REPORT"
echo "=========================================="
echo ""

# Check container statuses
echo "Container Status Summary:"
echo "-------------------------"
POSTGRES_STATUS=$(docker inspect -f '{{.State.Status}}' credit-card-postgres 2>/dev/null || echo "not running")
REDIS_STATUS=$(docker inspect -f '{{.State.Status}}' credit-card-redis 2>/dev/null || echo "not running")
BACKEND_STATUS=$(docker inspect -f '{{.State.Status}}' credit-card-backend 2>/dev/null || echo "not running")
FRONTEND_STATUS=$(docker inspect -f '{{.State.Status}}' credit-card-frontend 2>/dev/null || echo "not running")

echo "  1. postgres (credit-card-postgres):  $POSTGRES_STATUS"
echo "  2. redis (credit-card-redis):        $REDIS_STATUS"
echo "  3. backend (credit-card-backend):    $BACKEND_STATUS"
echo "  4. frontend (credit-card-frontend):  $FRONTEND_STATUS"
echo ""

# Check health statuses
echo "Container Health Summary:"
echo "-------------------------"
POSTGRES_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' credit-card-postgres 2>/dev/null || echo "no healthcheck")
REDIS_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' credit-card-redis 2>/dev/null || echo "no healthcheck")
BACKEND_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' credit-card-backend 2>/dev/null || echo "no healthcheck")
FRONTEND_HEALTH=$(docker inspect -f '{{.State.Health.Status}}' credit-card-frontend 2>/dev/null || echo "no healthcheck")

echo "  1. postgres:  $POSTGRES_HEALTH"
echo "  2. redis:     $REDIS_HEALTH"
echo "  3. backend:   $BACKEND_HEALTH"
echo "  4. frontend:  $FRONTEND_HEALTH"
echo ""

# Determine overall readiness
echo "Service Readiness:"
echo "------------------"
ALL_RUNNING=true
if [ "$POSTGRES_STATUS" != "running" ] || [ "$REDIS_STATUS" != "running" ] || [ "$BACKEND_STATUS" != "running" ] || [ "$FRONTEND_STATUS" != "running" ]; then
  ALL_RUNNING=false
fi

HEALTH_OK=true
if [ "$POSTGRES_HEALTH" != "healthy" ] && [ "$POSTGRES_HEALTH" != "no healthcheck" ]; then
  HEALTH_OK=false
fi
if [ "$REDIS_HEALTH" != "healthy" ] && [ "$REDIS_HEALTH" != "no healthcheck" ]; then
  HEALTH_OK=false
fi

if [ "$ALL_RUNNING" = true ] && [ "$HEALTH_OK" = true ]; then
  echo "✓ All services are running"
  echo "✓ Health checks passed"
  echo "✓ READY FOR CHROME DEVTOOLS TESTING"
  echo ""
  echo "Access URLs:"
  echo "  Frontend: http://localhost:3000"
  echo "  Backend:  http://localhost:8000"
  echo "  Backend Health: http://localhost:8000/health"
  echo "  Backend Docs: http://localhost:8000/docs"
else
  echo "✗ NOT READY - Some services are not running properly"
  echo ""
  echo "Check the logs above for errors"
  echo ""
  echo "Useful commands:"
  echo "  docker-compose logs backend"
  echo "  docker-compose logs frontend"
  echo "  docker-compose logs postgres"
  echo "  docker-compose logs redis"
fi

echo ""
echo "=========================================="
echo "Testing Sequence Complete"
echo "=========================================="
