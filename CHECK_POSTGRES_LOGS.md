# PostgreSQL Startup Failure - Diagnostics

**Error**: `dependency failed to start: container credit-card-postgres exited (3)`
**Status**: PostgreSQL failed to start

---

## 🔍 Check PostgreSQL Logs

Run this command to see why PostgreSQL failed:

```bash
docker-compose logs postgres
```

This will show the PostgreSQL startup logs and error messages.

---

## 🐛 Common PostgreSQL Issues

### Issue 1: Init Script Error

**Symptom**: PostgreSQL exits with code 3
**Cause**: Error in `/docker-entrypoint-initdb.d/init.sql`
**Fix**: Check init.sql syntax

**Check**:
```bash
cat backend/init.sql | head -50
```

### Issue 2: Permission Issues

**Symptom**: Cannot write to data directory
**Cause**: Volume permissions
**Fix**: Remove volume and recreate

**Fix Commands**:
```bash
docker-compose down -v  # -v removes volumes
docker-compose up -d
```

### Issue 3: Port Already in Use

**Symptom**: Port 5432 already bound
**Cause**: Another PostgreSQL instance running
**Fix**: Stop other PostgreSQL or change port

**Check**:
```bash
lsof -i :5432
```

**Fix**:
```bash
# Kill process using port
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "5433:5432"  # Use 5433 instead
```

### Issue 4: Invalid Environment Variables

**Symptom**: Missing required env vars
**Cause**: POSTGRES_USER, POSTGRES_PASSWORD, or POSTGRES_DB not set
**Fix**: Verify docker-compose.yml

**Check**:
```bash
grep -A 5 "postgres:" docker-compose.yml
```

---

## 🚀 Quick Fix - Try This First

```bash
# Stop everything
docker-compose down -v

# Remove any orphaned containers
docker ps -a | grep postgres | awk '{print $1}' | xargs docker rm -f

# Check if port is free
lsof -i :5432

# Start fresh
docker-compose up -d postgres

# Watch logs in real-time
docker-compose logs -f postgres
```

---

## 📋 Manual PostgreSQL Start (Debugging)

If you need to debug further:

```bash
# Start just PostgreSQL
docker run --rm -it \
  -e POSTGRES_USER=ccprocessor \
  -e POSTGRES_PASSWORD=devpassword123 \
  -e POSTGRES_DB=credit_card_db \
  -p 5432:5432 \
  postgres:16-alpine
```

If this works, the issue is in docker-compose.yml configuration.

---

## 🔧 Expected Next Steps

1. **Run**: `docker-compose logs postgres`
2. **Share the error output**
3. **I'll provide specific fix based on the error**

---

**Status**: Waiting for PostgreSQL logs
**Next**: Share output of `docker-compose logs postgres`
