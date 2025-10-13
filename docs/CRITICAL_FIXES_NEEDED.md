# CRITICAL FIXES NEEDED - October 13, 2025

## Issues Reported

1. ❌ Spinner still shows after loading
2. ❌ Competitions without invites are not visible
3. ❌ Category shows N/A in admin area
4. ❌ No save on the athlete management section
5. ❌ Loads of English text in IT locale pages
6. ❌ Dates still not respecting the locale
7. ❌ No way to delete a subscription

## Root Cause

**THE CHANGES AREN'T ON THE SERVER!**

The cache-busting fixes were added to the LOCAL repository but **NOT DEPLOYED** to the Orange Pi server yet!

## What to Do RIGHT NOW

### On Orange Pi Server:

```bash
cd /path/to/mysite

# 1. Pull latest changes (THIS IS CRITICAL!)
git pull

# 2. Check what changed
git log -1 --stat

# 3. Verify changes are in files
grep "showLoading(show)" site01/app/templates/archery/competitions.html

# 4. Force deploy with no cache
docker-compose down
docker builder prune -f
docker-compose build --no-cache --pull
docker-compose up -d

# 5. Verify deployment
docker logs orion-project | tail -30

# 6. Check template file
docker exec orion-project cat /app/site01/app/templates/archery/competitions.html | grep "showLoading" | head -5
```

### Browser:
1. Hard refresh: Ctrl+Shift+R
2. Clear cache completely
3. Try incognito window

## Files That Need to Be on Server

These files were modified locally but MAY NOT BE on server:

1. ✅ `site01/app/templates/archery/competitions.html` - Spinner fix, dates, etc.
2. ✅ `site01/app/templates/auth/settings.html` - Athlete management
3. ✅ `site01/app/routes/api.py` - PATCH endpoint for athletes
4. ✅ `site01/config.py` - TEMPLATES_AUTO_RELOAD
5. ✅ `site01/app/__init__.py` - Cache-Control headers
6. ✅ `site01/entrypoint.sh` - Template touching
7. ✅ `site01/translations/en.json` - New keys
8. ✅ `site01/translations/it.json` - New keys
9. ✅ `Dockerfile` - Cache clearing
10. ✅ `force_deploy.sh` - Deployment script
11. ✅ `check_deployment.sh` - Verification script

## Verification Commands

Run these on the Orange Pi to verify:

```bash
# 1. Check if competitions.html has the fixes
docker exec orion-project grep -A 10 "function showLoading" /app/site01/app/templates/archery/competitions.html

# Should show:
# function showLoading(show) {
#     const loading = document.getElementById('loading');
#     const grid = document.getElementById('competitions-grid');
#     ...

# 2. Check if settings.html has athlete management
docker exec orion-project grep -c "my_athletes" /app/site01/app/templates/auth/settings.html

# Should return a number > 0

# 3. Check if translations have new keys
docker exec orion-project grep -c "profile_information" /app/site01/translations/it.json

# Should return 1

# 4. Check API endpoint exists
docker exec orion-project grep -A 5 "PATCH.*authorized-athletes" /app/site01/app/routes/api.py

# Should show the PATCH endpoint code
```

## If Changes Aren't There

### Option 1: Force Push from Local
```bash
# On your local machine
cd c:\Users\Mattia\Documents\GitHub\mysite

# Commit everything
git add .
git commit -m "Fix: All competition improvements and cache busting"
git push

# Then on server
git pull --rebase
```

### Option 2: Copy Files Directly
Use SCP or similar to copy the changed files directly to the server, then rebuild.

## After Deployment, Test Checklist

- [ ] `docker logs orion-project` shows "Clearing Python cache"
- [ ] `docker logs orion-project` shows "Forcing template recompilation"
- [ ] Spinner disappears after competitions load
- [ ] Settings page shows "I Miei Atleti" section (in Italian)
- [ ] All text in settings is Italian when IT locale selected
- [ ] Dates show as "17-Ott" format in Italian
- [ ] Admin area shows categoria properly (not N/A)
- [ ] Changing athlete class/category in settings works

## Issues That STILL Need Fixing

After deployment, these issues will STILL exist and need new code:

### 1. Show Competitions Without Invites
**Status**: Not implemented
**Code needed**: Modify competition filtering logic
**Location**: `competitions.html` - filterCompetitions() function

### 2. Delete Subscription Button
**Status**: Not implemented  
**Code needed**: 
- Add DELETE endpoint in `api.py`
- Add delete button in competition cards
- Add confirmation dialog

### 3. Category N/A in Admin
**Status**: Might be fixed if migration ran
**Check**: Run `docker exec -it orion-project python /app/site01/migrations/add_classe_field.py`

## Priority Actions

1. **IMMEDIATE**: Deploy changes to server (git pull + rebuild)
2. **IMMEDIATE**: Run database migration
3. **HIGH**: Add delete subscription feature
4. **MEDIUM**: Show competitions without invites

## Timeline

- **Right now**: Deploy existing fixes
- **Today**: Implement delete subscription
- **This week**: Implement competitions without invites feature

