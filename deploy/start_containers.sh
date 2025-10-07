#!/bin/bash

# Script to start Docker containers for local testing
# Run from the deploy/ directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "Step 1: Stopping any existing containers"
echo "========================================="
docker-compose down -v
echo ""

echo "========================================="
echo "Step 2: Building and starting containers"
echo "========================================="
docker-compose up --build -d
echo ""

echo "========================================="
echo "Step 3: Waiting for services to be healthy (30 seconds)"
echo "========================================="
sleep 30
echo ""

echo "========================================="
echo "Step 4: Checking container status"
echo "========================================="
docker-compose ps
echo ""

echo "========================================="
echo "Step 5: Checking logs for errors"
echo "========================================="
docker-compose logs --tail=50
echo ""

echo "========================================="
echo "Summary Complete"
echo "========================================="
