# API Endpoint Usage Documentation

## ✅ Valid API Endpoints (from APIspec.json)

### 1. `/api/event_types` (GET)
**Purpose**: Get list of all event/competition types
**Parameters**: None
**Returns**: Array of strings (event type names)
**Usage**: Populating competition type dropdown

### 2. `/api/atleti` (GET)
**Purpose**: Search for athletes
**Parameters**:
- `q` (string, optional): Search query
- `limit` (integer, optional, default: 50): Max results
**Returns**: Array of athlete objects
**Usage**: Athlete search functionality

### 3. `/api/athlete/{tessera}/results` (GET)
**Purpose**: Get competition results for a specific athlete
**Parameters**:
- `tessera` (path, string, required): Athlete ID
- `limit` (integer, optional, default: 10): Max results
**Returns**: Array of result objects
**Usage**: Loading athlete competition history

### 4. `/api/stats` (GET)
**Purpose**: Get chart data for athlete performance over time
**Parameters**:
- `athletes` (array of strings, required): List of athlete IDs
- `event_type` (string, optional): Filter by event type
- `from_date` (date, optional): Start date
- `to_date` (date, optional): End date
- `period_months` (integer, optional): Period in months
**Returns**: Chart data object with labels and datasets
**Usage**: Generating performance graphs

### 5. `/api/best` (GET)
**Purpose**: Get best score for an athlete
**Parameters**:
- `athlete` (string, required): Athlete ID
- `event_type` (string, optional): Filter by event type
**Returns**: Best score object
**Usage**: Finding personal best scores

### 6. `/api/ranking` (GET)
**Purpose**: Get ranking for an event type
**Parameters**:
- `event_type` (string, required)
- `region` (string, optional)
- `from_date` (date, optional)
- `to_date` (date, optional)
**Returns**: Ranking data
**Usage**: Leaderboards (not yet implemented)

### 7. `/api/ranking_by_qualifica` (GET)
**Purpose**: Get ranking filtered by qualification
**Parameters**:
- `codice` (string, required): Qualification code
- `event_type` (string, required)
- `region` (string, optional)
**Returns**: Filtered ranking data
**Usage**: Championship rankings (not yet implemented)

### 8. `/api/societa` (GET)
**Purpose**: Get list of archery clubs/societies
**Parameters**: None
**Returns**: Array of society objects
**Usage**: Not currently used

### 9. `/api/qualifiche` (GET)
**Purpose**: Get list of qualifications/championships
**Parameters**: None
**Returns**: Array of qualification objects
**Usage**: Not currently used

### 10. `/api/ping` (GET)
**Purpose**: Health check endpoint
**Parameters**: None
**Returns**: Ping response
**Usage**: Testing API connectivity

---

## 🚫 Non-Existent Endpoints (DO NOT USE)

These endpoints are NOT in the API spec and should NOT be called:

- ❌ `/api/competitions` - Does not exist
- ❌ `/api/competitions/{id}` - Does not exist
- ❌ `/api/competitions/{id}/subscribe` - Does not exist
- ❌ `/api/categories` - Does not exist (we use local CSV)
- ❌ `/api/athlete/{id}` - Does not exist (use `/api/atleti?q={id}`)
- ❌ `/api/athletes/search` - Does not exist (use `/api/atleti?q={query}`)

---

## 📊 Data Sources

### From API (Authoritative)
1. **Event Types**: `/api/event_types`
   - Complete list of competition types
   - Used to populate dropdowns

2. **Athlete Search**: `/api/atleti`
   - Athlete database search
   - Returns tessera (ID), nome (name), classe, societa_codice

3. **Competition Results**: `/api/athlete/{tessera}/results`
   - Individual competition results
   - Returns detailed result objects

4. **Chart Data**: `/api/stats`
   - Performance over time
   - Returns Chart.js compatible format

### From Local CSV (`competition_arrows.csv`)
1. **Categories**: Indoor, FITA, H&F, 3D, Targa, 900R, Pinocchio, Altro
   - Grouping of competition types
   - Not provided by API

2. **Arrow Counts**: Number of arrows per competition type
   - Used for average calculations
   - Not provided by API

3. **Max Scores**: Maximum possible score
   - Used for normalization
   - Not provided by API

4. **Event Type Categorization**: Which event types belong to which categories
   - Mapping maintained locally
   - Not provided by API

---

## 🔄 Data Flow

### Event Types
```
API /api/event_types → Competition Type Dropdown
```

### Categories
```
Local CSV → Category Dropdown → Filters CSV data → Filtered Event Types
```

### Results with Averages
```
API /api/athlete/{id}/results → Raw results
    ↓
Local CSV (arrow counts) → Calculate averages
    ↓
Transformed results with average_per_arrow
```

### Statistics
```
API /api/athlete/{id}/results → Raw results
    ↓
Local processing (medals, positions, etc.) → Statistics summary
    ↓
Frontend display
```

---

## ⚠️ Important Notes

1. **Event Types Source of Truth**: Always use `/api/event_types` for the authoritative list
2. **CSV Synchronization**: CSV must be manually updated when new event types are added to the API
3. **No Competition Management API**: Competition subscription features will need separate implementation
4. **Local Processing**: Statistics are computed locally, not from API
5. **Category Filtering**: Categories are local concepts, not from API

---

## 🔧 Current Implementation

### Routes Using API
- `/archery/api/search_athlete` → Calls `/api/atleti`
- `/archery/api/athlete/{id}/results` → Calls `/api/athlete/{tessera}/results`
- `/archery/api/athlete/{id}/statistics` → Calls `/api/stats` + `/api/athlete/{tessera}/results`
- `/archery/api/competition_types` → Calls `/api/event_types`

### Routes Using Local Data Only
- `/archery/api/categories` → Reads CSV file
- `/archery/api/category/{cat}/types` → Reads CSV file

### Hybrid Routes (API + Local)
- `/archery/api/athlete/{id}/results?include_average=true` → API + CSV processing
- `/archery/api/athlete/{id}/statistics` → API + local statistics calculation
