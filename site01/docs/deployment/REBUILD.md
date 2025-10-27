# 🔄 How to Rebuild After Fixes

## Quick Rebuild

If you just updated the code (including the recent import fixes):

```bash
# Navigate to project directory
cd ~/mysite

# Stop containers
docker-compose down

# Rebuild without cache (IMPORTANT!)
docker-compose build --no-cache

# Start containers
docker-compose up -d

# Watch logs
docker-compose logs -f
```

---

## What to Look For

### ✅ Success Signs

In the logs, you should see:
```
orion-web  | [INFO] Listening at: http://0.0.0.0:5000
orion-web  | [INFO] Using worker: sync
orion-web  | [INFO] Booting worker with pid: 7
orion-web  | [INFO] Booting worker with pid: 8
orion-web  | [INFO] Booting worker with pid: 9
orion-web  | [INFO] Booting worker with pid: 10
```

### ❌ Error Signs

If you see:
```
ModuleNotFoundError: No module named 'config'
```

This means the old image is cached. Make sure you used `--no-cache`!

---

## Verify It's Working

### 1. Check Container Status
```bash
docker-compose ps
```

Should show:
```
NAME            STATE
orion-project   Up X seconds (healthy)
```

### 2. Test with curl
```bash
curl http://localhost:6080
```

Should return HTML with "Orion Project"

### 3. Test in Browser
Open: `http://your-orangepi-ip:6080`

Should show the homepage

---

## Still Not Working?

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for:
- Detailed diagnostics
- Common issues
- Advanced debugging
- How to get help

---

## Quick Tips

**Always use `--no-cache` when rebuilding after code changes!**

```bash
# ❌ Bad - might use old cached layers
docker-compose build

# ✅ Good - forces complete rebuild
docker-compose build --no-cache
```

**Check logs immediately after starting:**
```bash
docker-compose up -d && docker-compose logs -f
```

**If you change docker-compose.yml, use:**
```bash
docker-compose down
docker-compose up -d --force-recreate
```

---

**The fixes for the import errors are already in the code. Just rebuild! 🚀**
