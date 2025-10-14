# UI/UX Fixes - October 14, 2025 (Part 2)

## 🐛 Issues Fixed

### 1. ✅ Spinner Not Hiding Visually
**Problem**: Console said "Spinner hidden" but spinner still visible on screen

**Root Cause**: Mixing Tailwind's `hidden` class with inline `display` styles caused conflicts. Tailwind's `hidden` uses `!important` which can't be overridden by inline styles.

**Solution**: 
- Removed all inline `style.display` manipulations
- Only use Tailwind's `hidden` class for show/hide
- Added `hidden` class to loading div by default in HTML
- Simplified showLoading() function

**Files Changed**: `site01/app/templates/archery/competitions.html`

```javascript
// BEFORE (conflicting)
if (show) {
    loading.classList.remove('hidden');
    loading.style.display = 'flex';  // ← Inline style conflicts with Tailwind
} else {
    loading.classList.add('hidden');
    loading.style.display = 'none';  // ← Inline style conflicts with Tailwind
}

// AFTER (clean)
if (show) {
    loading.classList.remove('hidden');
    grid.classList.add('hidden');
} else {
    loading.classList.add('hidden');
    grid.classList.remove('hidden');  // Show grid when done
}
```

---

### 2. ✅ Removed Past Tab
**Problem**: Past competitions tab shouldn't exist

**Solution**: Removed the "Past" tab button from navbar

**Files Changed**: `site01/app/templates/archery/competitions.html`

**Tabs Before**:
- Upcoming
- Open Subscriptions
- Past ← REMOVED
- My Subscriptions

**Tabs After**:
- Upcoming
- Open Subscriptions
- My Subscriptions

Also removed the `case 'past':` from filterCompetitions() switch statement.

---

### 3. ✅ Fixed "Open" Tab Filtering
**Problem**: "Open" tab was filtering by "has turns" instead of actual subscription window dates

**Solution**: Changed logic to filter by invitation date ranges

**Files Changed**: `site01/app/templates/archery/competitions.html`

```javascript
// BEFORE (wrong logic)
case 'open':
    filtered = allCompetitions.filter(c => {
        const hasTurns = allTurni[c.codice] && allTurni[c.codice].length > 0;
        return startDate > now && hasTurns;  // ❌ Having turns ≠ open subscriptions
    });
    break;

// AFTER (correct logic)
case 'open':
    // Competitions with OPEN subscription windows
    filtered = allCompetitions.filter(c => {
        const invito = allInviti[c.codice];
        if (!invito) return false;  // No invite = not open
        
        const aperturaDate = new Date(invito.data_apertura_iscrizioni);
        const chiusuraDate = new Date(invito.data_chiusura_iscrizioni);
        const startDate = new Date(c.data_inizio);
        
        // ✅ Open if: today is between apertura and chiusura, and competition hasn't started
        return now >= aperturaDate && now <= chiusuraDate && startDate > now;
    });
    break;
```

**Impact**: "Open" tab now shows only competitions where subscriptions are actually open TODAY

---

### 4. ✅ Increased Competition Limit
**Problem**: Too few competitions shown (limit was 100)

**Solution**: Increased limit from 100 to 500

**Files Changed**: `site01/app/templates/archery/competitions.html`

```javascript
// BEFORE
const gareResp = await fetch(`/archery/api/gare?future=true&limit=100`);

// AFTER
const gareResp = await fetch(`/archery/api/gare?future=true&limit=500`);
```

**Note**: Still filters by `future=true` (only future/ongoing competitions) and `societa_codice.startsWith('06')` (Veneto region)

---

## 📊 Tab Filtering Logic Summary

### "Upcoming" Tab
Shows all future competitions that haven't ended yet (Veneto region only):
```javascript
endDate >= today
```

### "Open Subscriptions" Tab
Shows only competitions with currently open subscription windows:
```javascript
invito exists AND
data_apertura_iscrizioni <= today <= data_chiusura_iscrizioni AND
data_inizio > today
```

### "My Subscriptions" Tab
Shows competitions where user has active subscriptions:
```javascript
userSubscriptions.has(codice_gara)
```

---

## 🎯 Expected Behavior

### Spinner
- ✅ Shows when page loads
- ✅ Hides after all data loaded
- ✅ Grid appears after spinner hides

### Tabs
- ✅ Only 3 tabs (Upcoming, Open, My Subscriptions)
- ✅ "Open" shows competitions with active subscription windows
- ✅ No past competitions shown anywhere

### Competition Count
- ✅ Can show up to 500 competitions
- ✅ Filtered by Veneto region (06)
- ✅ Filtered by future/ongoing only

---

## 🧪 Testing Checklist

- [ ] Spinner disappears after loading
- [ ] Grid shows after spinner hides
- [ ] Only 3 tabs visible (no "Past" tab)
- [ ] "Upcoming" shows all future Veneto competitions
- [ ] "Open" shows only competitions with open subscription windows
- [ ] "My Subscriptions" shows user's subscriptions
- [ ] More than 100 competitions visible (if they exist in DB)
- [ ] No console errors

---

## 📝 Files Modified
1. `site01/app/templates/archery/competitions.html`
   - Fixed spinner hiding logic
   - Removed Past tab
   - Fixed Open tab filtering
   - Increased limit to 500

---

**Status**: All 4 issues fixed ✅
**Ready for**: Testing and deployment
