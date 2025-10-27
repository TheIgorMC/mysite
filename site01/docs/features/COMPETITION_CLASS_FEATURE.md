# Competition Class and Age Category Feature

## Overview
Added support for competition class selection (CO, OL, AN) and age category selection (GM, GF, RM, RF, etc.) in the athlete management and competition subscription system.

## Changes Made

### 1. Database Changes

#### authorized_athletes table
- Added `classe` field (VARCHAR(10)) to store competition class
- Values: CO (Compound), OL (Olympic/Recurve), AN (Barebow/Arco Nudo)

#### Field Clarification
- `classe` = Competition class (bow type): CO, OL, AN
- `categoria` = Age category: GM, GF, RM, RF, AM, AF, JM, JF, SM, SF, MM, MF
  - G = Giovanissimi, R = Ragazzi, A = Allievi, J = Juniores, S = Seniores, M = Master
  - M = Maschile (Male), F = Femminile (Female)

### 2. Migration Scripts

#### migrations/add_authorized_athletes.py
- Updated to include `classe` field in table creation

#### migrations/add_classe_field.py (NEW)
- Adds `classe` column to existing tables
- Sets default value 'CO' for existing records
- Includes safety checks

**To run:**
```bash
# In Docker container
docker exec -it orion-project python /app/site01/migrations/add_classe_field.py

# Or locally
python migrations/add_classe_field.py
```

### 3. Model Updates

#### app/models.py - AuthorizedAthlete
```python
categoria = db.Column(db.String(10))  # Age category: GM, GF, RM, RF, etc.
classe = db.Column(db.String(10))     # Competition class: CO, OL, AN
```

### 4. API Updates

#### app/routes/api.py
- `POST /admin/api/authorized-athletes`: Now accepts `classe` field
- `GET /api/user/authorized-athletes`: Returns `classe` field
- `GET /admin/api/authorized-athletes`: Returns `classe` field

### 5. Admin Panel Updates

#### app/templates/admin/manage_athletes.html

**New Features:**
- Class selection modal appears when adding an athlete
- Options: CO (Compound), OL (Olympic), AN (Barebow)
- Pre-filled with suggestion from API data
- User can override before adding

**Modal Flow:**
1. User searches for athlete
2. Clicks athlete from results
3. Modal appears asking for competition class
4. User selects class and confirms
5. Athlete is added with selected class

**JavaScript Changes:**
- `showClassModal()` - Shows class selection modal
- `closeClassModal()` - Closes modal
- `confirmAddAthlete()` - Confirms and adds athlete with selected class
- `addAthleteToUser()` - Updated to use `classe` instead of `categoria`

### 6. Competition Subscription Updates

#### app/templates/archery/competitions.html

**New Age Category Selector:**
- Added dropdown with all age categories
- Options include:
  - GM/GF - Giovanissimi Maschile/Femminile
  - RM/RF - Ragazzi Maschile/Femminile
  - AM/AF - Allievi Maschile/Femminile
  - JM/JF - Juniores Maschile/Femminile
  - SM/SF - Seniores Maschile/Femminile
  - MM/MF - Master Maschile/Femminile

**Submission Updates:**
- Now requires age category selection (mandatory)
- Sends both `classe` (from athlete's profile) and `categoria` (age category) to API
- FastAPI endpoint receives:
  ```json
  {
    "classe": "CO",      // Competition class from athlete profile
    "categoria": "SM",   // Age category selected in form
    "turno": 1,
    "stato": "confermato"
  }
  ```

### 7. Translation Updates

#### translations/en.json
```json
"age_category": "Age Category",
"select_age_category": "Select age category...",
"age_category_info": "Select the appropriate age and gender category"
```

#### translations/it.json
```json
"age_category": "Categoria di Età",
"select_age_category": "Seleziona categoria di età...",
"age_category_info": "Seleziona la categoria appropriata per età e genere"
```

## Usage Guide

### For Admins: Adding Athletes

1. Go to Admin Panel > Manage Athletes
2. Select a user from the left panel
3. Search for an athlete by name
4. Click the athlete from search results
5. **NEW:** Modal appears asking for competition class
6. Select the appropriate class (CO/OL/AN)
7. Click "Add Athlete"

### For Users: Subscribing to Competitions

1. Go to Competitions page
2. Click "Subscribe" on a competition
3. Select athlete from dropdown
4. **NEW:** Select age category (GM, GF, RM, etc.)
5. Select turn
6. Add optional notes
7. Click "Confirm Subscription"

The system will automatically use:
- Competition class (CO/OL/AN) from the athlete's profile
- Age category (GM/GF/RM/etc.) from the form selection

## Database Schema

```sql
CREATE TABLE authorized_athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tessera_atleta VARCHAR(10) NOT NULL,
    nome_atleta VARCHAR(100) NOT NULL,
    cognome_atleta VARCHAR(100) NOT NULL,
    data_nascita DATE,
    categoria VARCHAR(10),  -- Age category: GM, GF, RM, RF, etc.
    classe VARCHAR(10),     -- Competition class: CO, OL, AN
    added_by INTEGER,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE(user_id, tessera_atleta)
);
```

## API Examples

### Add Athlete with Class
```bash
POST /admin/api/authorized-athletes
{
  "user_id": 1,
  "athletes": [{
    "tessera": "93229",
    "nome": "John",
    "cognome": "Doe",
    "classe": "OL"  // Competition class
  }]
}
```

### Get Athletes
```bash
GET /api/user/authorized-athletes

Response:
{
  "authorized_athletes": [
    {
      "id": 1,
      "tessera": "93229",
      "nome_completo": "John Doe",
      "classe": "OL",
      "categoria": null
    }
  ]
}
```

### Subscribe to Competition
```bash
POST /api/iscrizioni
{
  "codice_gara": "GARA001",
  "tessera_atleta": "93229",
  "classe": "OL",      // From athlete profile
  "categoria": "SM",   // Selected in form
  "turno": 1,
  "stato": "confermato",
  "note": "Optional notes"
}
```

## Testing Checklist

- [ ] Run migration to add `classe` column
- [ ] Add athlete via admin panel - verify class modal appears
- [ ] Verify athlete is saved with selected class
- [ ] View athlete list - verify class is displayed
- [ ] Subscribe to competition - verify age category is required
- [ ] Submit subscription - verify both classe and categoria are sent
- [ ] Check API response includes classe field
- [ ] Test in both English and Italian

## Notes

- Competition class (CO/OL/AN) is set once when adding athlete
- Age category (GM/GF/RM/etc.) is selected for each subscription
- Both fields are sent to FastAPI backend for subscription
- Default class is 'CO' (Compound) if not specified
- Age category is mandatory for subscriptions
