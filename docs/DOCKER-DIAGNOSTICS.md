# Docker Container Diagnostics Guide

## Quick Start

Run the automated diagnostic script:

```bash
cd /Users/rogercox/Credit-Card-Processor
chmod +x check-docker-status.sh
./check-docker-status.sh
```

## Manual Diagnostics

### 1. Check Container Status

```bash
cd /Users/rogercox/Credit-Card-Processor
docker-compose ps
```

**Expected Output:**
All containers should show "Up" status:
- `credit-card-postgres` - Up (healthy)
- `credit-card-redis` - Up (healthy)
- `credit-card-backend` - Up
- `credit-card-frontend` - Up

### 2. Check Backend Logs

```bash
docker-compose logs backend --tail=20
```

**Look for:**
- ✅ "Application startup complete"
- ✅ "Uvicorn running on http://0.0.0.0:8000"
- ❌ Database connection errors
- ❌ Import errors or missing dependencies
- ❌ Port binding errors

### 3. Check Frontend Logs

```bash
docker-compose logs frontend --tail=20
```

**Look for:**
- ✅ "Ready in [X]s"
- ✅ "Local: http://localhost:3000"
- ❌ Module not found errors
- ❌ Build errors
- ❌ Port binding errors

### 4. Check Database Logs

```bash
docker-compose logs postgres --tail=10
```

**Look for:**
- ✅ "database system is ready to accept connections"
- ❌ Initialization errors
- ❌ Authentication failures

### 5. Check Redis Logs

```bash
docker-compose logs redis --tail=10
```

**Look for:**
- ✅ "Ready to accept connections"
- ❌ Configuration errors

## API Endpoint Testing

### Backend Health Check

```bash
# Root endpoint
curl http://localhost:8000/

# Health endpoint (with database check)
curl http://localhost:8000/api/health

# API documentation
open http://localhost:8000/docs
```

**Expected Health Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2025-10-06T..."
}
```

### Frontend Check

```bash
# Check if frontend is responding
curl -I http://localhost:3000

# Open in browser
open http://localhost:3000
```

## Port Availability Check

```bash
# Check if ports are in use
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

## Common Issues & Solutions

### Issue 1: Containers Not Starting

**Symptoms:**
- `docker-compose ps` shows "Exit" status
- Containers restart repeatedly

**Solutions:**
```bash
# Check logs for specific error
docker-compose logs [service-name]

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Check disk space
df -h
```

### Issue 2: Database Connection Failed

**Symptoms:**
- Backend logs show "could not connect to server"
- Health endpoint returns 503

**Solutions:**
```bash
# Check if postgres is healthy
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres

# Wait for health check
docker-compose ps | grep healthy
```

### Issue 3: Port Already in Use

**Symptoms:**
- "port is already allocated" error
- Container fails to start

**Solutions:**
```bash
# Find process using the port
lsof -i :8000  # or :3000, :5432, :6379

# Kill the process
kill -9 <PID>

# Or stop other docker-compose instances
docker ps -a
docker stop <container-id>
```

### Issue 4: Frontend Can't Connect to Backend

**Symptoms:**
- Frontend loads but API calls fail
- Network errors in browser console

**Solutions:**
```bash
# Check backend is running
curl http://localhost:8000/

# Check CORS settings in backend
docker-compose logs backend | grep CORS

# Verify environment variable
docker-compose exec frontend env | grep NEXT_PUBLIC_API_URL
```

### Issue 5: Database Initialization Failed

**Symptoms:**
- Backend can't connect to database
- "relation does not exist" errors

**Solutions:**
```bash
# Check if init.sql exists
ls -la /Users/rogercox/Credit-Card-Processor/backend/init.sql

# Recreate database from scratch
docker-compose down -v  # WARNING: Deletes all data
docker-compose up -d postgres
docker-compose logs postgres  # Wait for "ready to accept connections"
docker-compose up -d
```

## Container Management Commands

```bash
# Start all containers
docker-compose up -d

# Stop all containers
docker-compose down

# Restart specific service
docker-compose restart backend

# View real-time logs
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend bash

# Remove containers and volumes (DESTRUCTIVE)
docker-compose down -v
```

## Health Check URLs

- **Backend Root**: http://localhost:8000/
- **Backend Health**: http://localhost:8000/api/health
- **Backend API Docs**: http://localhost:8000/docs
- **Backend ReDoc**: http://localhost:8000/redoc
- **Frontend**: http://localhost:3000/

## Service Dependencies

```
frontend → backend → postgres (healthy)
                  → redis (healthy)
```

The backend will not start until both postgres and redis pass their health checks.

## Environment Variables

### Backend
- `DATABASE_URL`: postgresql+asyncpg://ccprocessor:devpassword123@postgres:5432/credit_card_db
- `REDIS_URL`: redis://redis:6379/0
- `ENVIRONMENT`: development
- `LOG_LEVEL`: DEBUG

### Frontend
- `NEXT_PUBLIC_API_URL`: http://localhost:8000
- `NODE_ENV`: development

## Useful Docker Commands

```bash
# Check all running containers
docker ps

# Check container resource usage
docker stats

# Inspect container
docker inspect credit-card-backend

# View container networks
docker network ls
docker network inspect credit-card-network

# Clean up unused resources
docker system prune
```

## Troubleshooting Checklist

- [ ] All containers show "Up" status
- [ ] PostgreSQL health check passing
- [ ] Redis health check passing
- [ ] Backend logs show "Application startup complete"
- [ ] Frontend logs show "Ready"
- [ ] `curl http://localhost:8000/` returns JSON
- [ ] `curl http://localhost:8000/api/health` returns "healthy"
- [ ] `curl -I http://localhost:3000` returns 200 OK
- [ ] No port conflicts (3000, 8000, 5432, 6379)
- [ ] Adequate disk space available
- [ ] Docker daemon is running

## Getting Help

If issues persist:
1. Collect all logs: `docker-compose logs > docker-logs.txt`
2. Check container status: `docker-compose ps > container-status.txt`
3. Check system resources: `docker stats --no-stream > docker-stats.txt`
4. Review error messages in logs
5. Check for known issues in project documentation
