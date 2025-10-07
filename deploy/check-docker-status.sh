#!/bin/bash

echo "================================"
echo "Docker Container Status Check"
echo "================================"
echo ""

echo "1. Checking container status..."
echo "-------------------------------"
docker-compose ps
echo ""

echo "2. Backend logs (last 20 lines)..."
echo "-----------------------------------"
docker-compose logs backend --tail=20
echo ""

echo "3. Frontend logs (last 20 lines)..."
echo "------------------------------------"
docker-compose logs frontend --tail=20
echo ""

echo "4. Postgres logs (last 10 lines)..."
echo "------------------------------------"
docker-compose logs postgres --tail=10
echo ""

echo "5. Redis logs (last 10 lines)..."
echo "----------------------------------"
docker-compose logs redis --tail=10
echo ""

echo "6. Testing backend health endpoint..."
echo "--------------------------------------"
curl -s http://localhost:8000/health || echo "Backend health check failed"
echo ""

echo "7. Testing backend root endpoint..."
echo "------------------------------------"
curl -s http://localhost:8000/ || echo "Backend root endpoint failed"
echo ""

echo "8. Testing frontend..."
echo "----------------------"
curl -s -I http://localhost:3000 | head -5 || echo "Frontend check failed"
echo ""

echo "9. Checking port availability..."
echo "---------------------------------"
echo "Port 3000 (frontend):"
lsof -i :3000 || echo "Port 3000 not in use"
echo ""
echo "Port 8000 (backend):"
lsof -i :8000 || echo "Port 8000 not in use"
echo ""
echo "Port 5432 (postgres):"
lsof -i :5432 || echo "Port 5432 not in use"
echo ""
echo "Port 6379 (redis):"
lsof -i :6379 || echo "Port 6379 not in use"
echo ""

echo "================================"
echo "Diagnostic Complete"
echo "================================"
