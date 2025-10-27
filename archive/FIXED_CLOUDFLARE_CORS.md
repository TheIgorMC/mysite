# Fixed: Cloudflare Access CORS Errors

## Problem
The competitions page was making **direct browser calls** to the FastAPI backend (`api.orion-project.it`), which is protected by Cloudflare Access. This caused:
- CORS errors (No 'Access-Control-Allow-Origin' header)
- Redirects to Cloudflare Access login page
- Failed API requests

## Root Cause
Browser-based JavaScript cannot send Cloudflare Access authentication headers (`CF-Access-Client-Id` and `CF-Access-Client-Secret`) directly because:
1. These are sensitive credentials that should never be exposed in frontend code
2. Cloudflare Access redirects unauthenticated requests to a login page
3. CORS policy blocks cross-origin requests without proper headers

## Solution: Flask Proxy Pattern
All API calls now go through **Flask proxy endpoints** that:
1. Run on the server-side (not in the browser)
2. Add Cloudflare Access authentication headers
3. Forward requests to FastAPI backend
4. Return responses to the browser

### Architecture
```
Browser ────> Flask Proxy ────> FastAPI (Cloudflare Access)
        (same origin)      (authenticated)
```

## Changes Made

### 1. Updated OrionAPIClient (`app/api/__init__.py`)
Added new methods to support competition subscriptions:
```python
def get_competitions(self, future=False, limit=100)
def get_turns(self, codice_gara)
def get_subscriptions(self, tessera_atleta)
def create_subscription(self, codice_gara, tessera_atleta, categoria, turno, stato, note)
```

### 2. Added Flask Proxy Endpoints (`app/routes/archery.py`)
```python
@bp.route('/api/gare')                    # GET competitions
@bp.route('/api/turni')                   # GET turns for a competition
@bp.route('/api/iscrizioni', methods=['GET', 'POST'])  # GET/POST subscriptions
```

### 3. Updated Frontend (`app/templates/archery/competitions.html`)
**Before (Direct API calls):**
```javascript
const ARCHERY_API_BASE = 'https://api.orion-project.it/api';
fetch(`${ARCHERY_API_BASE}/gare?future=true&limit=100`)
```

**After (Flask proxy calls):**
```javascript
// No hardcoded API URL needed
fetch(`/archery/api/gare?future=true&limit=100`)
fetch(`/archery/api/turni?codice_gara=${codice}`)
fetch(`/archery/api/iscrizioni`, { method: 'POST', ... })
```

## Updated Endpoints

### Get Competitions (Gare)
**Frontend:**
```javascript
GET /archery/api/gare?future=true&limit=100
```
**Flask proxy forwards to:**
```
GET https://api.orion-project.it/api/gare?future=true&limit=100
Headers: CF-Access-Client-Id, CF-Access-Client-Secret
```

### Get Turns (Turni)
**Frontend:**
```javascript
GET /archery/api/turni?codice_gara=GARA001
```
**Flask proxy forwards to:**
```
GET https://api.orion-project.it/api/turni?codice_gara=GARA001
Headers: CF-Access-Client-Id, CF-Access-Client-Secret
```

### Get Subscriptions (Iscrizioni)
**Frontend:**
```javascript
GET /archery/api/iscrizioni?tessera_atleta=93229
```
**Flask proxy forwards to:**
```
GET https://api.orion-project.it/api/iscrizioni?tessera_atleta=93229
Headers: CF-Access-Client-Id, CF-Access-Client-Secret
```

### Create Subscription
**Frontend:**
```javascript
POST /archery/api/iscrizioni
{
  "codice_gara": "GARA001",
  "tessera_atleta": "93229",
  "classe": "CO",
  "categoria": "SM",
  "turno": 1,
  "stato": "confermato",
  "note": "Optional notes"
}
```
**Flask proxy forwards to:**
```
POST https://api.orion-project.it/api/iscrizioni
Headers: CF-Access-Client-Id, CF-Access-Client-Secret
Body: (same as frontend)
```

## Benefits

1. ✅ **Security**: Cloudflare Access credentials never exposed to browser
2. ✅ **No CORS issues**: All requests are same-origin (Flask → Browser)
3. ✅ **Centralized auth**: Authentication logic in one place (`OrionAPIClient`)
4. ✅ **Easy to maintain**: Update API auth in one file, not scattered across frontend
5. ✅ **Error handling**: Server-side can log and handle API errors better

## Testing

### Before (Error):
```
Failed to load resource: net::ERR_FAILED
CORS policy: No 'Access-Control-Allow-Origin' header
Redirected to Cloudflare Access login page
```

### After (Success):
```
✅ Competitions load successfully
✅ Turns load for selected competition
✅ Subscriptions submit successfully
✅ No CORS errors
✅ No Cloudflare redirects
```

## Files Changed

1. ✅ `app/api/__init__.py` - Added methods to OrionAPIClient
2. ✅ `app/routes/archery.py` - Added Flask proxy endpoints
3. ✅ `app/templates/archery/competitions.html` - Updated all fetch() calls

## Pattern for Future API Endpoints

When adding new API endpoints, follow this pattern:

### 1. Add method to OrionAPIClient
```python
def get_something(self, param):
    return self._make_request('GET', '/api/something', params={'param': param})
```

### 2. Add Flask proxy endpoint
```python
@bp.route('/api/something')
def get_something():
    param = request.args.get('param')
    client = OrionAPIClient()
    result = client.get_something(param)
    return jsonify(result if result else [])
```

### 3. Update frontend to use proxy
```javascript
// ✅ Use Flask proxy
fetch('/archery/api/something?param=value')

// ❌ Never call FastAPI directly from browser
fetch('https://api.orion-project.it/api/something')  // CORS ERROR!
```

## Summary

All API calls now properly go through Flask proxy endpoints, which handle Cloudflare Access authentication server-side. This eliminates CORS errors and keeps credentials secure. The competitions page will now load and function correctly! 🎯
