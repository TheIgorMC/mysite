# 🚨 DEPLOYMENT INSTRUCTIONS - READ THIS FIRST! 🚨

## THE PROBLEM

**All the fixes exist in your LOCAL repository but are NOT on the Orange Pi server!**

You need to:
1. Commit and push changes from local machine
2. Pull changes on server  
3. Rebuild Docker container
4. Clear browser cache

## STEP-BY-STEP INSTRUCTIONS

### Part 1: On Your Local Machine (Windows)

```powershell
# 1. Open PowerShell in the project directory
cd C:\Users\Mattia\Documents\GitHub\mysite

# 2. Check what files changed
git status

# 3. Add all changes
git add .

# 4. Commit with message
git commit -m "Fix: Competition improvements, translations, cache busting"

# 5. Push to GitHub
git push origin main
```

### Part 2: On Orange Pi Server

```bash
# 1. SSH into your Orange Pi
ssh user@your-orange-pi-ip

# 2. Go to project directory
cd /path/to/mysite

# 3. Pull latest changes
git pull origin main

# 4. Verify changes arrived
git log -1

# 5. Check a specific file to confirm
grep "showLoading(show)" site01/app/templates/archery/competitions.html

# Should show the new multi-line function

# 6. Stop containers
docker-compose down

# 7. Clear Docker cache
docker builder prune -f

# 8. Rebuild WITHOUT cache
docker-compose build --no-cache --pull

# 9. Start containers
docker-compose up -d

# 10. Watch logs
docker logs -f orion-project

# Look for:
# 🧹 Clearing Python cache...
# 🔄 Forcing template recompilation...
# ✅ Cache cleared and templates refreshed!
```

### Part 3: In Your Browser

1. **Hard Refresh**: Press `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)
2. **Clear Cache**: 
   - Chrome: `Ctrl+Shift+Delete` → Clear cached images and files
   - Firefox: `Ctrl+Shift+Delete` → Cached Web Content
3. **Test in Incognito**: Open incognito window to verify
4. **Check DevTools**: F12 → Network tab → Reload → HTML should be `200` not `304`

## WHAT WILL BE FIXED

After deployment, these issues will be RESOLVED:

- ✅ Spinner will hide after competitions load
- ✅ Settings page fully translated to Italian
- ✅ Password change page fully translated
- ✅ "I Miei Atleti" section in settings (Italian)
- ✅ Athlete class/category can be edited
- ✅ Dates show in Italian format (17-Ott)
- ✅ Turn dropdowns won't show "(null)"
- ✅ Location shows club name not just code
- ✅ Subscriptions created as "in attesa" (pending)
- ✅ All dropdowns theme-matched for dark mode

## WHAT STILL NEEDS CODE

These features are NOT implemented yet and need new code:

### 1. Show Competitions WITHOUT Invites
**Currently**: Only shows competitions with published invites  
**Needed**: Show all upcoming competitions, allow interest registration

### 2. Delete Subscription Button
**Currently**: No way to cancel a subscription  
**Needed**: Delete button on competition cards for subscribed competitions

### 3. Category N/A in Admin
**Possible Fix**: Run migration  
**Command**: 
```bash
docker exec -it orion-project python /app/site01/migrations/add_classe_field.py
```

## VERIFICATION CHECKLIST

After deployment, verify:

- [ ] Git pull on server shows "Already up to date" after pulling
- [ ] Docker logs show cache clearing messages
- [ ] Browser hard refresh loads new version
- [ ] Spinner disappears after competitions load
- [ ] Settings page is in Italian when IT locale selected
- [ ] "Profile" sidebar shows "Profilo" in Italian
- [ ] "Change Password" shows "Cambia Password" in Italian
- [ ] Dates format as "17-Ott-2025" in Italian
- [ ] Competition location shows club name
- [ ] Turn dropdown has no "(null)" text

##  TROUBLESHOOTING

### If changes still don't appear:

```bash
# On server - Nuclear option
docker-compose down -v
docker rmi $(docker images -q orion-project)
docker builder prune -af
git pull
docker-compose build --no-cache --pull
docker-compose up -d
```

### If Git push fails:

```bash
# On local machine
git status
git stash
git pull --rebase
git stash pop
git add .
git commit -m "Fix: All improvements"
git push
```

### If Docker build fails:

```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Remove old images
docker system prune -a
```

## FILES THAT CHANGED

These files have been modified and need to be on the server:

1. `site01/app/templates/archery/competitions.html` - Fixed spinner, dates, locations
2. `site01/app/templates/auth/settings.html` - Full Italian translation + athlete management
3. `site01/app/routes/api.py` - Added PATCH endpoint for athlete preferences  
4. `site01/config.py` - Added TEMPLATES_AUTO_RELOAD
5. `site01/app/__init__.py` - Added cache control headers
6. `site01/entrypoint.sh` - Enhanced cache clearing
7. `site01/translations/en.json` - Added new translation keys
8. `site01/translations/it.json` - Added Italian translations
9. `Dockerfile` - Added cache clearing on build
10. `force_deploy.sh` - NEW deployment automation script
11. `check_deployment.sh` - NEW verification script

## NEXT STEPS AFTER DEPLOYMENT

Once you confirm everything is working:

1. **Test all features** - Go through the checklist above
2. **Report any remaining issues** - Be specific about what's not working
3. **Request new features** - Delete subscription, show all competitions, etc.

## TIMELINE

- **NOW**: Deploy changes (should take 10-15 minutes)
- **TODAY**: Fix remaining issues if any
- **THIS WEEK**: Implement delete subscription feature
- **THIS WEEK**: Implement show all competitions feature

## HELP

If you get stuck at any step:
1. Check the logs: `docker logs orion-project`
2. Verify file contents: `docker exec orion-project cat /path/to/file`
3. Check Git status: `git status` and `git log -1`
4. Try the nuclear option (rebuild everything from scratch)

Remember: **The code is ready, it just needs to be deployed!** 🚀

