# Image Loading Troubleshooting Guide

## 🔍 Problem: Images Not Loading on Subsection Pages

### Quick Diagnosis

The images are **correctly configured** in the code and **present** in the right location. Here's what might be happening:

---

## ✅ Current Status

### Images Present in Correct Location:
```
site01/app/static/media/
├── 3d_gallery.jpg ✅
├── 3d_quote.jpg ✅
├── 3d_shop.jpg ✅
├── el_gallery.jpg ✅
├── el_shop.jpg ✅
├── 3dprinting.jpg (old)
├── circuit.jpg (old)
├── archery.jpg
├── background.png
└── ... (other images)
```

### All Templates Use Correct Path:
```jinja
{{ url_for('static', filename='media/3d_gallery.jpg') }}
```

This generates URL: `/static/media/3d_gallery.jpg`

---

## 🐛 Possible Issues & Solutions

### Issue 1: Browser Cache 🔄

**Symptom:** Old images still showing, new images not loading

**Solution:**
```bash
# Hard refresh in browser
Windows: Ctrl + Shift + R
Mac: Cmd + Shift + R

# Or clear browser cache
```

**Or add cache-busting parameter:**
```jinja
{{ url_for('static', filename='media/3d_gallery.jpg') }}?v=2
```

---

### Issue 2: File Permissions 🔒

**Symptom:** 403 Forbidden errors in browser console

**Solution:**
```bash
# On server, fix permissions
chmod 644 site01/app/static/media/*.jpg

# Or for all media files
find site01/app/static/media -type f -exec chmod 644 {} \;
```

---

### Issue 3: Docker Volume Mapping 🐳

**Symptom:** Images work locally but not in Docker

**Problem:** Static files not properly mapped

**Check docker-compose.yml:**
```yaml
volumes:
  - ./site01:/app/site01  # Should map the entire site01 folder
```

**Solution:**
```bash
# Restart container to remount volumes
docker-compose down
docker-compose up -d

# Or copy files directly into container
docker cp site01/app/static/media/3d_gallery.jpg orion-project:/app/site01/app/static/media/
docker cp site01/app/static/media/3d_quote.jpg orion-project:/app/site01/app/static/media/
docker cp site01/app/static/media/3d_shop.jpg orion-project:/app/site01/app/static/media/
docker cp site01/app/static/media/el_gallery.jpg orion-project:/app/site01/app/static/media/
docker cp site01/app/static/media/el_shop.jpg orion-project:/app/site01/app/static/media/
```

---

### Issue 4: Nginx/Reverse Proxy Configuration 🌐

**Symptom:** HTML loads but static files 404

**Problem:** Proxy not configured to serve static files

**Check Nginx config:**
```nginx
location /static {
    alias /path/to/site01/app/static;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

**Or let Flask serve static files** (development):
```python
# Flask will handle /static/ automatically
```

---

### Issue 5: Case Sensitivity 📝

**Symptom:** Works on Windows, fails on Linux

**Problem:** Filename case mismatch

**Verify exact filenames:**
```bash
ls -la site01/app/static/media/ | grep -E "(3d_|el_)"
```

Should match exactly:
- `3d_gallery.jpg` (lowercase, underscore)
- `3d_quote.jpg`
- `3d_shop.jpg`
- `el_gallery.jpg`
- `el_shop.jpg`

**NOT:**
- `3D_gallery.jpg` ❌
- `3d-gallery.jpg` ❌
- `3d_Gallery.jpg` ❌

---

## 🔧 Debugging Steps

### Step 1: Check Browser Console

Open browser DevTools (F12) → Console tab

Look for errors like:
```
GET http://localhost:5000/static/media/3d_gallery.jpg 404 Not Found
GET http://localhost:5000/static/media/3d_gallery.jpg 403 Forbidden
```

### Step 2: Test Direct URL

Try accessing image directly in browser:
```
http://your-domain.com/static/media/3d_gallery.jpg
```

**If it loads:** Problem is in template
**If it doesn't load:** Problem is in server configuration

### Step 3: Check Network Tab

DevTools → Network tab → Reload page

Filter by "Img" to see:
- Which images are loading
- Which are failing
- HTTP status codes
- Response times

### Step 4: Verify File Paths

**In production container:**
```bash
# Enter container
docker exec -it orion-project /bin/bash

# Check files exist
ls -la /app/site01/app/static/media/3d_*
ls -la /app/site01/app/static/media/el_*

# Check file sizes (should not be 0)
du -h /app/site01/app/static/media/3d_*

# Exit container
exit
```

### Step 5: Check Flask Logs

```bash
# View container logs
docker logs orion-project --tail=100

# Or if using systemctl
journalctl -u orion-project -n 100
```

Look for:
- 404 errors for static files
- Permission denied errors
- Path not found errors

---

## 🎯 Quick Fix Checklist

Run these commands in order:

```bash
# 1. Verify images are in correct location
ls -lh site01/app/static/media/*.jpg

# 2. Fix permissions
chmod 644 site01/app/static/media/*.jpg

# 3. If using Docker, restart
docker-compose restart

# 4. Clear browser cache
# (Ctrl+Shift+R in browser)

# 5. Check in browser console for errors
# (F12 → Console tab)
```

---

## 🔍 Comparison: Homepage vs Subsections

### Why Homepage Works:

**Homepage uses:**
```jinja
<img src="{{ url_for('static', filename='media/archery.jpg') }}">
<img src="{{ url_for('static', filename='media/3dprinting.jpg') }}">
<img src="{{ url_for('static', filename='media/circuit.jpg') }}">
```

### Subsection Pages Use:

**3D Printing:**
```jinja
<img src="{{ url_for('static', filename='media/3d_gallery.jpg') }}">
<img src="{{ url_for('static', filename='media/3d_quote.jpg') }}">
<img src="{{ url_for('static', filename='media/3d_shop.jpg') }}">
```

**Electronics:**
```jinja
<img src="{{ url_for('static', filename='media/el_gallery.jpg') }}">
<img src="{{ url_for('static', filename='media/el_shop.jpg') }}">
```

### Key Difference:

**NONE!** Both use identical path structure: `/static/media/*.jpg`

**Therefore:** If homepage images work, subsection images should also work (assuming files exist with correct names)

---

## 💡 Most Likely Causes

### 1. Files Not Uploaded to Production (90% chance)

**Check:**
```bash
# On production server
ls site01/app/static/media/3d_*
ls site01/app/static/media/el_*
```

**Fix:**
```bash
# Upload missing files
scp site01/app/static/media/3d_*.jpg user@server:/path/to/site01/app/static/media/
scp site01/app/static/media/el_*.jpg user@server:/path/to/site01/app/static/media/
```

### 2. Browser Cache (5% chance)

**Fix:** Hard refresh (Ctrl+Shift+R)

### 3. Docker Volume Not Mounted (3% chance)

**Fix:** `docker-compose down && docker-compose up -d`

### 4. Permission Issue (2% chance)

**Fix:** `chmod 644 site01/app/static/media/*.jpg`

---

## ✅ Verification Test

Create this test page to verify all images:

**File:** `site01/app/templates/test_images.html`

```html
{% extends "base.html" %}

{% block title %}Image Test{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-12">
    <h1 class="text-3xl font-bold mb-8">Image Loading Test</h1>
    
    <!-- Old Images (Should Work) -->
    <h2 class="text-2xl font-bold mb-4">Old Images (Homepage)</h2>
    <div class="grid grid-cols-3 gap-4 mb-8">
        <div>
            <p class="text-sm mb-2">archery.jpg</p>
            <img src="{{ url_for('static', filename='media/archery.jpg') }}" 
                 class="w-full h-40 object-cover" 
                 onerror="this.parentElement.style.border='3px solid red'">
        </div>
        <div>
            <p class="text-sm mb-2">3dprinting.jpg</p>
            <img src="{{ url_for('static', filename='media/3dprinting.jpg') }}" 
                 class="w-full h-40 object-cover"
                 onerror="this.parentElement.style.border='3px solid red'">
        </div>
        <div>
            <p class="text-sm mb-2">circuit.jpg</p>
            <img src="{{ url_for('static', filename='media/circuit.jpg') }}" 
                 class="w-full h-40 object-cover"
                 onerror="this.parentElement.style.border='3px solid red'">
        </div>
    </div>

    <!-- New Images (Testing) -->
    <h2 class="text-2xl font-bold mb-4">New Images (3D Printing)</h2>
    <div class="grid grid-cols-3 gap-4 mb-8">
        <div>
            <p class="text-sm mb-2">3d_gallery.jpg</p>
            <img src="{{ url_for('static', filename='media/3d_gallery.jpg') }}" 
                 class="w-full h-40 object-cover"
                 onerror="this.parentElement.style.border='3px solid red'">
        </div>
        <div>
            <p class="text-sm mb-2">3d_quote.jpg</p>
            <img src="{{ url_for('static', filename='media/3d_quote.jpg') }}" 
                 class="w-full h-40 object-cover"
                 onerror="this.parentElement.style.border='3px solid red'">
        </div>
        <div>
            <p class="text-sm mb-2">3d_shop.jpg</p>
            <img src="{{ url_for('static', filename='media/3d_shop.jpg') }}" 
                 class="w-full h-40 object-cover"
                 onerror="this.parentElement.style.border='3px solid red'">
        </div>
    </div>

    <h2 class="text-2xl font-bold mb-4">New Images (Electronics)</h2>
    <div class="grid grid-cols-2 gap-4 mb-8">
        <div>
            <p class="text-sm mb-2">el_gallery.jpg</p>
            <img src="{{ url_for('static', filename='media/el_gallery.jpg') }}" 
                 class="w-full h-40 object-cover"
                 onerror="this.parentElement.style.border='3px solid red'">
        </div>
        <div>
            <p class="text-sm mb-2">el_shop.jpg</p>
            <img src="{{ url_for('static', filename='media/el_shop.jpg') }}" 
                 class="w-full h-40 object-cover"
                 onerror="this.parentElement.style.border='3px solid red'">
        </div>
    </div>

    <div class="bg-yellow-100 dark:bg-yellow-900 p-4 rounded mt-8">
        <p><strong>Note:</strong> Images with red border failed to load.</p>
        <p>Check browser console (F12) for error details.</p>
    </div>
</div>
{% endblock %}
```

**Add route in main.py:**
```python
@bp.route('/test-images')
def test_images():
    return render_template('test_images.html')
```

**Then visit:** `http://your-domain.com/test-images`

Images with red border = failed to load

---

## 📊 Summary

| Check | Status | Action if Failed |
|-------|--------|------------------|
| Files exist locally | ✅ | - |
| Files in correct folder | ✅ | - |
| Path syntax correct | ✅ | - |
| Files on production | ❓ | Upload files |
| Permissions correct | ❓ | `chmod 644 *.jpg` |
| Docker volume mapped | ❓ | Restart container |
| Browser cache clear | ❓ | Ctrl+Shift+R |

---

## 🚀 Production Deployment Checklist

Before deploying:

- [ ] All 5 new images uploaded to production
- [ ] Files in `/app/site01/app/static/media/` (not root `/media/`)
- [ ] File permissions set to 644
- [ ] Docker container restarted (if using Docker)
- [ ] Browser cache cleared
- [ ] Tested direct URL access
- [ ] Checked browser console for errors
- [ ] Verified file sizes are not 0 bytes

---

## 📞 Still Not Working?

Run this diagnostic command and share the output:

```bash
# Full diagnostic
echo "=== File Check ==="
ls -lh site01/app/static/media/{3d_*,el_*}.jpg

echo -e "\n=== In Container (if Docker) ==="
docker exec orion-project ls -lh /app/site01/app/static/media/ | grep -E "(3d_|el_)"

echo -e "\n=== URL Test ==="
curl -I http://localhost:5000/static/media/3d_gallery.jpg

echo -e "\n=== Permissions ==="
stat site01/app/static/media/3d_gallery.jpg
```

This will show:
- If files exist
- File sizes
- Permissions
- Whether URLs are accessible

---

**Most Common Solution:** The files probably aren't uploaded to production yet. Upload them and restart! 🎯
