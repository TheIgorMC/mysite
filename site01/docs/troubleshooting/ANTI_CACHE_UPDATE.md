# Anti-Cache Update - October 13, 2025

## Problem
Templates and code changes not appearing after Docker rebuild. Cache persisting despite restarts.

## Root Cause Analysis
Multiple caching layers:
1. **Python bytecode** (`.pyc` files)
2. **Jinja template compilation cache**
3. **Gunicorn worker memory**
4. **Browser HTTP cache**
5. **Docker layer cache**

## Solutions Implemented

### 1. Flask Configuration Updates
**File**: `site01/config.py`

```python
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    TEMPLATES_AUTO_RELOAD = True  # NEW: Force template reloading
    SEND_FILE_MAX_AGE_DEFAULT = 0  # NEW: Disable static file caching
```

**Effect**: Flask now watches templates and reloads them automatically.

---

### 2. HTTP Cache Control Headers
**File**: `site01/app/__init__.py`

```python
@app.after_request
def add_header(response):
    if response.content_type and 'text/html' in response.content_type:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response
```

**Effect**: Browsers are forced to fetch fresh HTML on every request.

---

### 3. Enhanced Entrypoint Script
**File**: `site01/entrypoint.sh`

**Changes**:
```bash
# Clear Python bytecode (.pyc, .pyo)
find /app -type d -name __pycache__ -exec rm -rf {} +
find /app -type f -name "*.pyc" -delete
find /app -type f -name "*.pyo" -delete

# Force Jinja recompilation (touch all templates)
find /app/site01/app/templates -type f -name "*.html" -exec touch {} +

# Clear /tmp cache
rm -rf /tmp/__pycache__
```

**Effect**: All cached bytecode cleared on every container start.

---

### 4. Gunicorn Worker Recycling
**File**: `site01/entrypoint.sh`

```bash
# Add worker recycling flags
exec python -m gunicorn -b 0.0.0.0:5000 -w 4 --timeout 120 \
  --max-requests 1000 \
  --max-requests-jitter 100 \
  wsgi:app
```

**Effect**: Workers restart after 1000 requests, preventing stale code in memory.

---

### 5. Force Deploy Script
**File**: `force_deploy.sh` (NEW)

Automates complete cache-clear deployment:
1. Git pull
2. Stop containers
3. Clear Docker build cache
4. Rebuild with `--no-cache`
5. Start containers
6. Verify deployment

**Usage**:
```bash
chmod +x force_deploy.sh
./force_deploy.sh
```

---

## Deployment Checklist

### On Server (Orange Pi)

1. **Pull changes**:
   ```bash
   cd /path/to/mysite
   git pull
   ```

2. **Use force deploy script**:
   ```bash
   chmod +x force_deploy.sh
   ./force_deploy.sh
   ```

   **OR manually**:
   ```bash
   docker-compose down
   docker builder prune -f
   CACHE_BUST=$(date +%s) docker-compose build --no-cache --pull
   docker-compose up -d
   ```

3. **Verify in logs**:
   ```bash
   docker logs orion-project | grep -A 5 "Clearing Python cache"
   ```

   Should see:
   ```
   🧹 Clearing Python cache...
   🔄 Forcing template recompilation...
   ✅ Cache cleared and templates refreshed!
   ```

4. **Check template timestamp**:
   ```bash
   docker exec orion-project stat /app/site01/app/templates/archery/competitions.html
   ```

### On Browser

1. **Hard refresh**: `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)

2. **Clear cache**:
   - Chrome: `Ctrl+Shift+Delete` → Clear cached images and files
   - Firefox: `Ctrl+Shift+Delete` → Cached Web Content

3. **Verify in DevTools**:
   - Open DevTools (F12)
   - Network tab
   - Reload page
   - Check HTML response should be `200` (not `304 Not Modified`)
   - Check response headers: `Cache-Control: no-store`

---

## Why Previous Fixes Didn't Work

### Attempt 1: `docker-compose restart`
**Problem**: Doesn't rebuild image, uses cached layers

### Attempt 2: `docker-compose build --pull`
**Problem**: Docker can still use cached layers for unchanged lines

### Attempt 3: Editing files in container
**Problem**: Changes lost on restart, doesn't fix source

### Attempt 4: Multiple restarts
**Problem**: Gunicorn workers kept old code in memory

### Solution: All of the above combined
- Force rebuild (`--no-cache`)
- Clear all bytecode caches (entrypoint)
- Force template recompilation (touch)
- Recycle workers (max-requests)
- Disable HTTP caching (headers)
- Enable auto-reload (config)

---

## Verification Commands

### Check file on server matches Git:
```bash
# On server
docker exec orion-project md5sum /app/site01/app/templates/archery/competitions.html

# Locally
md5sum site01/app/templates/archery/competitions.html
```

### Check for cached bytecode:
```bash
docker exec orion-project find /app -name "*.pyc" -o -name "*.pyo"
# Should return nothing
```

### Check Flask config:
```bash
docker exec orion-project python -c "
from app import create_app
app = create_app('production')
print('TEMPLATES_AUTO_RELOAD:', app.config.get('TEMPLATES_AUTO_RELOAD'))
print('SEND_FILE_MAX_AGE_DEFAULT:', app.config.get('SEND_FILE_MAX_AGE_DEFAULT'))
"
```

### Monitor real-time:
```bash
docker logs -f orion-project
```

---

## Files Modified

1. ✅ `site01/config.py` - Added TEMPLATES_AUTO_RELOAD and SEND_FILE_MAX_AGE_DEFAULT
2. ✅ `site01/app/__init__.py` - Added cache control headers
3. ✅ `site01/entrypoint.sh` - Enhanced cache clearing + template touching
4. ✅ `force_deploy.sh` - NEW automated deployment script
5. ✅ `docs/CACHE_TROUBLESHOOTING.md` - NEW comprehensive guide

---

## Expected Behavior After Deploy

1. ✅ Container logs show cache clearing messages
2. ✅ Template modification times are recent (today's date)
3. ✅ No `.pyc` files in container
4. ✅ Browser receives `Cache-Control: no-store` header
5. ✅ Changes visible immediately after hard refresh
6. ✅ Workers recycle every ~1000 requests

---

## If Problems Persist

### Nuclear Option:
```bash
# Complete reset
docker-compose down -v
docker rmi $(docker images -q orion-project)
docker builder prune -af
git pull
docker-compose build --no-cache --pull
docker-compose up -d
```

### Check Cloudflare:
If using Cloudflare proxy:
1. Go to Cloudflare dashboard
2. Caching → Configuration
3. Enable "Development Mode" (3 hours)
4. OR Purge cache for HTML files

### Check Browser:
- Try incognito/private window
- Try different browser
- Check DevTools → Disable cache checkbox

---

## Prevention

1. **Always use force_deploy.sh for production updates**
2. **Increment CACHE_BUST** in docker-compose.yml
3. **Monitor logs** after each deployment
4. **Hard refresh browser** after server updates
5. **Document cache issues** when they occur

---

## Testing

After this deploy, test:
- [ ] Spinner hides properly
- [ ] Turn dropdown shows no "(null)"
- [ ] Dates in Italian format (17-Ott)
- [ ] Location shows club name
- [ ] Settings page shows "My Athletes"
- [ ] Athlete dropdown styled correctly
- [ ] All translations working

---

## Success Criteria

✅ Changes visible within 30 seconds of deployment  
✅ No need to wait 5-10 minutes  
✅ Hard refresh always shows latest version  
✅ Logs confirm cache clearing  
✅ Template timestamps are recent  

---

## Created: October 13, 2025
**Context**: Persistent cache issues preventing template updates from being visible
**Solution**: Multi-layer cache busting across Docker, Python, Flask, Gunicorn, and browser
