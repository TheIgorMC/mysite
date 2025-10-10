# ✅ Implementation Complete: Authorized Athletes & Competitions Integration

## 🎯 What Was Implemented

### 1. **Database Migration** (`migrations/add_authorized_athletes.py`)
- Created `authorized_athletes` table in **website-level database**
- Stores user→athlete authorizations
- Fields: `tessera_atleta`, `nome_atleta`, `cognome_atleta`, `data_nascita`, `categoria`
- Admin tracking: `added_by`, `added_at`
- Indexed on `user_id` and `tessera_atleta`

**Run migration:**
```powershell
cd site01
python migrations/add_authorized_athletes.py
```

### 2. **Updated Models** (`app/models.py`)
- Added `AuthorizedAthlete` model with relationships
- Properties: `nome_completo`, `display_name` (tessera - full name)
- Unique constraint: one user can't have duplicate athletes
- Relationship: `User.authorized_athletes`

### 3. **Website-Level API Routes** (`app/routes/api.py`)
Created 4 new endpoints:

#### For Users:
- **GET `/api/user/authorized-athletes`** - Get current user's authorized athletes
  - Returns list with `tessera`, `nome`, `cognome`, `display`, `categoria`

#### For Admins:
- **GET `/admin/api/authorized-athletes`** - View all user assignments
- **POST `/admin/api/authorized-athletes`** - Assign athletes to a user
  - Body: `{user_id, athletes: [{tessera, nome, cognome, categoria, data_nascita}]}`
- **DELETE `/admin/api/authorized-athletes/<id>`** - Remove athlete from user

### 4. **Competitions Page Integration** (`app/templates/archery/competitions.html`)
Updated to work with **FastAPI backend**:

#### Configuration:
```javascript
const ARCHERY_API_BASE = 'http://localhost:80/api';  // Update with your FastAPI URL
```

#### Data Flow:
1. **Load authorized athletes** from website (`/api/user/authorized-athletes`)
2. **Load competitions** from FastAPI (`/api/gare?future=true`)
3. **Load user subscriptions** from FastAPI (`/api/iscrizioni?tessera_atleta=...`)
4. **Filter by region** Tuscany (societa_codice starts with '06')

#### Features:
- ✅ Multi-athlete subscription (dropdown if multiple athletes)
- ✅ Auto-select if only one athlete
- ✅ Warning if no authorized athletes
- ✅ Turn selection from FastAPI (`/api/turni`)
- ✅ Submission to FastAPI (`POST /api/iscrizioni`)
- ✅ Real-time status updates

#### Subscription Modal:
- Athlete selection (from authorized list)
- Turn selection (loaded from API)
- Notes field
- Submits to FastAPI with proper structure

### 5. **Translations Updated**
Added keys to both `en.json` and `it.json`:
- `select_athlete` - "Select Athlete" / "Seleziona Atleta"
- `ongoing` - "Ongoing" / "In Corso"
- `closed` - "Closed" / "Chiusa"

---

## 🔧 Configuration Required

### 1. Update FastAPI URL
In `competitions.html`, line ~192:
```javascript
const ARCHERY_API_BASE = 'http://localhost:80/api';  // Change to your FastAPI URL
```

If FastAPI runs on different port or domain:
```javascript
const ARCHERY_API_BASE = 'http://api.orionproject.com/api';  // Production
const ARCHERY_API_BASE = 'http://localhost:8000/api';  // Dev
```

### 2. Run Database Migration
```powershell
cd site01
python migrations/add_authorized_athletes.py
```

To rollback:
```powershell
python migrations/add_authorized_athletes.py downgrade
```

### 3. Admin Panel (To Be Implemented)
You'll need to create an admin UI to assign athletes to users. For now, you can add directly to database:

```sql
INSERT INTO authorized_athletes (user_id, tessera_atleta, nome_atleta, cognome_atleta, categoria, added_by)
VALUES (1, 'ABC123', 'Mario', 'Rossi', 'SM', 1);
```

---

## 📊 API Integration with FastAPI

### Endpoints Used:

#### From Your FastAPI Backend:
1. **GET `/api/gare?future=true&limit=100`** - Load competitions
   - Response: Array of gare objects with `codice`, `nome`, `tipo`, `societa_codice`, `data_inizio`, `data_fine`

2. **GET `/api/turni?codice_gara=<codice>`** - Load turns for a competition
   - Response: Array of turn objects with `turno`, `giorno`, `fase`, `ora_ritrovo`, `ora_inizio_tiri`

3. **GET `/api/iscrizioni?tessera_atleta=<tessera>`** - Load athlete's subscriptions
   - Response: Array of subscription objects

4. **POST `/api/iscrizioni`** - Create new subscription
   - Body: `{codice_gara, tessera_atleta, categoria, turno, stato, note}`
   - Response: `{id, status: "created"}`

#### From Website (Flask):
1. **GET `/api/user/authorized-athletes`** - Get current user's athletes
2. Admin endpoints (for future admin panel)

---

## 🎨 How It Works for Users

### User Experience:

1. **User logs in** to website
2. **Admin assigns** athlete card numbers to user account (e.g., parent gets child's tessera, coach gets team members)
3. **User visits Competitions page**
   - Sees upcoming Tuscany competitions (region 06)
   - Can filter: Upcoming, Open, Past, My Subscriptions
4. **User clicks "Subscribe"**
   - Modal opens
   - If multiple athletes: dropdown shows "ABC123 - Mario Rossi", "ABC124 - Luigi Verdi"
   - If single athlete: auto-selected, name shown
   - If no athletes: warning message "Contact admin to add athletes"
5. **User selects turn** (loaded from FastAPI)
6. **User clicks "Confirm"**
   - POST to FastAPI `/api/iscrizioni`
   - Success notification
   - Competition card shows "Subscribed"

---

## 🔐 Security Model

### Authorization Hierarchy:
1. **Admin** → Can assign any athlete to any user
2. **User** → Can only subscribe athletes assigned to them
3. **Athletes in Database** → Must exist in FastAPI's ARC_atleti table

### Validation:
- Website checks: Is user authorized for this tessera?
- FastAPI validates: Does tessera exist? Is competition real? Is turn valid?

---

## 📝 Next Steps (Recommended)

### Immediate:
1. **Run the migration** to create `authorized_athletes` table
2. **Update FastAPI URL** in competitions.html
3. **Test with one user** - manually add athlete authorization in database

### Short-term:
1. **Create admin panel UI** for managing athlete assignments
   - Page: `/admin/athletes`
   - Features: Search users, search athletes (from FastAPI), assign/remove
2. **Add user profile page** showing "My Athletes" (read-only)
3. **Test end-to-end** subscription flow

### Optional Enhancements:
1. **Add ARC_inviti integration** for proper subscription status (open/closing soon/closed)
2. **Email notifications** when subscribed
3. **Subscription management** (cancel, edit turn)
4. **Admin view** of all subscriptions for a competition

---

## 🐛 Troubleshooting

### Issue: "No authorized athletes" message
**Solution:** Admin needs to add athletes to user's account via database or (future) admin panel

### Issue: Competitions not loading
**Solution:** Check ARCHERY_API_BASE URL is correct and FastAPI is running

### Issue: Turns dropdown empty
**Solution:** Check `/api/turni` endpoint returns data for the competition

### Issue: Subscription fails
**Solution:** 
- Check tessera exists in ARC_atleti
- Check codice_gara exists in ARC_gare
- Check turn number exists in ARC_turni

---

## 📚 Files Modified

1. `site01/migrations/add_authorized_athletes.py` ✅ NEW
2. `site01/app/models.py` ✅ UPDATED (AuthorizedAthlete model)
3. `site01/app/routes/api.py` ✅ NEW (website API endpoints)
4. `site01/app/__init__.py` ✅ UPDATED (register api blueprint)
5. `site01/app/templates/archery/competitions.html` ✅ UPDATED (FastAPI integration)
6. `site01/translations/en.json` ✅ UPDATED (new keys)
7. `site01/translations/it.json` ✅ UPDATED (new keys)
8. `site01/docs/COMPETITION_API_SPEC.md` ✅ UPDATED (architecture doc)

---

## ✨ Benefits of This Architecture

1. **Centralized** - Athletes managed in one place for all services
2. **Reusable** - Same authorization system can be used for shop orders, events, etc.
3. **Secure** - Admin-controlled, users can't self-assign
4. **Flexible** - Easy to extend (add roles, permissions, etc.)
5. **Clean** - Website handles authorization, FastAPI handles data
6. **Scalable** - Can add multiple athletes, multiple users, without changes

---

**You're all set!** Run the migration and test it out. Let me know if you need help with the admin panel implementation or have any questions! 🚀
