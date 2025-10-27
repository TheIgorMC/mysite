# 🔄 Force Rebuild in Dockge - Multiple Options

Dockge LOVES caching. Here are your options to force a proper rebuild.

---

## ✅ **Option 1: Cache Bust Variable (BEST METHOD)**

**Already implemented in the code!**

### How it works:
The Dockerfile has:
```dockerfile
ARG CACHE_BUST=1
RUN echo "Cache bust: ${CACHE_BUST}"
COPY site01/ ./site01/
```

The `RUN echo` command **uses** the ARG variable. When the ARG value changes, Docker can't reuse the cached RUN layer, forcing a rebuild from that point forward (including the COPY command).

The docker-compose.yml has:
```yaml
build:
  context: .
  dockerfile: Dockerfile
  args:
    CACHE_BUST: 2  # Change this number to force rebuild
```

### To force rebuild in Dockge:

1. **Open Dockge** in browser (`http://orangepi-ip:5001`)
2. **Find your stack** (Orion Project)
3. Click **"Edit"** or **"Edit Compose"**
4. Find this section:
   ```yaml
   build:
     args:
       CACHE_BUST: 2
   ```
5. **Change the number** to anything different (e.g., `3`, `4`, `5`, etc.)
6. Click **"Save"**
7. Click **"Down"** to stop containers
8. Click **"Up"** to start (this triggers rebuild)

**Important:** 
- Must click "Down" then "Up" - just "Restart" won't rebuild!
- Each rebuild needs a DIFFERENT number (Docker compares values)
- You'll see "Cache bust: 3" in build logs when it works

---

## 🔥 **Option 2: Delete Docker Image via SSH**

If cache bust doesn't work or Dockge is stuck:

```bash
# SSH into OrangePi
ssh user@orangepi-ip

# Navigate to stack
cd /root/dockge/stacks/orion-project

# Stop container
docker-compose down

# Find image ID
docker images | grep mysite

# Delete the image
docker rmi <IMAGE_ID>

# Or delete all mysite images
docker rmi $(docker images | grep mysite | awk '{print $3}')

# Go back to Dockge and click "Up"
# Or rebuild via SSH:
docker-compose up -d --build
```

---

## 💪 **Option 3: Nuclear Option - Complete Rebuild via SSH**

When nothing else works:

```bash
# SSH to OrangePi
cd /root/dockge/stacks/orion-project

# Stop everything
docker-compose down

# Remove all related images
docker rmi $(docker images | grep mysite | awk '{print $3}')

# Clear ALL Docker cache
docker builder prune -af

# Pull latest code
git pull origin main

# Verify fix is in code
head -15 site01/app/__init__.py
# Should show sys.path.insert around line 11

# Force rebuild
docker-compose build --no-cache

# Start
docker-compose up -d

# Check logs
docker-compose logs -f
```

---

## 🎯 **Option 4: Modify Dockerfile Directly**

Quick dirty trick in Dockge:

1. Edit your stack
2. At the top of Dockerfile, add/change a comment:
   ```dockerfile
   # Force rebuild - 2025-10-08-14:30
   ```
3. Save
4. Down → Up

Any change to Dockerfile forces rebuild!

---

## ⚡ **Option 5: Delete site01/ Directory**

The nuclear option for corrupted files:

```bash
# SSH to OrangePi
cd /root/dockge/stacks/orion-project

# Stop containers
docker-compose down

# Delete site01
rm -rf site01/

# Restore from git
git checkout origin/main -- site01/
# or
git restore --source=origin/main site01/

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## 📊 **Troubleshooting Cache Bust**

### Check if it's working:

During build, you should see:
```
Step X/Y : ARG CACHE_BUST=1
Step X/Y : RUN echo "Cache bust: 3"
 ---> Running in abc123
Cache bust: 3
 ---> def456
Step X/Y : COPY site01/ ./site01/
 ---> ghi789
```

If you see `---> Using cache` on the RUN echo step, the number didn't change!

### Debug in Dockge:

1. Check build logs in Dockge
2. Look for "Cache bust: X" message
3. If number matches what you set, it's working
4. If you see "Using cache", increment CACHE_BUST again

---

## 🔍 **Why Cache Bust Works**

Docker caching works layer-by-layer:
1. If a layer hasn't changed, Docker reuses cache
2. `ARG` alone doesn't invalidate cache (Docker quirk)
3. `RUN echo "${ARG}"` uses the ARG value in a command
4. When ARG changes, the RUN output changes
5. Docker can't use cached RUN layer → rebuilds from there
6. Everything after (COPY, etc.) also rebuilds

The `RUN echo` is the "cache breaker"!

---

## ✅ **Verification Checklist**

After rebuild, verify:
- [ ] Check build logs for "Cache bust: X" with YOUR number
- [ ] No "Using cache" after the Cache bust line
- [ ] Container starts without errors
- [ ] Logs show line 12 for import error (not line 8)
  - Line 8 = old code (cached)
  - Line 12 = new code (with sys.path.insert)
- [ ] App accessible at `http://orangepi-ip:6080`

---

## 🎯 **Recommended Workflow**

1. **First attempt:** Increment CACHE_BUST (easiest)
2. **Still cached:** Delete image via SSH (Option 2)
3. **Still broken:** Nuclear rebuild (Option 3)
4. **Code corrupted:** Delete site01/ and restore (Option 5)

---

## 📝 **Current Setup in Your Files**

**Dockerfile:**
```dockerfile
ARG CACHE_BUST=1
RUN echo "Cache bust: ${CACHE_BUST}"
COPY site01/ ./site01/
```

**docker-compose.yml:**
```yaml
build:
  args:
    CACHE_BUST: 2  # ← Change this number
```

---

**The RUN echo trick forces Docker to see the cache as invalid when the number changes!** 🚀
