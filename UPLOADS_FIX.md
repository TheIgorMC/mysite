# 🖼️ CRITICAL FIX: Upload Images Persistence

**Issue:** Uploaded images (shop products, gallery items) were being deleted on container rebuild/restart.

**Root Cause:** The uploads directory was not mounted as a persistent Docker volume, so all uploaded files were stored inside the container and lost when the container was recreated.

---

## ✅ Fix Applied

### 1. Updated `docker-compose.yml`

**Added persistent volume for uploads:**
```yaml
volumes:
  # Persistent data
  - orion-data:/app/data
  - orion-logs:/app/site01/logs
  
  # CRITICAL: Mount uploads directory to persist uploaded images!
  - orion-uploads:/app/site01/app/static/uploads  # ← NEW!
```

**Added volume definition:**
```yaml
volumes:
  orion-data:
    driver: local
  orion-logs:
    driver: local
  orion-uploads:  # ← NEW!
    driver: local
```

---

## 🚀 How to Apply This Fix

### Option 1: Apply Without Losing Current Images (RECOMMENDED)

If you have images currently uploaded and visible:

```bash
# 1. Copy current images out of container FIRST
docker cp orion-project:/app/site01/app/static/uploads /tmp/uploads_backup

# 2. Apply the new configuration
docker compose down
docker compose up -d

# 3. Wait for container to start (10 seconds)
sleep 10

# 4. Copy images back into the persistent volume
docker cp /tmp/uploads_backup/. orion-project:/app/site01/app/static/uploads/

# 5. Set correct permissions
docker exec orion-project chmod -R 755 /app/site01/app/static/uploads
docker exec orion-project chown -R root:root /app/site01/app/static/uploads

# 6. Verify images are there
docker exec orion-project ls -la /app/site01/app/static/uploads/
```

### Option 2: Fresh Start (If images are already lost)

```bash
# Just restart with new configuration
docker compose down
docker compose up -d

# Re-upload all product images through admin panel
```

---

## 📁 Directory Structure

The uploads folder may contain:
```
uploads/
├── shop/              # Shop product images
├── gallery/           # Gallery images  
├── printing/          # 3D printing project images
├── electronics/       # Electronics project images
└── (other files)      # Misc uploads
```

All of these are now persisted in the `orion-uploads` Docker volume.

---

## 🔍 Verify Fix is Working

### Check if volume is mounted:
```bash
docker inspect orion-project | grep -A 10 Mounts
```

Should show:
```json
"Mounts": [
    {
        "Type": "volume",
        "Source": "mysite_orion-uploads",
        "Destination": "/app/site01/app/static/uploads",
        ...
    }
]
```

### Test persistence:
```bash
# 1. Upload an image through admin panel
# 2. Note the filename
# 3. Restart container
docker compose restart

# 4. Check if image still exists
docker exec orion-project ls -la /app/site01/app/static/uploads/shop/
```

If the image is still there after restart: **✅ FIX WORKING!**

---

## 🗂️ Manage Upload Volume

### View volume location:
```bash
docker volume inspect mysite_orion-uploads
```

### Backup uploads:
```bash
# Create backup
docker run --rm -v mysite_orion-uploads:/data -v $(pwd):/backup \
  alpine tar czf /backup/uploads-backup-$(date +%Y%m%d).tar.gz /data

# Or simpler:
docker cp orion-project:/app/site01/app/static/uploads ./uploads_backup
```

### Restore uploads:
```bash
# From tar.gz backup
docker run --rm -v mysite_orion-uploads:/data -v $(pwd):/backup \
  alpine tar xzf /backup/uploads-backup-20251030.tar.gz -C /

# Or simpler:
docker cp ./uploads_backup/. orion-project:/app/site01/app/static/uploads/
docker exec orion-project chmod -R 755 /app/site01/app/static/uploads
```

### Clear all uploads (if needed):
```bash
docker exec orion-project rm -rf /app/site01/app/static/uploads/*
docker exec orion-project touch /app/site01/app/static/uploads/.gitkeep
```

---

## ⚠️ Important Notes

### Why This Happened:
1. The volume mount was commented out in docker-compose.yml
2. When running `docker compose down` and `docker compose up`, Docker creates a fresh container
3. Fresh containers only have files from the Docker image (built from code)
4. Uploaded files were never in the image, so they disappeared

### This Fix Prevents:
- ✅ Images lost on container restart
- ✅ Images lost on container rebuild (`docker compose build`)
- ✅ Images lost on deployments
- ✅ Images lost on force updates (`force_deploy.sh`)

### What's Now Persistent:
- ✅ Database (orion-data volume)
- ✅ Logs (orion-logs volume)
- ✅ **Uploaded images (orion-uploads volume)** ← NEW!

---

## 🛠️ If Images Are Still Missing After Fix

### Check upload permissions:
```bash
docker exec orion-project ls -la /app/site01/app/static/uploads/
```

Should show:
```
drwxr-xr-x  2 root root 4096 Oct 30 12:00 .
```

### Fix permissions if needed:
```bash
docker exec orion-project chmod -R 755 /app/site01/app/static/uploads
docker exec orion-project chown -R root:root /app/site01/app/static/uploads
```

### Check if volume is actually mounted:
```bash
docker exec orion-project mount | grep uploads
```

Should show something like:
```
/dev/sda1 on /app/site01/app/static/uploads type ext4 (rw,relatime)
```

### Manually create subdirectories:
```bash
docker exec orion-project mkdir -p /app/site01/app/static/uploads/shop
docker exec orion-project mkdir -p /app/site01/app/static/uploads/gallery
docker exec orion-project mkdir -p /app/site01/app/static/uploads/printing
docker exec orion-project mkdir -p /app/site01/app/static/uploads/electronics
docker exec orion-project chmod -R 755 /app/site01/app/static/uploads
```

---

## 📊 Quick Commands Reference

```bash
# Check if fix is applied
docker inspect orion-project | grep uploads

# List uploaded files
docker exec orion-project find /app/site01/app/static/uploads -type f

# Count uploaded files
docker exec orion-project find /app/site01/app/static/uploads -type f | wc -l

# Check volume size
docker system df -v | grep orion-uploads

# Backup uploads
docker cp orion-project:/app/site01/app/static/uploads ./uploads_$(date +%Y%m%d)

# Restore uploads
docker cp ./uploads_backup/. orion-project:/app/site01/app/static/uploads/
```

---

## ✅ Verification Checklist

After applying fix:

- [ ] Run `docker compose down && docker compose up -d`
- [ ] Upload a test image through admin panel
- [ ] Run `docker compose restart`
- [ ] Check if image is still accessible
- [ ] Check volume is mounted: `docker inspect orion-project`
- [ ] Check files exist: `docker exec orion-project ls /app/site01/app/static/uploads/`

**If all checks pass: Your images will now persist forever!** 🎉

---

**Fixed:** October 30, 2025  
**Status:** ✅ RESOLVED - Images now persist across container restarts and rebuilds
