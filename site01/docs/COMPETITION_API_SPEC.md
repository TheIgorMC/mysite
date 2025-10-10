# Competition Management API Specification

## 📋 Database Structure

### Tables Used:

1. **ARC_gare** - Competition main information
2. **ARC_inviti** - Invitation/subscription settings
3. **ARC_turni** - Competition turns/shifts
4. **ARC_iscrizioni** - User subscriptions
5. **users** - User accounts and authorized athletes

---

## 🔗 API Endpoints

### 1. GET `/archery/api/competitions`

**Purpose:** Get all competitions in region 06 (Tuscany) with subscription status

**Query Parameters:**
- `region` (optional, default='06') - Filter by societa_codice prefix
- `status` (optional) - Filter by status: 'upcoming', 'open', 'past', 'my'

**Response Structure:**

```json
{
  "competitions": [
    {
      "codice": "TOS2025001",
      "nome": "Campionato Indoor 2025",
      "tipo": "Indoor",
      "societa_codice": "06-CAR-001",
      "data_inizio": "2025-11-15",
      "data_fine": "2025-11-15",
      "invito": true,
      
      // From ARC_inviti (if exists)
      "invito_details": {
        "solo_giovanile": false,
        "numero_turni": 2,
        "data_apertura_iscrizioni": "2025-10-15",
        "data_chiusura_iscrizioni": "2025-11-10"
      },
      
      // Subscription status
      "subscription_status": "open",  // "not_open", "open", "closing_soon", "closed", "past"
      "days_until_deadline": 5,
      
      // User's subscription (if any)
      "user_subscribed": true,
      "user_subscription": {
        "id": 123,
        "tessera_atleta": "ABC123",
        "categoria": "SM",
        "turno": 1,
        "stato": "confermato",
        "note": "Note here"
      },
      
      // Available turns
      "turni": [
        {
          "id": 1,
          "turno": 1,
          "giorno": "Sabato",
          "fase": "Qualificazione",
          "ora_ritrovo": "08:30:00",
          "ora_inizio_tiri": "09:00:00"
        },
        {
          "id": 2,
          "turno": 2,
          "giorno": "Sabato",
          "fase": "Qualificazione",
          "ora_ritrovo": "13:30:00",
          "ora_inizio_tiri": "14:00:00"
        }
      ]
    }
  ],
  
  // Current user's authorized athletes
  "authorized_athletes": [
    {
      "tessera": "ABC123",
      "nome": "Mario Rossi",
      "display": "ABC123 - Mario Rossi",
      "categoria": "SM"
    },
    {
      "tessera": "ABC124",
      "nome": "Luigi Verdi",
      "display": "ABC124 - Luigi Verdi",
      "categoria": "SM"
    }
  ],
  
  // User's subscriptions across all competitions
  "user_subscriptions": [
    {
      "id": 123,
      "codice_gara": "TOS2025001",
      "tessera_atleta": "ABC123",
      "categoria": "SM",
      "turno": 1,
      "stato": "confermato",
      "note": ""
    }
  ]
}
```

**Subscription Status Logic:**
- `not_open`: No invito record OR before data_apertura_iscrizioni
- `open`: Current date between apertura and chiusura, > 3 days to deadline
- `closing_soon`: Current date between apertura and chiusura, <= 3 days to deadline
- `closed`: Current date > data_chiusura_iscrizioni AND date < data_inizio
- `past`: Current date > data_fine

**Status Indicators:**
- 🟢 Green dot: `open` (invito present, subscriptions open, >3 days)
- 🟡 Yellow triangle: `closing_soon` (invito present, subscriptions open, <=3 days)
- 🔴 Red dot: `closed` (subscriptions closed but competition not started)
- ⚫ Gray: `past` (competition finished)
- ⚪ White/empty: `not_open` (no invito or not yet open)

---

### 2. POST `/archery/api/competitions/<codice_gara>/subscribe`

**Purpose:** Subscribe an athlete to a competition

**Request Body:**

```json
{
  "tessera_atleta": "ABC123",  // Athlete card number (from authorized list)
  "categoria": "SM",            // Category
  "turno": 1,                   // Turn number
  "note": "Optional notes"      // Optional notes
}
```

**Validation:**
1. Check user is authenticated
2. Check user is authorized to subscribe this athlete (tessera in user's authorized list)
3. Check competition has invito
4. Check current date is between data_apertura and data_chiusura
5. Check athlete not already subscribed to this competition
6. Check turn exists for this competition

**Response:**

```json
{
  "success": true,
  "subscription_id": 123,
  "message": "Successfully subscribed ABC123 - Mario Rossi to Campionato Indoor 2025"
}
```

**Error Response:**

```json
{
  "success": false,
  "error": "not_authorized",  // or "already_subscribed", "closed", "no_invito", "invalid_turn"
  "message": "You are not authorized to subscribe this athlete"
}
```

---

### 3. DELETE `/archery/api/competitions/<codice_gara>/subscribe/<subscription_id>`

**Purpose:** Cancel a subscription

**Authorization:** User must own the subscription (their authorized athlete)

**Response:**

```json
{
  "success": true,
  "message": "Subscription cancelled"
}
```

---

### 4. GET `/archery/api/competitions/<codice_gara>`

**Purpose:** Get detailed information about a specific competition

**Response:**

```json
{
  "codice": "TOS2025001",
  "nome": "Campionato Indoor 2025",
  "tipo": "Indoor",
  "societa_codice": "06-CAR-001",
  "data_inizio": "2025-11-15",
  "data_fine": "2025-11-15",
  "invito": true,
  
  "invito_details": {
    "solo_giovanile": false,
    "numero_turni": 2,
    "data_apertura_iscrizioni": "2025-10-15",
    "data_chiusura_iscrizioni": "2025-11-10"
  },
  
  "turni": [
    // Full turn details...
  ],
  
  "subscriptions": [
    // All subscriptions (for admin view)
    {
      "id": 123,
      "tessera_atleta": "ABC123",
      "nome_atleta": "Mario Rossi",
      "categoria": "SM",
      "turno": 1,
      "stato": "confermato",
      "note": ""
    }
  ]
}
```

---

### 5. GET `/api/user/authorized-athletes`

**Purpose:** Get authorized athletes for current user (website-level)

**Authentication:** Required (current user)

**Response:**

```json
{
  "authorized_athletes": [
    {
      "id": 1,
      "tessera": "ABC123",
      "nome": "Mario",
      "cognome": "Rossi",
      "nome_completo": "Mario Rossi",
      "display": "ABC123 - Mario Rossi",
      "categoria": "SM",
      "data_nascita": "1990-01-15"
    },
    {
      "id": 2,
      "tessera": "ABC124",
      "nome": "Luigi",
      "cognome": "Verdi",
      "nome_completo": "Luigi Verdi",
      "display": "ABC124 - Luigi Verdi",
      "categoria": "SM",
      "data_nascita": "1992-03-20"
    }
  ]
}
```

---

### 6. GET `/admin/authorized-athletes`

**Purpose:** Admin panel - view all user→athlete assignments

**Authentication:** Admin only

**Response:**

```json
{
  "assignments": [
    {
      "user_id": 5,
      "username": "mario.rossi",
      "email": "mario@example.com",
      "athletes": [
        {
          "id": 1,
          "tessera": "ABC123",
          "nome_completo": "Mario Rossi",
          "added_at": "2025-01-15T10:30:00"
        }
      ]
    }
  ]
}
```

---

### 7. POST `/admin/authorized-athletes`

**Purpose:** Assign athlete(s) to a user (admin only)

**Authentication:** Admin only

**Request Body:**

```json
{
  "user_id": 5,
  "athletes": [
    {
      "tessera": "ABC123",
      "nome": "Mario",
      "cognome": "Rossi",
      "data_nascita": "1990-01-15",
      "categoria": "SM"
    }
  ]
}
```

**Response:**

```json
{
  "success": true,
  "added": 1,
  "message": "Added 1 athlete(s) to user mario.rossi"
}
```

---

### 8. DELETE `/admin/authorized-athletes/<athlete_assignment_id>`

**Purpose:** Remove athlete assignment from a user (admin only)

**Authentication:** Admin only

**Response:**

```json
{
  "success": true,
  "message": "Athlete removed from user"
}
```

---

## 🗄️ Database Changes Needed

### 1. New Table: `authorized_athletes` (Website-Level)

**Location:** Main website database (SQLite for dev, can be in main DB)

This is a **website-level feature** - users can manage athletes across all sections:

```sql
CREATE TABLE authorized_athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tessera_atleta VARCHAR(10) NOT NULL,
    nome_atleta VARCHAR(255) NOT NULL,
    cognome_atleta VARCHAR(255) NOT NULL,
    data_nascita DATE,
    categoria VARCHAR(10),
    added_by INTEGER,  -- Admin who authorized
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (user_id, tessera_atleta),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_authorized_athletes_user ON authorized_athletes(user_id);
CREATE INDEX idx_authorized_athletes_tessera ON authorized_athletes(tessera_atleta);
```

**Purpose:** 
- Allow users to manage multiple athletes (e.g., parents managing children, coaches managing team)
- Centralized authorization system usable across all website sections
- Admin-controlled: only admins can assign athletes to users

---

## 📊 Implementation Example (Python/Flask)

### Backend Route: `/archery/api/competitions`

```python
@bp.route('/api/competitions')
@login_required
def get_competitions():
    """Get competitions with subscription status"""
    region = request.args.get('region', '06')
    status_filter = request.args.get('status')
    
    # Get current date
    today = date.today()
    closing_soon_threshold = 3  # days
    
    # Query competitions
    query = """
        SELECT 
            g.*,
            i.solo_giovanile,
            i.numero_turni,
            i.data_apertura_iscrizioni,
            i.data_chiusura_iscrizioni
        FROM ARC_gare g
        LEFT JOIN ARC_inviti i ON g.codice = i.codice
        WHERE g.societa_codice LIKE :region
        AND g.data_fine >= :today
        ORDER BY g.data_inizio ASC
    """
    
    competitions = db.execute(query, {
        'region': f'{region}%',
        'today': today
    }).fetchall()
    
    # Get user's authorized athletes (from website-level table)
    authorized_athletes = db.execute("""
        SELECT tessera_atleta, nome_atleta, cognome_atleta, categoria
        FROM authorized_athletes
        WHERE user_id = :user_id
    """, {'user_id': current_user.id}).fetchall()
    
    # Get user's subscriptions
    user_tessere = [a['tessera_atleta'] for a in authorized_athletes]
    user_subscriptions = []
    if user_tessere:
        placeholders = ','.join(['?' for _ in user_tessere])
        user_subscriptions = db.execute(f"""
            SELECT *
            FROM ARC_iscrizioni
            WHERE tessera_atleta IN ({placeholders})
        """, user_tessere).fetchall()
    
    # Process competitions
    result_competitions = []
    for comp in competitions:
        # Get turns
        turns = db.execute("""
            SELECT *
            FROM ARC_turni
            WHERE codice_gara = :codice
            ORDER BY turno ASC
        """, {'codice': comp['codice']}).fetchall()
        
        # Determine subscription status
        subscription_status = 'not_open'
        days_until_deadline = None
        
        if comp['data_apertura_iscrizioni'] and comp['data_chiusura_iscrizioni']:
            apertura = comp['data_apertura_iscrizioni']
            chiusura = comp['data_chiusura_iscrizioni']
            
            if today < apertura:
                subscription_status = 'not_open'
            elif today > chiusura:
                if today < comp['data_inizio']:
                    subscription_status = 'closed'
                else:
                    subscription_status = 'past'
            else:
                days_until_deadline = (chiusura - today).days
                if days_until_deadline <= closing_soon_threshold:
                    subscription_status = 'closing_soon'
                else:
                    subscription_status = 'open'
        elif today >= comp['data_inizio']:
            subscription_status = 'past'
        
        # Check if user is subscribed
        user_subscription = next(
            (s for s in user_subscriptions if s['codice_gara'] == comp['codice']),
            None
        )
        
        result_competitions.append({
            'codice': comp['codice'],
            'nome': comp['nome'],
            'tipo': comp['tipo'],
            'societa_codice': comp['societa_codice'],
            'data_inizio': comp['data_inizio'].isoformat(),
            'data_fine': comp['data_fine'].isoformat(),
            'invito': bool(comp['invito']),
            'invito_details': {
                'solo_giovanile': bool(comp['solo_giovanile']),
                'numero_turni': comp['numero_turni'],
                'data_apertura_iscrizioni': comp['data_apertura_iscrizioni'].isoformat() if comp['data_apertura_iscrizioni'] else None,
                'data_chiusura_iscrizioni': comp['data_chiusura_iscrizioni'].isoformat() if comp['data_chiusura_iscrizioni'] else None
            } if comp['data_apertura_iscrizioni'] else None,
            'subscription_status': subscription_status,
            'days_until_deadline': days_until_deadline,
            'user_subscribed': bool(user_subscription),
            'user_subscription': dict(user_subscription) if user_subscription else None,
            'turni': [dict(t) for t in turns]
        })
    
    return jsonify({
        'competitions': result_competitions,
        'authorized_athletes': [
            {
                'tessera': a['tessera_atleta'],
                'nome': a['nome_atleta'],
                'cognome': a['cognome_atleta'],
                'nome_completo': f"{a['nome_atleta']} {a['cognome_atleta']}",
                'display': f"{a['tessera_atleta']} - {a['nome_atleta']} {a['cognome_atleta']}",
                'categoria': a['categoria']
            }
            for a in authorized_athletes
        ],
        'user_subscriptions': [dict(s) for s in user_subscriptions]
    })
```

### Backend Route: Subscribe

```python
@bp.route('/api/competitions/<codice_gara>/subscribe', methods=['POST'])
@login_required
def subscribe_to_competition(codice_gara):
    """Subscribe an athlete to a competition"""
    data = request.get_json()
    
    tessera_atleta = data.get('tessera_atleta')
    categoria = data.get('categoria')
    turno = data.get('turno')
    note = data.get('note', '')
    
    # Validate user is authorized for this athlete (website-level check)
    authorized = db.execute("""
        SELECT * FROM authorized_athletes
        WHERE user_id = :user_id AND tessera_atleta = :tessera
    """, {
        'user_id': current_user.id,
        'tessera': tessera_atleta
    }).fetchone()
    
    if not authorized:
        return jsonify({
            'success': False,
            'error': 'not_authorized',
            'message': 'You are not authorized to subscribe this athlete'
        }), 403
    
    # Check invito exists and is open
    today = date.today()
    invito = db.execute("""
        SELECT * FROM ARC_inviti
        WHERE codice = :codice
        AND data_apertura_iscrizioni <= :today
        AND data_chiusura_iscrizioni >= :today
    """, {
        'codice': codice_gara,
        'today': today
    }).fetchone()
    
    if not invito:
        return jsonify({
            'success': False,
            'error': 'closed',
            'message': 'Subscriptions are not open for this competition'
        }), 400
    
    # Check not already subscribed
    existing = db.execute("""
        SELECT * FROM ARC_iscrizioni
        WHERE codice_gara = :codice AND tessera_atleta = :tessera
    """, {
        'codice': codice_gara,
        'tessera': tessera_atleta
    }).fetchone()
    
    if existing:
        return jsonify({
            'success': False,
            'error': 'already_subscribed',
            'message': 'This athlete is already subscribed'
        }), 400
    
    # Validate turn exists
    turn_exists = db.execute("""
        SELECT * FROM ARC_turni
        WHERE codice_gara = :codice AND turno = :turno
    """, {
        'codice': codice_gara,
        'turno': turno
    }).fetchone()
    
    if not turn_exists:
        return jsonify({
            'success': False,
            'error': 'invalid_turn',
            'message': 'Invalid turn selected'
        }), 400
    
    # Insert subscription
    result = db.execute("""
        INSERT INTO ARC_iscrizioni 
        (codice_gara, tessera_atleta, categoria, turno, stato, note)
        VALUES (:codice, :tessera, :categoria, :turno, 'in_attesa', :note)
    """, {
        'codice': codice_gara,
        'tessera': tessera_atleta,
        'categoria': categoria,
        'turno': turno,
        'note': note
    })
    
    db.commit()
    
    # Get competition name for message
    comp = db.execute("""
        SELECT nome FROM ARC_gare WHERE codice = :codice
    """, {'codice': codice_gara}).fetchone()
    
    return jsonify({
        'success': True,
        'subscription_id': result.lastrowid,
        'message': f"Successfully subscribed {tessera_atleta} - {authorized['nome_atleta']} to {comp['nome']}"
    })
```

---

## 🎨 Frontend Updates Needed

### Competition Card Status Indicators

```javascript
function getStatusIndicator(subscription_status, days_until_deadline) {
    switch(subscription_status) {
        case 'open':
            return {
                icon: '🟢',
                color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
                text: 'Open',
                badge: 'green'
            };
        case 'closing_soon':
            return {
                icon: '🟡',
                color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
                text: `Closing in ${days_until_deadline} days`,
                badge: 'yellow'
            };
        case 'closed':
            return {
                icon: '🔴',
                color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
                text: 'Closed',
                badge: 'red'
            };
        case 'past':
            return {
                icon: '⚫',
                color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300',
                text: 'Ended',
                badge: 'gray'
            };
        case 'not_open':
        default:
            return {
                icon: '⚪',
                color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300',
                text: 'Not Open Yet',
                badge: 'gray'
            };
    }
}
```

### Athlete Selection Dropdown

```html
<select id="athlete-select" class="form-select">
    <option value="">Select athlete...</option>
    <!-- Populated from authorized_athletes -->
    <option value="ABC123">ABC123 - Mario Rossi</option>
    <option value="ABC124">ABC124 - Luigi Verdi</option>
</select>
```

---

## 📝 Summary of API Changes

### What You Need to Implement:

#### Website Level (Main DB):

1. **Create `authorized_athletes` table** in main website database
2. **Add admin panel UI** in `/admin/users` to manage athlete assignments:
   - View all users and their assigned athletes
   - Add/remove athletes for each user
   - Search athletes by tessera or name
3. **Add user profile section** showing "My Athletes" (read-only for users)
4. **Implement website-level endpoints**:
   - `GET /api/user/authorized-athletes` - Get current user's athletes
   - `GET /admin/authorized-athletes` - Admin view all assignments
   - `POST /admin/authorized-athletes` - Admin assign athletes
   - `DELETE /admin/authorized-athletes/<id>` - Admin remove assignment

#### Archery API Level (MySQL):

1. **Update `/archery/api/competitions` endpoint** to:
   - Filter by region (societa_codice LIKE '06%')
   - Join with ARC_inviti to get subscription dates
   - Calculate subscription_status from dates
   - Query website's `authorized_athletes` table for current user
   - Return user_subscriptions from ARC_iscrizioni

2. **Update `/archery/api/competitions/<codice>/subscribe` endpoint** to:
   - Accept tessera_atleta parameter
   - Validate user is authorized (check website's `authorized_athletes` table)
   - Insert into ARC_iscrizioni with athlete's tessera
   - Validate turn exists in ARC_turni
   - Check dates in ARC_inviti

#### Benefits of This Architecture:

- ✅ **Centralized**: One place to manage athlete authorizations
- ✅ **Reusable**: Can use for future features (shop orders for kids, event registration)
- ✅ **Secure**: Admin-controlled assignments, users can't self-assign
- ✅ **Flexible**: Easy to extend with roles (parent, coach, manager)
- ✅ **Clean**: Archery API just checks authorization, doesn't manage it

---

This structure gives you:
- ✅ Regional filtering (Tuscany competitions)
- ✅ Status indicators (green/yellow/red dots)
- ✅ Multi-athlete subscription (with authorization)
- ✅ Proper date checking
- ✅ Clean separation of concerns

Let me know if you need any clarification or want me to generate the complete updated frontend code!
