# Fix: Added Missing /api/inviti Endpoint

## 🐛 Problem
```
GET https://orion-project.it/archery/api/inviti?only_open=false&only_youth=false 404 (Not Found)
```

The `/archery/api/inviti` endpoint was missing from the Flask routes, even though the FastAPI backend has it.

---

## ✅ Solution

Added the missing endpoint and API client method to proxy requests to FastAPI.

### Files Modified

#### 1. `site01/app/routes/archery.py`
Added new route after `/api/turni`:

```python
@bp.route('/api/inviti')
def get_inviti():
    """Proxy endpoint for fetching invitations (inviti) from FastAPI"""
    codice = request.args.get('codice')
    only_open = request.args.get('only_open', 'false').lower() == 'true'
    only_youth = request.args.get('only_youth', 'false').lower() == 'true'
    
    client = OrionAPIClient()
    
    try:
        # Fetch from FastAPI
        inviti = client.get_inviti(codice=codice, only_open=only_open, only_youth=only_youth)
        return jsonify(inviti if inviti else [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

#### 2. `site01/app/api/__init__.py`
Added method to `OrionAPIClient` class:

```python
def get_inviti(self, codice=None, only_open=False, only_youth=False):
    """Get invitations (inviti) from FastAPI"""
    params = {}
    if codice:
        params['codice'] = codice
    if only_open:
        params['only_open'] = 'true'
    if only_youth:
        params['only_youth'] = 'true'
    return self._make_request('GET', '/api/inviti', params=params)
```

---

## 🔄 Request Flow

```
Browser
  ↓
  GET /archery/api/inviti?only_open=false&only_youth=false
  ↓
Flask (archery.py route)
  ↓
OrionAPIClient.get_inviti()
  ↓
  GET https://api.orion-project.it/api/inviti?only_open=false&only_youth=false
  Headers: CF-Access-Client-Id, CF-Access-Client-Secret
  ↓
FastAPI Backend
  ↓
MariaDB/MySQL (orion_db.ARC_inviti)
  ↓
Response: JSON array of invitations
```

---

## 📊 Endpoint Details

**Flask Route**: `/archery/api/inviti`
**FastAPI Endpoint**: `/api/inviti`
**Method**: GET
**Parameters**:
- `codice` (optional) - Filter by specific competition code
- `only_open` (optional, boolean) - Show only currently open registrations
- `only_youth` (optional, boolean) - Show only youth competitions

**Response**:
```json
[
  {
    "codice": "25A001",
    "solo_giovanile": 0,
    "numero_turni": 2,
    "data_apertura_iscrizioni": "2025-10-01",
    "data_chiusura_iscrizioni": "2025-10-25"
  }
]
```

---

## 🧪 Testing

### Test 1: Get All Invites
```bash
curl http://localhost/archery/api/inviti?only_open=false&only_youth=false
```

### Test 2: Get Specific Invite
```bash
curl http://localhost/archery/api/inviti?codice=25A001
```

### Test 3: Get Only Open Invites
```bash
curl http://localhost/archery/api/inviti?only_open=true
```

### Test 4: Frontend
1. Open competitions page
2. Open DevTools Console
3. Should see:
   ```
   loadInviti: Starting...
   loadInviti: Fetch complete, status: 200
   loadInviti: Got X invites
   loadInviti: Complete
   ```
4. No more 404 errors!

---

## ✅ Status

**Before**: 404 Not Found
**After**: Working endpoint that proxies to FastAPI

This should fix the spinner issue since the inviti request will now complete successfully!

---

**Files Changed**:
1. `site01/app/routes/archery.py` - Added `/api/inviti` route
2. `site01/app/api/__init__.py` - Added `get_inviti()` method

**Commit Message**:
```
fix: add missing /api/inviti endpoint to Flask routes

- Added /archery/api/inviti route to proxy requests to FastAPI
- Added OrionAPIClient.get_inviti() method
- Fixes 404 error when loading competition invitations
- Required for competition status badge system
```
