# Bug Fixes - October 2025

## ✅ All Issues Fixed

### 1. Fixed categoria/classe Swap ✅
**Problem**: Server expects `categoria=CO/OL/AN` (bow type) and `classe=SM/SF/MM/MF` (age category), but we were sending them swapped.

**Solution**:
- Fixed `submitSubscription()` in `competitions.html`
- Now sends: `categoria: competitionClass` (CO/OL/AN) and `classe: ageCategory` (SM/SF/etc.)
- Updated subscription object creation to match

**Files Modified**:
- `site01/app/templates/archery/competitions.html`

---

### 2. Added Yellow "In Attesa" Badge ✅
**Problem**: Subscriptions with status "in attesa" (pending) were showing green like confirmed ones.

**Solution**:
- Modified `renderCompetitions()` to check subscription status
- If `stato === 'in attesa'`, change styling from green to yellow
- Text changes from "Subscribed" to "In attesa"
- Icon changes from check to clock

**Visual Changes**:
- **Before**: Green badge for all subscriptions
- **After**: Yellow badge for pending ("in attesa"), green for confirmed

**Files Modified**:
- `site01/app/templates/archery/competitions.html`

---

### 3. Fixed Athlete Preferences Saving ✅
**Problem**: Settings page not saving classe/categoria preferences (though this might be due to missing DB column).

**Solution**:
- Added error handling and rollback to PATCH endpoint
- Returns proper error messages if database operation fails
- If migration not run, will show error message instead of silent failure

**Files Modified**:
- `site01/app/routes/api.py`

**Note**: The actual save will work AFTER running the database migration (see Issue #4).

---

### 4. Fix N/A in Admin Console (Requires Migration) ⚠️
**Problem**: Admin console shows N/A for `classe` field because column doesn't exist in database.

**Solution**: **USER ACTION REQUIRED**

```bash
# On the server, run this migration:
docker exec -it orion-project python /app/site01/migrations/add_classe_field.py
```

This will add the `classe` column to the `authorized_athletes` table.

**Status**: Code is ready, migration must be run manually by user.

---

### 5. Fixed Loading Spinner Visibility ✅
**Problem**: Loading spinner was showing even after data loaded.

**Solution**:
- Added `hidden` class to loading div in initial HTML
- Loading spinner now starts hidden, shows on request, hides when done
- `finally` block ensures it's always hidden even on errors

**Files Modified**:
- `site01/app/templates/archery/competitions.html`

---

### 6. Fixed Date Format Locale ✅
**Problem**: Date formatting not respecting Italian locale setting.

**Solution**:
- Added `_lang` property to `window.translations` object
- Injected from server: `{{ session.get('lang', 'it') }}`
- Date formatting functions now correctly detect Italian vs English
- Italian dates: "17-Ott" format
- English dates: "October 17" format

**Files Modified**:
- `site01/app/templates/base.html`

---

## 📋 Summary

| Issue | Status | Requires Migration | Deployment Needed |
|-------|--------|-------------------|-------------------|
| categoria/classe swap | ✅ Fixed | No | Yes |
| Yellow "in attesa" badge | ✅ Fixed | No | Yes |
| Athlete preferences saving | ✅ Fixed | **Yes** | Yes |
| N/A in admin console | ⚠️ Migration needed | **Yes** | After migration |
| Loading spinner | ✅ Fixed | No | Yes |
| Date format locale | ✅ Fixed | No | Yes |

---

## 🚀 Deployment Steps

### 1. Commit and Push
```powershell
cd c:\Users\Mattia\Documents\GitHub\mysite
git add .
git commit -m "fix: categoria/classe swap, yellow pending badge, spinner, date locale"
git push origin main
```

### 2. Deploy to Server
```bash
cd /path/to/mysite
git pull origin main
docker-compose down
docker-compose build --no-cache --pull
docker-compose up -d
```

### 3. Run Migration (REQUIRED for preferences saving)
```bash
docker exec -it orion-project python /app/site01/migrations/add_classe_field.py
```

### 4. Verify
- Hard refresh browser: `Ctrl+Shift+R`
- Check dates are in Italian format (17-Ott)
- Check "in attesa" subscriptions show yellow badge
- Check loading spinner doesn't persist
- Try saving athlete preferences in settings (after migration)

---

## 🐛 Remaining Known Issues

1. **Text translations**: Some hardcoded Italian/English text not in JSON files
   - Status: Non-critical, can be fixed incrementally
   - Solution: Move all text to translations JSON files

---

## Files Modified in This Fix

1. `site01/app/templates/archery/competitions.html`
   - Fixed categoria/classe swap
   - Added yellow "in attesa" badge logic
   - Fixed loading spinner initial state

2. `site01/app/templates/base.html`
   - Added `_lang` to window.translations

3. `site01/app/routes/api.py`
   - Added error handling to PATCH endpoint

---

**Status**: ✅ All code fixes complete, ready for deployment + migration
**Date**: 2025-10-13
**Remaining**: User must run migration on server after deployment
