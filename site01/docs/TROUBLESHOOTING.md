# 🔧 Troubleshooting Guide

This guide helps you fix common issues when deploying the Orion Project.

---

## 🚨 Critical Fixes Applied

### Issue 1: ModuleNotFoundError: No module named 'config'

**Error:**
```
ModuleNotFoundError: No module named 'config'
```

**Cause:** Python couldn't find the config module because of incorrect PYTHONPATH.

**Fix Applied:**
1. Updated `Dockerfile` to set correct PYTHONPATH
2. Changed working directory to `/app/site01`
3. Created `site01/app.py` as the application entry point
4. Updated Gunicorn command to use `app:app` instead of `site01.app:app`

**To rebuild after fix:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 📋 Quick Diagnostics

### Step 1: Check if Container is Running

```bash
docker-compose ps
```

**Expected output:**
```
NAME            IMAGE               STATUS
orion-project   mysite-orion-web    Up X minutes (healthy)
```

### Step 2: Check Logs

```bash
docker-compose logs --tail=50
```

**Look for:**
- ✅ "Listening at: http://0.0.0.0:5000"
- ✅ "Booting worker with pid: X"
- ❌ Any ERROR lines
- ❌ Any Traceback lines

### Step 3: Test Application

```bash
# From inside the host
curl http://localhost:6080

# From another machine
curl http://your-orangepi-ip:6080
```

**Expected:** HTML response with "Orion Project"

---

## 🐛 Common Issues & Solutions

### Issue: "Failed to find attribute 'app' in 'app'"

**Error:**
```
Failed to find attribute 'app' in 'app'.
gunicorn.errors.HaltServer: <HaltServer 'App failed to load.' 4>
```

**Cause:** Naming conflict between `app.py` file and `app/` package directory.

**Solution:**
This is **already fixed** in the latest code! The entry point is now `wsgi.py` instead of `app.py`.

**To apply the fix:**
```bash
# In Dockge: Click Down → Update/Rebuild → Up
# Or via SSH:
cd ~/dockge/stacks/orion-project
git pull
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

See [URGENT_FIX.md](URGENT_FIX.md) for details.

---

### Issue: "table users already exists"

**Error:**
```
sqlite3.OperationalError: table users already exists
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) table users already exists
```

**Cause:** Multiple Gunicorn workers trying to create tables simultaneously, or tables already exist from previous deployment.

**Solution:**
This is **already fixed** in the latest code! The app now checks if tables exist before trying to create them.

**To apply the fix:**
```bash
# Pull latest code
git pull origin main

# Rebuild
docker-compose down
docker-compose build
docker-compose up -d
```

**Alternative - Delete and recreate database:**
```bash
# Stop containers
docker-compose down

# Delete database volume
docker volume rm mysite_orion-data

# Start (will create fresh database)
docker-compose up -d
```

---

### Issue: Worker Failed to Boot (Import Errors)

**Symptoms:**
- Container keeps restarting
- Error: "Worker failed to boot"
- `ModuleNotFoundError: No module named 'config'`

**Solutions:**

1. **Check PYTHONPATH**
   ```bash
   docker-compose exec orion-web python -c "import sys; print(sys.path)"
   ```
   Should include `/app` and `/app/site01`

2. **Verify file structure**
   ```bash
   docker-compose exec orion-web ls -la /app/site01/
   docker-compose exec orion-web ls -la /app/site01/app/
   ```
   Should show `config.py`, `wsgi.py`, and `app/` directory

3. **Test imports manually**
   ```bash
   docker-compose exec orion-web python -c "from config import config; print('OK')"
   docker-compose exec orion-web python -c "from app import create_app; print('OK')"
   ```

### Issue: Port Already in Use

**Error:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:6080: bind: address already in use
```

**Solution:**

1. **Find what's using the port**
   ```bash
   sudo lsof -i :6080
   # or
   sudo netstat -tulpn | grep 6080
   ```

2. **Stop the conflicting service**
   ```bash
   sudo kill <PID>
   ```

3. **Or change the port in docker-compose.yml**
   ```yaml
   ports:
     - "6081:5000"  # Use 6081 instead
   ```

### Issue: Permission Denied on Volumes

**Error:**
```
Permission denied: '/app/data/orion.db'
```

**Solution:**

```bash
# Fix volume permissions
docker-compose exec orion-web chown -R root:root /app/data
docker-compose exec orion-web chown -R root:root /app/site01/logs

# Or recreate volumes
docker-compose down -v
docker-compose up -d
```

### Issue: Database Not Found

**Error:**
```
OperationalError: no such table: users
```

**Solution:**

```bash
# Access container
docker-compose exec orion-web bash

# Initialize database
cd /app/site01
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"

# Exit container
exit
```

### Issue: Out of Memory (OrangePi)

**Symptoms:**
- Container killed randomly
- OOM errors in system logs
- Slow performance

**Solution:**

1. **Reduce Gunicorn workers**
   
   Edit `Dockerfile`:
   ```dockerfile
   CMD ["python", "-m", "gunicorn", "-b", "0.0.0.0:5000", "-w", "2", "--timeout", "120", "app:app"]
   ```
   Change `-w 4` to `-w 2`

2. **Add memory limits**
   
   Edit `docker-compose.yml`:
   ```yaml
   services:
     orion-web:
       # ... existing config ...
       deploy:
         resources:
           limits:
             cpus: '2.0'
             memory: 512M
   ```

3. **Enable swap**
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
   ```

### Issue: Can't Connect to Orion API

**Error:**
```
ConnectionError: Failed to connect to api.orion-project.it
```

**Solution:**

1. **Check internet connectivity**
   ```bash
   docker-compose exec orion-web ping -c 3 api.orion-project.it
   ```

2. **Check DNS**
   ```bash
   docker-compose exec orion-web nslookup api.orion-project.it
   ```

3. **Test API directly**
   ```bash
   docker-compose exec orion-web curl -I https://api.orion-project.it:443
   ```

4. **Check Cloudflare credentials**
   ```bash
   # Verify .env has correct values
   cat .env | grep CF_ACCESS
   ```

### Issue: Translations Not Loading

**Symptoms:**
- Text appears in English only
- Translation keys showing instead of text

**Solution:**

1. **Verify translation files exist**
   ```bash
   docker-compose exec orion-web ls -la /app/site01/translations/
   ```
   Should show `en.json` and `it.json`

2. **Test translation loading**
   ```bash
   docker-compose exec orion-web python -c "import json; print(json.load(open('/app/site01/translations/en.json'))['site']['title'])"
   ```

3. **Check for JSON syntax errors**
   ```bash
   docker-compose exec orion-web python -m json.tool /app/site01/translations/en.json
   docker-compose exec orion-web python -m json.tool /app/site01/translations/it.json
   ```

---

## 🔍 Advanced Debugging

### Access Container Shell

```bash
docker-compose exec orion-web bash
```

Inside container:
```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check environment variables
env | grep -E 'FLASK|SECRET|DATABASE'

# Test Flask app manually
cd /app/site01
python -c "from app import create_app; app = create_app(); print('Flask app created successfully')"

# Run Flask development server (for testing only)
export FLASK_APP=app.py
flask run --host=0.0.0.0
```

### View All Logs

```bash
# Follow logs in real-time
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Only errors
docker-compose logs | grep -i error

# Save logs to file
docker-compose logs > orion-logs-$(date +%Y%m%d-%H%M%S).txt
```

### Check Resource Usage

```bash
# Container stats
docker stats orion-project

# Detailed inspect
docker inspect orion-project

# Disk usage
docker system df
```

### Network Issues

```bash
# Check if port is exposed
docker port orion-project

# Test from host
curl -I http://localhost:6080

# Test from another container
docker run --rm --network mysite_orion-network alpine:latest \
  sh -c "apk add curl && curl http://orion-web:5000"
```

---

## 🔄 Complete Rebuild

If all else fails, complete rebuild:

```bash
# Stop and remove everything
docker-compose down -v

# Remove images
docker rmi $(docker images 'mysite*' -q)

# Clear Docker cache
docker builder prune -af

# Rebuild from scratch
docker-compose build --no-cache

# Start fresh
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## 📊 Health Check

### Manual Health Check

```bash
# Check if app responds
curl -f http://localhost:6080/ || echo "Health check failed"

# Check specific endpoints
curl http://localhost:6080/archery
curl http://localhost:6080/static/css/style.css
```

### Docker Health Status

```bash
# View health status
docker inspect --format='{{.State.Health.Status}}' orion-project

# View health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' orion-project
```

---

## 🆘 Getting Help

If you're still stuck:

1. **Gather information:**
   ```bash
   # System info
   uname -a
   docker --version
   docker-compose --version
   
   # Save all logs
   docker-compose logs > debug-logs.txt
   
   # Container info
   docker inspect orion-project > container-info.txt
   ```

2. **Create GitHub issue** with:
   - Error message
   - Logs (debug-logs.txt)
   - Steps to reproduce
   - System information

3. **Check documentation:**
   - [DEPLOYMENT.md](DEPLOYMENT.md)
   - [DOCKGE_SETUP.md](DOCKGE_SETUP.md)
   - `site01/docs/INDEX.md`

---

## ✅ Verification Checklist

After fixing issues, verify:

- [ ] Container is running: `docker-compose ps`
- [ ] No errors in logs: `docker-compose logs | grep -i error`
- [ ] App responds: `curl http://localhost:6080`
- [ ] Homepage loads in browser
- [ ] Language switching works
- [ ] Theme switching works
- [ ] Archery page loads
- [ ] Database persists after restart
- [ ] Volumes are created: `docker volume ls | grep orion`

---

**Most issues are fixed by rebuilding with `--no-cache`! 🔄**
