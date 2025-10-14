# 🧪 Competition Status Testing Guide

## Quick Test Scenarios

### Test Data Examples
Current date for testing: **October 14, 2025**

---

## Scenario 1: Iscrizioni Aperte (Green) 🟢

**Setup:**
```sql
-- Competition: Indoor Championship
ARC_gare: 
  codice: "25A001"
  data_inizio: "2025-11-15"
  data_fine: "2025-11-17"
  societa_codice: "0601"

ARC_inviti:
  codice: "25A001"
  data_apertura_iscrizioni: "2025-10-01"
  data_chiusura_iscrizioni: "2025-11-10"
```

**Expected Result:**
- ✅ Badge: "Iscrizioni aperte" (Green)
- ✅ Button: "Subscribe" (enabled, blue)
- ✅ Reason: Today (Oct 14) is BETWEEN Oct 1 and Nov 10, competition starts Nov 15

---

## Scenario 2: In Arrivo (Blue) 🔵

**Setup:**
```sql
ARC_gare:
  codice: "25A002"
  data_inizio: "2025-12-01"
  societa_codice: "0602"

ARC_inviti:
  codice: "25A002"
  data_apertura_iscrizioni: "2025-11-01"  ← Future opening
  data_chiusura_iscrizioni: "2025-11-25"
```

**Expected Result:**
- ✅ Badge: "In arrivo" (Blue)
- ✅ Button: "Subscribe" (enabled, blue)
- ✅ Reason: Subscriptions open Nov 1 (future), competition starts Dec 1

---

## Scenario 3: Iscrizioni Chiuse - Competition Started (Red) 🔴

**Setup:**
```sql
ARC_gare:
  codice: "25A003"
  data_inizio: "2025-10-12"  ← Already started
  data_fine: "2025-10-14"
  societa_codice: "0603"

ARC_inviti:
  codice: "25A003"
  data_apertura_iscrizioni: "2025-09-01"
  data_chiusura_iscrizioni: "2025-10-11"
```

**Expected Result:**
- ✅ Badge: "Iscrizioni chiuse" (Red)
- ✅ Button: "Chiuso" (disabled, red)
- ✅ Reason: Competition started Oct 12 (past)

---

## Scenario 4: Iscrizioni Chiuse - Window Closed (Red) 🔴

**Setup:**
```sql
ARC_gare:
  codice: "25A004"
  data_inizio: "2025-10-20"  ← Future
  societa_codice: "0604"

ARC_inviti:
  codice: "25A004"
  data_apertura_iscrizioni: "2025-09-15"
  data_chiusura_iscrizioni: "2025-10-10"  ← Closed Oct 10
```

**Expected Result:**
- ✅ Badge: "Iscrizioni chiuse" (Red)
- ✅ Button: "Chiuso" (disabled, red)
- ✅ Reason: Subscription window closed Oct 10 (past), even though competition is future

---

## Scenario 5: Attesa Invito (White) ⚪

**Setup:**
```sql
ARC_gare:
  codice: "25A005"
  data_inizio: "2025-11-20"
  societa_codice: "0605"

ARC_inviti:
  -- NO ENTRY for this competition!
```

**Expected Result:**
- ✅ Badge: "Attesa invito" (Gray/White)
- ✅ Button: "Mi interessa" (yellow)
- ✅ Reason: No invite published yet

**After clicking "Mi interessa":**
- ✅ Modal opens with yellow info box
- ✅ Submits with turno: 0
- ✅ Button changes to darker yellow with checkmark
- ✅ Button disabled
- ✅ localStorage contains competition code

---

## Subscription Status Testing

### Test 1: Richiesta Effettuata (Gray/White) ⚪

**Setup:**
```sql
ARC_iscrizioni:
  id: 1
  codice_gara: "25A001"
  tessera_atleta: "012345"
  stato: "pending"  ← or any value except confermato/in attesa/cancellato
```

**Expected:**
- ✅ Status box: Gray background
- ✅ Icon: Paper plane
- ✅ Text: "Richiesta effettuata"
- ✅ Subscribe button: Disabled

---

### Test 2: Iscritto (Green) 🟢

**Setup:**
```sql
ARC_iscrizioni:
  stato: "confermato"
```

**Expected:**
- ✅ Status box: Green background
- ✅ Icon: Check circle
- ✅ Text: "Iscritto"
- ✅ Subscribe button: Disabled
- ✅ Delete button: Visible

---

### Test 3: In Attesa (Yellow) 🟡

**Setup:**
```sql
ARC_iscrizioni:
  stato: "in attesa"
```

**Expected:**
- ✅ Status box: Yellow background
- ✅ Icon: Clock
- ✅ Text: "In attesa"
- ✅ Subscribe button: Disabled
- ✅ Delete button: Visible

---

### Test 4: Cancellato (Red → Allow Resubscribe) 🔴

**Setup:**
```sql
ARC_iscrizioni:
  stato: "cancellato"
```

**Expected:**
- ✅ Status box: HIDDEN (removed from display)
- ✅ Subscribe button: ENABLED
- ✅ Button text: "Subscribe"
- ✅ Delete button: HIDDEN
- ✅ User can resubscribe

---

## Browser Testing

### Chrome/Edge
```bash
# Open DevTools (F12)
# Console tab:
localStorage.getItem('archery_expressed_interest')
# Should show array of competition codes after expressing interest
```

### Firefox
```bash
# Storage tab → Local Storage → your-domain
# Check: archery_expressed_interest key
```

### Safari
```bash
# Develop → Show Web Inspector → Storage → Local Storage
```

---

## API Endpoint Testing

### 1. Check Inviti Endpoint
```bash
curl http://localhost/archery/api/inviti
# Should return array of invitations with dates
```

### 2. Check Gare Endpoint
```bash
curl http://localhost/archery/api/gare?future=true&limit=10
# Should return future competitions
```

### 3. Submit Express Interest
```bash
curl -X POST http://localhost/archery/api/iscrizioni \
  -H "Content-Type: application/json" \
  -d '{
    "codice_gara": "25A005",
    "tessera_atleta": "012345",
    "categoria": "CO",
    "classe": "SM",
    "turno": 0,
    "stato": "in attesa",
    "note": "Interesse espresso (invito non pubblicato)."
  }'
```

---

## Edge Cases to Test

### Edge Case 1: Competition Starts Today
```
data_inizio: "2025-10-14" (today)
Expected: Red "Iscrizioni chiuse" (startDate <= now)
```

### Edge Case 2: Subscription Closes Today
```
data_chiusura_iscrizioni: "2025-10-14" (today)
Expected: Green "Iscrizioni aperte" (today <= chiusura)
```

### Edge Case 3: Multiple Subscriptions Same Competition
```
User has 2 athletes subscribed to same competition
Expected: Show first subscription status
```

### Edge Case 4: No Region 06 Filter
```
societa_codice: "0501" (different region)
Expected: NOT shown in any tab
```

### Edge Case 5: Express Interest Already Submitted
```
localStorage has competition code
Expected: Yellow button with checkmark, disabled
```

---

## Visual Regression Checklist

- [ ] Desktop (1920x1080): 3 columns
- [ ] Tablet (768px): 2 columns
- [ ] Mobile (375px): 1 column
- [ ] Dark mode: All colors visible
- [ ] Light mode: All colors visible
- [ ] Badge text: Readable on all backgrounds
- [ ] Status box: Proper padding and alignment
- [ ] Buttons: Correct icon alignment
- [ ] Modal: Proper centering

---

## Performance Benchmarks

### Before Optimization
- Load 100 competitions: ~10-15 seconds
- Spinner: Appears stuck

### After Optimization
- Load 100 competitions: ~2-3 seconds
- Spinner: Disappears promptly

**Test:**
```javascript
// In browser console
console.time('load');
// Reload page
// Wait for spinner to disappear
console.timeEnd('load');
// Should be < 3000ms
```

---

## Accessibility Testing

- [ ] Keyboard navigation: Tab through buttons
- [ ] Screen reader: Reads badge text correctly
- [ ] High contrast mode: Colors still distinguishable
- [ ] Focus indicators: Visible on all interactive elements
- [ ] ARIA labels: Present on icon-only buttons

---

## Cross-Browser Compatibility

| Browser | Version | Status | Notes |
|---------|---------|--------|-------|
| Chrome | 118+ | ✅ | Primary |
| Firefox | 119+ | ✅ | Test localStorage |
| Safari | 17+ | ✅ | Date parsing |
| Edge | 118+ | ✅ | Same as Chrome |
| Mobile Safari | iOS 17+ | ✅ | Touch events |
| Mobile Chrome | Android 13+ | ✅ | LocalStorage |

---

## Debug Commands

### Check Loaded Data
```javascript
// In browser console
console.log('Competitions:', allCompetitions.length);
console.log('Inviti:', Object.keys(allInviti).length);
console.log('Turni:', Object.keys(allTurni).length);
console.log('Subscriptions:', userSubscriptions.size);
console.log('Expressed Interest:', expressedInterest);
```

### Manually Test Status Function
```javascript
const comp = allCompetitions[0];
const status = getCompetitionStatus(comp);
console.log('Status:', status);
```

### Clear Express Interest
```javascript
localStorage.removeItem('archery_expressed_interest');
location.reload();
```

---

## Sign-Off Checklist

Before deploying to production:

- [ ] All 5 competition status scenarios tested
- [ ] All 4 subscription status scenarios tested
- [ ] Express interest feature works
- [ ] localStorage persists across sessions
- [ ] Translations show correctly (IT/EN)
- [ ] No console errors
- [ ] Page loads in <3 seconds
- [ ] Mobile responsive
- [ ] Dark mode works
- [ ] Delete subscription works
- [ ] Resubscribe after cancellation works
- [ ] Region 06 filter works
- [ ] API endpoints responding correctly

---

**Testing Date**: _______________
**Tester**: _______________
**Sign-Off**: _______________
