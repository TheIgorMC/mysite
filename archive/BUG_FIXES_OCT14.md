# Bug Fixes - October 14, 2025

## 🐛 Issues Fixed

### 1. ✅ Inviti API Call Fixed
**Problem**: API call was missing query parameters
**File**: `site01/app/templates/archery/competitions.html`
**Change**:
```javascript
// BEFORE
const resp = await fetch(`/archery/api/inviti`);

// AFTER  
const resp = await fetch(`/archery/api/inviti?only_open=false&only_youth=false`);
```
**Impact**: Now fetches ALL invites (not just open or youth-only)

---

### 2. ✅ Admin "Add Athletes" Display Fixed
**Problem**: Showed "Suggested class: MM/SM" (age category) instead of bow type
**File**: `site01/app/templates/admin/manage_athletes.html`
**Change**:
```javascript
// BEFORE
<p class="text-sm text-gray-600">Suggested class: ${athlete.classe || 'N/A'}</p>

// AFTER
<p class="text-sm text-gray-600">Bow type: ${athlete.classe || 'N/A'}</p>
```
**Impact**: Correctly shows "Bow type: CO/OL/AN" instead of confusing age category

**Note**: The `classe` field in ARC_atleti table contains bow type (CO/OL/AN), not age category

---

### 3. ✅ Admin Back Button
**Status**: Already exists!
**Location**: Line 10-13 of `site01/app/templates/admin/manage_athletes.html`
```html
<a href="{{ url_for('main.admin_dashboard') }}" 
   class="inline-flex items-center text-primary hover:text-primary-dark mb-4 transition">
    <i class="fas fa-arrow-left mr-2"></i>Back to Admin Dashboard
</a>
```
**No changes needed** - back button was already present

---

### 4. 🔍 Spinner Debug Logging Added
**Problem**: Spinner never disappears (still investigating)
**Files**: `site01/app/templates/archery/competitions.html`
**Changes**: Added extensive logging to trace execution:

```javascript
// loadInviti()
console.log('loadInviti: Starting...');
console.log('loadInviti: Fetch complete, status:', resp.status);
console.log('loadInviti: Got', inviti.length, 'invites');
console.log('loadInviti: Complete');

// loadTurniForAll()
console.log('loadTurniForAll: Starting for', allCompetitions.length, 'competitions');
console.log('loadTurniForAll: Complete, loaded turns for', Object.keys(allTurni).length, 'competitions');

// showLoading()
console.log('showLoading called with:', show);
console.log('Spinner shown');
console.log('Spinner hidden');
```

**How to diagnose**:
1. Open browser DevTools (F12)
2. Go to Console tab
3. Reload competitions page
4. Watch console logs
5. Identify where execution hangs

**Expected log sequence**:
```
Loading initial data...
showLoading called with: true
Spinner shown
Loaded athletes: X
Loaded competitions: X
loadInviti: Starting...
loadInviti: Fetch complete, status: 200
loadInviti: Got X invites
loadInviti: Complete
loadTurniForAll: Starting for X competitions
loadTurniForAll: Complete, loaded turns for X competitions
Loaded inviti and turni
Loaded subscriptions
Filtering competitions...
Filter complete
Hiding spinner
showLoading called with: false
Spinner hidden
```

**If spinner hangs**: Look for which log statement is missing - that's where the issue is

---

## 📊 Summary

| Issue | Status | Impact |
|-------|--------|--------|
| Inviti API call | ✅ Fixed | Loads all invites correctly |
| Admin display | ✅ Fixed | Shows bow type not age |
| Back button | ✅ Already exists | No change needed |
| Spinner debug | 🔍 Investigating | Logging added for diagnosis |

---

## 🧪 Testing Instructions

### Test 1: Inviti Loading
1. Open competitions page
2. Check browser console
3. Look for: `loadInviti: Got X invites`
4. Verify X > 0 (should have invites)

### Test 2: Admin Display
1. Go to Admin → Manage Athletes
2. Select a user
3. Search for an athlete
4. Verify label says "Bow type: CO" (or OL/AN)
5. Should NOT say "Suggested class: SM/MM"

### Test 3: Back Button
1. Go to Admin → Manage Athletes
2. Look for back arrow at top left
3. Click it
4. Should return to Admin Dashboard

### Test 4: Spinner Diagnosis
1. Open competitions page with DevTools open
2. Watch console logs
3. Identify where execution stops
4. Report back which log line is last

---

## 🔮 Next Steps

### If spinner still hangs:
1. Check if `/archery/api/inviti` endpoint works:
   ```bash
   curl http://localhost/archery/api/inviti?only_open=false&only_youth=false
   ```

2. Check if endpoint is properly proxied in Flask:
   - File: `site01/app/routes/archery.py`
   - Should have route for `/api/inviti`

3. Possible causes:
   - Endpoint doesn't exist → returns 404 → fetch hangs
   - CORS issue → fetch blocked
   - Response is not JSON → JSON parsing fails
   - Timeout → fetch waits indefinitely

4. Temporary fix (if needed):
   - Add timeout to fetch:
   ```javascript
   const controller = new AbortController();
   const timeoutId = setTimeout(() => controller.abort(), 5000);
   const resp = await fetch(url, { signal: controller.signal });
   clearTimeout(timeoutId);
   ```

---

**Status**: 3/4 fixed, 1 under investigation
**Date**: October 14, 2025
**Files Modified**:
- `site01/app/templates/archery/competitions.html` (inviti API + debug logging)
- `site01/app/templates/admin/manage_athletes.html` (bow type label)
