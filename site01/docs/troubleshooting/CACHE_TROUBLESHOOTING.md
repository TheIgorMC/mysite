# Flask Template Cache Troubleshooting Guide

## Problem
Flask serving cached templates even after Docker rebuild, preventing updates from being visible.

## Root Causes

### 1. Python Bytecode Cache
- `.pyc` files in `__pycache__` directories
- `.pyo` optimized bytecode files

### 2. Jinja Template Cache
- Jinja compiles templates to Python bytecode
- Can cache in memory or `/tmp`

### 3. Gunicorn Worker Pre-loading
- Workers can load old code if not restarted properly
- Pre-fork model can cache templates

### 4. Browser Caching
- Browser caches HTML responses
- Need proper Cache-Control headers

### 5. Docker Layer Caching
- Docker may use cached layers
- COPY commands can use old files

## Solutions Implemented

### 1. Dockerfile - Build-Time Cache Clearing
```dockerfile
# After COPY, clear all cache
RUN find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
RUN find /app -type f -name "*.pyc" -delete 2>/dev/null || true
```

### 2. Entrypoint - Runtime Cache Clearing
```bash
# Clear Python cache
find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find /app -type f -name "*.pyc" -delete 2>/dev/null || true
find /app -type f -name "*.pyo" -delete 2>/dev/null || true

# Force Jinja recompilation
find /app/site01/app/templates -type f -name "*.html" -exec touch {} +

# Clear /tmp cache
rm -rf /tmp/__pycache__
```

### 3. Flask Configuration
```python
# config.py - ProductionConfig
TEMPLATES_AUTO_RELOAD = True
SEND_FILE_MAX_AGE_DEFAULT = 0  # Disable static file caching
```

### 4. Flask App - Cache Control Headers
```python
# app/__init__.py
@app.after_request
def add_header(response):
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response
```

### 5. Gunicorn Configuration
```bash
# Worker recycling to prevent stale code
gunicorn --max-requests 1000 --max-requests-jitter 100
```

## Deployment Process

### Step 1: Commit and Push Changes
```bash
git add .
git commit -m "Update: Add cache busting improvements"
git push
```

### Step 2: Pull and Rebuild on Server
```bash
cd /path/to/mysite
git pull

# Build with NO cache
docker-compose build --no-cache --pull

# Or regular build (faster but may cache)
docker-compose build --pull
```

### Step 3: Stop and Remove Container
```bash
# Complete stop (not just restart)
docker-compose down

# Remove any orphaned containers
docker-compose rm -f
```

### Step 4: Start Fresh
```bash
docker-compose up -d
```

### Step 5: Verify
```bash
# Check logs for cache clearing
docker logs orion-project | grep -A 5 "Clearing Python cache"

# Should see:
# 🧹 Clearing Python cache...
# 🔄 Forcing template recompilation...
# ✅ Cache cleared and templates refreshed!

# Verify template modification times
docker exec orion-project ls -la /app/site01/app/templates/archery/competitions.html
```

### Step 6: Hard Refresh Browser
```
Windows: Ctrl + Shift + R
Mac: Cmd + Shift + R
Linux: Ctrl + Shift + R
```

## Nuclear Option - Complete Reset

If nothing else works:

```bash
# Stop everything
docker-compose down

# Remove container and volumes
docker-compose down -v

# Remove Docker images
docker rmi $(docker images -q orion-project)

# Clear Docker builder cache
docker builder prune -af

# Rebuild from scratch
docker-compose build --no-cache --pull
docker-compose up -d
```

## Verification Checklist

- [ ] Git pull shows "Already up to date"
- [ ] Docker build completes without errors
- [ ] Container logs show "Clearing Python cache"
- [ ] Container logs show "Forcing template recompilation"
- [ ] Template file modification time is recent: `docker exec orion-project stat /app/site01/app/templates/archery/competitions.html`
- [ ] Browser hard refresh (Ctrl+Shift+R)
- [ ] Check browser DevTools Network tab - HTML should be re-downloaded (200, not 304)
- [ ] Response headers include `Cache-Control: no-store`

## Debugging Commands

### Check if file is updated on server
```bash
# View file contents
docker exec orion-project cat /app/site01/app/templates/archery/competitions.html | grep -A 5 "loadInitialData"

# Check file timestamp
docker exec orion-project stat /app/site01/app/templates/archery/competitions.html

# Compare with Git
git show main:site01/app/templates/archery/competitions.html | grep -A 5 "loadInitialData"
```

### Check for cached bytecode
```bash
# Find all __pycache__ directories
docker exec orion-project find /app -type d -name __pycache__

# Should return nothing or very few results
```

### Check Flask configuration
```bash
# Check if TEMPLATES_AUTO_RELOAD is True
docker exec orion-project python -c "from app import create_app; app = create_app('production'); print(app.config['TEMPLATES_AUTO_RELOAD'])"
```

### Check Gunicorn workers
```bash
# List Gunicorn processes
docker exec orion-project ps aux | grep gunicorn

# Check worker restart count (should reset after deploy)
docker exec orion-project cat /proc/$(pidof gunicorn | awk '{print $1}')/stat
```

### Monitor in real-time
```bash
# Watch logs during deployment
docker logs -f orion-project
```

## Common Issues

### Issue: Changes visible locally but not on server
**Cause**: Git not synced or Docker using old layer
**Solution**: 
```bash
# On server
git status  # Check for uncommitted changes
git log -1  # Check last commit
git pull --rebase  # Force sync
```

### Issue: File updated but template not rendering changes
**Cause**: Jinja bytecode cache
**Solution**: Touch templates in entrypoint (already implemented)

### Issue: Changes appear after 5-10 minutes
**Cause**: Gunicorn workers not recycled
**Solution**: Use `--max-requests` flag (already implemented)

### Issue: Hard refresh doesn't work
**Cause**: Proxy/CDN caching (Cloudflare)
**Solution**: 
1. Purge Cloudflare cache
2. Check "Development Mode" in Cloudflare
3. Add bypass cache rule for HTML

## Prevention

### 1. Always Use CACHE_BUST
In `docker-compose.yml`:
```yaml
args:
  CACHE_BUST: ${CACHE_BUST:-1}
```

Increment when deploying:
```bash
CACHE_BUST=2 docker-compose build
```

### 2. Use Volume Mounts for Development
```yaml
volumes:
  - ./site01:/app/site01  # Live reload in dev
```

### 3. Separate Dev and Prod Configs
- Dev: DEBUG=True, TEMPLATES_AUTO_RELOAD=True
- Prod: DEBUG=False, TEMPLATES_AUTO_RELOAD=True (for updates)

### 4. Monitor Template Changes
Add logging:
```python
@app.before_request
def log_template_load():
    if app.debug:
        app.logger.info(f"Loading template for: {request.endpoint}")
```

## Files Modified

- `Dockerfile` - Added cache clearing after COPY
- `site01/entrypoint.sh` - Aggressive cache clearing on start
- `site01/config.py` - Added TEMPLATES_AUTO_RELOAD
- `site01/app/__init__.py` - Added cache control headers
- `docs/CACHE_TROUBLESHOOTING.md` - This guide

## Created: October 13, 2025
**Context**: Persistent template caching issues after Docker deployments
