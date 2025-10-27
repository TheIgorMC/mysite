# Latest Bug Fixes - October 13, 2025

## ✅ All 5 Issues Fixed

### 1. Fixed SyntaxError in Settings Dropdown ✅
**Problem**: `Uncaught SyntaxError: Failed to execute 'setValueAndClosePopup'` when changing class dropdown.

**Root Cause**: Escaped quotes in querySelector within inline onclick attribute.

**Solution**:
- Added ID `class-${athlete.id}` to competition class dropdown
- Changed from `document.querySelector('[onchange*=\"cat-${athlete.id}\"]')` 
- To clean: `document.getElementById('class-${athlete.id}')`

**Files Modified**:
- `site01/app/templates/auth/settings.html`

---

### 2. Competition Filtering with Open Invites ✅
**Problem**: 
- Competitions without invites not showing
- Need to filter by ARC_inviti (open subscription windows)
- Should show region 06 (Veneto) only
- Show "iscrizioni chiuse" for closed/started competitions

**Solution**:
- Added `loadTurniForAll()` function to load turns for ALL competitions at startup
- Stores turn data in `allTurni` object keyed by codice_gara
- Updated filter logic:
  - **Upcoming**: Shows region 06 competitions that haven't ended yet
  - **Open**: Shows region 06 competitions with published invites (have turns) and haven't started
  - **Past**: Shows ended competitions
  - **My**: Shows user's subscriptions
- Added red "Iscrizioni chiuse" note for competitions that started or have no invite
- Disabled subscribe button for closed competitions (red button)

**Logic**:
```javascript
// Competition is "open" if:
1. Has turns (invite published)
2. Start date is in the future
3. Region 06 (Veneto)

// Competition shows "iscrizioni chiuse" if:
1. No turns (no invite) OR
2. Already started
```

**Files Modified**:
- `site01/app/templates/archery/competitions.html`

---

### 3. Fixed Spinner Visibility ✅
**Problem**: Spinner not showing at all during loading.

**Root Cause**: Previous fix added `hidden` class to initial state, preventing spinner from ever showing.

**Solution**:
- Removed `hidden` class from loading div initial state
- Spinner now shows on page load
- `showLoading(false)` in `finally` block ensures it hides after load completes

**Files Modified**:
- `site01/app/templates/archery/competitions.html`

---

### 4. N/A in Admin Console (Migration Required) ⚠️
**Problem**: Admin console shows "N/A" for classe field.

**Root Cause**: Database column `classe` doesn't exist in `authorized_athletes` table yet.

**Solution**: Migration file already exists, **USER MUST RUN IT**:

```bash
# On the server:
docker exec -it orion-project python /app/site01/migrations/add_classe_field.py
```

This will:
- Add `classe` column to `authorized_athletes` table
- Set default value 'CO' for existing records
- Enable saving bow type preferences

**Status**: Code ready, migration pending user action.

---

### 5. Turn Time Display Cleaned Up ✅
**Problem**: Turn dropdown showing times like "Domenica - Qualifica - 08:45:00" (with seconds).

**Solution**:
- Format time by removing seconds: `ora_ritrovo.substring(0, 5)`
- Now displays: "Domenica - Qualifica - 08:45"

**Files Modified**:
- `site01/app/templates/archery/competitions.html`

---

## 📋 Summary

| Issue | Status | User Action Required |
|-------|--------|---------------------|
| SyntaxError in settings | ✅ Fixed | No |
| Competition filtering | ✅ Fixed | No |
| Spinner visibility | ✅ Fixed | No |
| N/A in admin | ⚠️ Needs migration | **YES - Run migration** |
| Turn time format | ✅ Fixed | No |

---

## 🚀 Deployment Instructions

### 1. Commit Changes
```powershell
cd c:\Users\Mattia\Documents\GitHub\mysite
git add .
git commit -m "fix: settings dropdown, competition filtering, spinner, turn display"
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

### 3. **CRITICAL**: Run Migration for Admin Console
```bash
docker exec -it orion-project python /app/site01/migrations/add_classe_field.py
```

This migration **MUST** be run to:
- Fix N/A in admin console
- Enable athlete preference saving
- Allow classe field to be displayed/edited

### 4. Verify
- Hard refresh browser: `Ctrl+Shift+R`
- **Competitions page**:
  - Spinner shows during load
  - "Upcoming" tab shows region 06 competitions not ended
  - "Open" tab shows only competitions with published invites
  - Closed competitions show red "Iscrizioni chiuse" note
  - Turn times show as "08:45" (no seconds)
- **Settings page**:
  - Change class dropdown - no errors
  - Changes save successfully (after migration)
- **Admin console**:
  - Classe field shows values (not N/A) after migration

---

## 🔍 Technical Details

### Competition Filtering Logic

**Before**: Only checked dates, ignored invite status
**After**: 
1. Loads ALL competition turns at startup
2. Filters by:
   - Region 06 (societa_codice starts with '06')
   - Invite status (has turns = invite published)
   - Date status (not ended, not started, etc.)

### Turn Loading
```javascript
async function loadTurniForAll() {
    for (const comp of allCompetitions) {
        const turns = await fetch(`/archery/api/turni?codice_gara=${comp.codice}`);
        allTurni[comp.codice] = turns || [];
    }
}
```

### Filter Examples
```javascript
// "Open" tab: Has invite AND future
filtered = competitions.filter(c => {
    const startDate = new Date(c.data_inizio);
    const hasTurns = allTurni[c.codice]?.length > 0;
    return startDate > now && hasTurns;
});

// "Upcoming" tab: Not ended yet (may not have invite)
filtered = competitions.filter(c => {
    const endDate = new Date(c.data_fine);
    return endDate >= now;
});
```

---

## 📝 Files Modified

1. **site01/app/templates/archery/competitions.html** (4 fixes)
   - Added loadTurniForAll() function
   - Updated filter logic for open/upcoming
   - Added "iscrizioni chiuse" red note
   - Fixed spinner initial state
   - Formatted turn times (removed seconds)

2. **site01/app/templates/auth/settings.html** (1 fix)
   - Fixed SyntaxError with proper ID usage

---

## ⚠️ Post-Deployment Checklist

- [ ] Code deployed to server
- [ ] **Migration run** (REQUIRED for admin console)
- [ ] Browser hard refreshed
- [ ] Competitions show correctly by tab
- [ ] "Iscrizioni chiuse" appears on appropriate competitions
- [ ] Settings dropdowns work without errors
- [ ] Spinner shows during page load
- [ ] Turn times display without seconds
- [ ] Admin console shows classe values (not N/A)

---

**Status**: ✅ All code complete, migration pending
**Date**: 2025-10-13
**Next Step**: **RUN MIGRATION ON SERVER**
