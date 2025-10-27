# 🚀 Quick Start Guide - Competition System

## Step 1: Run Database Migration

```powershell
cd site01
python migrations/add_authorized_athletes.py
```

Expected output:
```
Creating authorized_athletes table...
✅ Table authorized_athletes created successfully!
✅ Indexes created successfully!
```

---

## Step 2: Configure FastAPI URL

Edit `site01/app/templates/archery/competitions.html` line ~192:

```javascript
const ARCHERY_API_BASE = 'http://localhost:80/api';  // Your FastAPI URL
```

---

## Step 3: Test with Admin User

### 3.1 Add Test Athlete Authorization
Connect to SQLite database:
```powershell
cd site01
sqlite3 instance/site.db
```

Add athlete to your user (replace user_id with your admin user ID):
```sql
INSERT INTO authorized_athletes (user_id, tessera_atleta, nome_atleta, cognome_atleta, categoria, added_by)
VALUES (1, 'TEST001', 'Test', 'Athlete', 'SM', 1);

-- Check it was added
SELECT * FROM authorized_athletes;

-- Exit SQLite
.quit
```

### 3.2 Start Flask App
```powershell
cd site01
python run.py
```

### 3.3 Visit Competitions Page
1. Go to `http://localhost:5000/archery/competitions`
2. You should see:
   - Competitions loading from FastAPI
   - Only region 06 (Tuscany) competitions
   - "Subscribe" buttons enabled
3. Click "Subscribe" → should see:
   - Athlete dropdown with "TEST001 - Test Athlete"
   - Turn dropdown (loaded from FastAPI)
   - Notes field

### 3.4 Test Subscription
1. Select athlete
2. Select turn
3. Click "Confirm"
4. Should see success notification
5. Competition card should show "Subscribed"

---

## Step 4: Check What Happened

### Check Flask Website
```powershell
sqlite3 instance/site.db
SELECT * FROM authorized_athletes;
.quit
```

### Check FastAPI Database
Should have new record in `ARC_iscrizioni` table with:
- `codice_gara` - competition code
- `tessera_atleta` - 'TEST001'
- `categoria` - 'SM'
- `turno` - selected turn
- `stato` - 'confermato'

---

## 🎯 What's Next?

### For Production Use:
1. **Add real athletes** to your account (admin does this)
2. **Update FastAPI URL** if different from localhost
3. **Test with multiple athletes** (add more to database)

### For Complete System:
1. **Build admin panel** to manage athlete assignments
   - UI to search users
   - UI to search athletes from FastAPI
   - Assign/remove buttons
2. **Add user profile page** showing "My Athletes"
3. **Add email notifications** on subscription

---

## 📞 Troubleshooting

| Problem | Solution |
|---------|----------|
| Migration fails | Check you're in `site01` directory |
| No competitions show | Check FastAPI is running at configured URL |
| Can't subscribe | Check athlete exists in `authorized_athletes` table |
| Empty turns dropdown | Check `/api/turni?codice_gara=XXX` returns data |
| 404 on /api/user/authorized-athletes | Restart Flask app (new routes) |

---

## 🧪 Quick Test Commands

```powershell
# Test authorized athletes API
curl http://localhost:5000/api/user/authorized-athletes

# Test FastAPI competitions
curl http://localhost:80/api/gare?future=true&limit=5

# Test FastAPI turns
curl http://localhost:80/api/turni?codice_gara=25A001

# Test FastAPI iscrizioni (replace tessera)
curl http://localhost:80/api/iscrizioni?tessera_atleta=TEST001
```

---

**All set!** You have a working multi-athlete competition subscription system! 🎉
