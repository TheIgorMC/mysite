# Competition Filtering Logic - Current Implementation

## 🤔 I Need Your Help Understanding the Requirements!

### Current Implementation (What I Did):

#### Data Loading:
```javascript
1. Load competitions: GET /api/gare?future=true&limit=100
   → Returns all future competitions

2. For EACH competition:
   Load turns: GET /api/turni?codice_gara={code}
   → If turns exist = invite is published
   → If no turns = no invite yet

3. Filter by region 06 (societa_codice starts with '06')
```

#### Tab Filtering:
```javascript
"Upcoming" tab:
- Shows: Region 06 competitions that haven't ENDED yet
- Includes: Both with and without published invites
- Logic: endDate >= today

"Open" tab:
- Shows: Region 06 competitions with published invites (have turns) that haven't STARTED
- Logic: hasturns && startDate > today

"Past" tab:
- Shows: Competitions that have ended
- Logic: endDate < today

"My" tab:
- Shows: User's subscriptions
```

#### Subscribe Button Logic:
```javascript
IF competition already started OR no turns (no invite):
  → Show "Chiuso" (red button, disabled)
  → Show red note "Iscrizioni chiuse"
  
ELSE IF has turns and not started:
  → Show "Subscribe" button (enabled)
  
ELSE IF no turns and not started:
  → Show "Express Interest" mode (yellow banner)
```

---

## ❓ Questions I Have:

### 1. About ARC_inviti Table:
**What does ARC_inviti contain?**

Option A: Just a list of which competitions have invites published?
```
ARC_inviti:
- codice_gara
- published: true/false
```

Option B: Date ranges for when subscriptions are open?
```
ARC_inviti:
- codice_gara
- data_apertura_iscrizioni (e.g., "2025-10-01")
- data_chiusura_iscrizioni (e.g., "2025-10-25")
```

Option C: Something else? Please describe!

**Is there an API endpoint for inviti?**
- I checked APIspec.md and didn't find `/api/inviti`
- Should I add one?
- Or should I infer from turni?

---

### 2. About "Open Subscriptions" Tab:
**What should this tab show?**

Option A: Competitions where subscription window is currently open
```javascript
// Today is between apertura and chiusura dates
const today = new Date();
const aperturaDate = new Date(invito.data_apertura);
const chiusuraDate = new Date(invito.data_chiusura);
return today >= aperturaDate && today <= chiusuraDate;
```

Option B: Competitions that just have an invite published (any future competition with turns)
```javascript
return hasTurns && !hasEnded;
```

Option C: Competitions with invite published and not yet started
```javascript
return hasTurns && startDate > today;
```

---

### 3. About "Upcoming" Tab:
**What should this show?**

Option A: ALL region 06 competitions that haven't ended (with OR without invite)
```javascript
// My current implementation
return endDate >= today && region06;
```

Option B: Only region 06 competitions WITH published invite
```javascript
return hasTurns && endDate >= today && region06;
```

Option C: Only region 06 competitions with OPEN subscription window
```javascript
return isSubscriptionOpen && region06;
```

---

### 4. About Competitions WITHOUT Invite:
**How should these be handled?**

Option A: Show in "Upcoming" with "Express Interest" button
```javascript
// Current: Show yellow banner, allow interest registration
// Button says "Express Interest" instead of "Subscribe"
```

Option B: Don't show at all until invite is published
```javascript
// Hide from all lists until turns are loaded
```

Option C: Show in a separate section/tab
```javascript
// Add "Coming Soon" or "No Invite Yet" tab
```

---

### 5. About "Iscrizioni Chiuse" (Closed Subscriptions):
**When should we show this red note?**

Option A: When competition has started (regardless of invite)
```javascript
// My current implementation
if (startDate <= today) {
    showRedNote("Iscrizioni chiuse");
}
```

Option B: When subscription window has closed (chiusura date passed)
```javascript
if (today > chiusuraDate) {
    showRedNote("Iscrizioni chiuse");
}
```

Option C: Both of the above
```javascript
if (today > chiusuraDate || competitionStarted) {
    showRedNote("Iscrizioni chiuse");
}
```

---

## 🐛 Current Problems:

### 1. Spinner Not Disappearing:
**Cause**: Loading 100+ turns sequentially takes too long
**Solutions**:
- Option A: Load turns in parallel (Promise.all)
- Option B: Don't load all turns upfront, load on-demand
- Option C: Add inviti endpoint to API

### 2. May Be Showing Wrong Competitions:
**Cause**: I'm guessing the logic without understanding ARC_inviti structure
**Solution**: You tell me the correct logic!

---

## 📝 Example Scenario:

Let's say we have these competitions:

```
Competition A:
- codice: "25A001"
- data_inizio: 2025-11-15 (1 month away)
- data_fine: 2025-11-17
- societa_codice: 0601 (Veneto)
- Has turns: YES
- ARC_inviti: ???

Competition B:
- codice: "25A002"  
- data_inizio: 2025-12-01 (2 months away)
- data_fine: 2025-12-03
- societa_codice: 0602 (Veneto)
- Has turns: NO
- ARC_inviti: ???

Competition C:
- codice: "25A003"
- data_inizio: 2025-10-10 (3 days ago - STARTED)
- data_fine: 2025-10-12 (yesterday - ENDED)
- societa_codice: 0603 (Veneto)
- Has turns: YES
- ARC_inviti: ???
```

**Please tell me:**
1. Which competitions should show in "Upcoming" tab?
2. Which should show in "Open" tab?
3. Which should show in "Past" tab?
4. Which should have subscribe button enabled?
5. Which should show "Iscrizioni chiuse"?
6. Which should show "Express Interest"?

---

## 🚀 Once You Clarify:

I will:
1. Update the filtering logic correctly
2. Fix the spinner issue (parallel loading or on-demand)
3. Add proper subscription window checking
4. Show correct buttons and notes

**Please explain the ARC_inviti structure and your requirements!**
