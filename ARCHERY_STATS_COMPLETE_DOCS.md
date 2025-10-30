# Archery Statistics System - Complete Documentation

**Last Updated:** October 30, 2025  
**Status:** ✅ FULLY OPERATIONAL  
**API Integration:** 100% Complete

---

## 🎯 System Overview

The archery statistics system integrates with the external FastAPI service at `api.orion-project.it` to provide comprehensive athlete performance analytics, including:

- Career statistics (total competitions, medals, best scores)
- Filtered statistics by competition type and date range
- Performance charts and visualizations
- Multi-athlete comparison
- Category-based breakdowns (Indoor 18m, Outdoor 70m, etc.)

---

## 📋 Table of Contents

1. [Architecture](#architecture)
2. [API Integration](#api-integration)
3. [Database Schema](#database-schema)
4. [File Structure](#file-structure)
5. [API Endpoints](#api-endpoints)
6. [Data Flow](#data-flow)
7. [Frontend Components](#frontend-components)
8. [Error Handling](#error-handling)
9. [Testing Guide](#testing-guide)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Browser)                       │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  archery-analysis.js                                    │ │
│  │  - Loads statistics via AJAX                            │ │
│  │  - Renders charts (Chart.js)                            │ │
│  │  - Handles athlete comparison                           │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/JSON
┌───────────────────────────▼─────────────────────────────────┐
│              Flask Backend (site01/app)                      │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  routes/archery.py                                      │ │
│  │  - /archery/api/athlete/<id>/statistics                │ │
│  │  - /archery/api/athlete/<id>/results                   │ │
│  │  - /archery/api/competition_types                       │ │
│  └────────────────┬───────────────────────────────────────┘ │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  api/__init__.py (OrionAPIClient)                      │ │
│  │  - Handles all external API calls                      │ │
│  │  - Manages authentication & error handling             │ │
│  └────────────────┬───────────────────────────────────────┘ │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  archery_utils.py                                       │ │
│  │  - Statistics calculations                              │ │
│  │  - Medal counting, percentiles, categories             │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS
┌───────────────────────────▼─────────────────────────────────┐
│           External API (api.orion-project.it)                │
│  - /api/stats (chart data)                                   │
│  - /api/athlete/{tessera}/results (detailed results)        │
│  - /api/event_types (competition types list)                │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend:** Flask 2.x, Python 3.11+
- **Frontend:** Vanilla JavaScript, Chart.js 4.x, Tailwind CSS
- **External API:** FastAPI (separate service)
- **Database:** MariaDB (production), SQLite (dev)
- **Authentication:** Session-based (Flask sessions)

---

## 🔌 API Integration

### External API Endpoints Used

#### 1. GET `/api/stats`
**Purpose:** Retrieve time-series data for performance charts

**Request:**
```http
GET https://api.orion-project.it/api/stats?athlete_ids=93229,149020&event_type=18%20m&from_date=2023-01-01&to_date=2025-12-31&period_months=6
```

**Parameters:**
- `athlete_ids` (required): Comma-separated athlete IDs (tessera numbers)
- `event_type` (optional): Filter by competition type (e.g., "18 m", "70/60mt Round")
- `from_date` (optional): Start date (YYYY-MM-DD)
- `to_date` (optional): End date (YYYY-MM-DD)
- `period_months` (optional): Aggregation period in months

**Response:**
```json
{
  "labels": ["2023-01", "2023-07", "2024-01", "2024-07"],
  "datasets": [
    {
      "name": "Cesarotto Giovanni Igor",
      "data": [520, 535, 548, 542]
    }
  ]
}
```

**Implementation:** `app/api/__init__.py` line 134
```python
def get_statistics(self, athlete_ids, event_type=None, from_date=None, to_date=None, period_months=None):
    url = f"{self.base_url}/api/stats"
    # Uses event_type (NOT competition_type)
    # Uses from_date/to_date (NOT start_date/end_date)
```

---

#### 2. GET `/api/athlete/{tessera}/results`
**Purpose:** Get detailed competition results with scores and positions

**Request:**
```http
GET https://api.orion-project.it/api/athlete/93229/results?event_type=18%20m&limit=500
```

**Parameters:**
- `tessera` (path, required): Athlete ID (tessera number)
- `event_type` (optional): Filter by competition type
- `limit` (optional): Maximum number of results (default: 100)

**Response Format:**
```json
{
  "summary": {
    "count": 91,
    "best_score": 1057,
    "avg_score": 502.73,
    "avg_position": 8.73
  },
  "results": [
    {
      "tessera": "93229",
      "atleta": "Cesarotto Giovanni Igor",
      "codice_societa_atleta": "06084",
      "nome_societa_atleta": "A.S.D.COMPAGNIA ARCIERI CARRARESI",
      "nome_gara": "10 Torneo Carraresi",
      "tipo_gara": "70/60mt Round - 50mt Round",
      "data_gara": "2025-07-06",
      "codice_gara": "R2506054",
      "luogo_gara": "Due Carrare (PD)",
      "codice_societa_organizzatrice": "06084",
      "nome_societa_organizzatrice": "A.S.D.COMPAGNIA ARCIERI CARRARESI",
      "posizione": 3,
      "punteggio": 540
    }
  ]
}
```

**Field Mapping (API → Internal):**
```python
{
    'atleta': 'athlete',
    'nome_gara': 'competition_name',
    'tipo_gara': 'competition_type',
    'data_gara': 'date',
    'posizione': 'position',
    'punteggio': 'score'
}
```

**Implementation:** `app/api/__init__.py` line 105
```python
def get_athlete_results(self, athlete_id, competition_type=None, start_date=None, end_date=None, limit=100):
    url = f"{self.base_url}/api/athlete/{athlete_id}/results"
    params = {}
    if competition_type:
        params['event_type'] = competition_type  # Maps competition_type → event_type
    if limit:
        params['limit'] = limit
    # Returns wrapper: {summary: {...}, results: [...]}
```

---

#### 3. GET `/api/event_types`
**Purpose:** Get list of all available competition types

**Request:**
```http
GET https://api.orion-project.it/api/event_types
```

**Response:**
```json
[
  "18 m",
  "25+18",
  "70/60mt Round - 50mt Round",
  "Trofeo Pinocchio"
]
```

**Implementation:** `app/api/__init__.py` line 156
```python
def get_competition_types(self):
    url = f"{self.base_url}/api/event_types"
    # Returns simple list of strings
```

---

### API Response Handling

#### Wrapper Format Support
Both legacy (direct array) and new (wrapper object) formats are supported:

**Legacy Format:**
```json
[
  {"atleta": "...", "punteggio": 540, ...},
  {"atleta": "...", "punteggio": 535, ...}
]
```

**New Format (Wrapper):**
```json
{
  "summary": {"count": 91, "best_score": 1057, ...},
  "results": [
    {"atleta": "...", "punteggio": 540, ...},
    {"atleta": "...", "punteggio": 535, ...}
  ]
}
```

**Detection Logic:** `app/routes/archery.py` lines 207-215
```python
if not isinstance(all_results, list):
    current_app.logger.info(f"API returned wrapped format: {type(all_results)}")
    if isinstance(all_results, dict) and 'results' in all_results:
        current_app.logger.info(f"Extracting results array ({len(all_results['results'])} items)")
        all_results = all_results['results']
    else:
        return jsonify({'error': 'Unexpected API response format'}), 502
```

---

## 💾 Database Schema

### Athletes Table
```sql
CREATE TABLE athletes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tessera VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    birth_date DATE,
    club_code VARCHAR(20),
    club_name VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

**Key Fields:**
- `tessera`: Athlete ID used for API calls (e.g., "93229")
- `first_name`, `last_name`: Display name
- `club_code`, `club_name`: Organization affiliation

**Note:** Competition results are NOT stored in database - they're fetched from API in real-time.

---

## 📁 File Structure

```
site01/
├── app/
│   ├── routes/
│   │   └── archery.py              # Flask routes for archery statistics
│   │       - get_athlete_results()         (line 82)
│   │       - get_athlete_statistics()      (line 158)
│   │       - get_competition_types()       (line 349)
│   │
│   ├── api/
│   │   └── __init__.py             # OrionAPIClient class
│   │       - get_athlete_results()         (line 105)
│   │       - get_statistics()              (line 134)
│   │       - get_competition_types()       (line 156)
│   │
│   ├── archery_utils.py            # Statistics calculation utilities
│   │   - calculate_medal_count()           (line 82)
│   │   - calculate_percentile_stats()      (line 149)
│   │   - get_best_score_by_category()      (line 191)
│   │   - get_statistics_summary()          (line 259)
│   │   - filter_by_category()              (line 118)
│   │
│   ├── templates/
│   │   └── archery/
│   │       └── analysis.html       # Statistics page template
│   │
│   └── static/
│       └── js/
│           └── archery-analysis.js # Frontend JavaScript
│               - loadStatistics()          (line 619)
│               - loadComparisonStatistics() (line 675)
│               - renderChart()             (line 491)
│               - analyzeResults()          (line 236)
│
└── docs/
    └── api/
        └── APIspec.md              # Complete API specification
            - /api/stats                    (line 402)
            - /api/athlete/{tessera}/results (line 495)
            - /api/event_types              (line 575)
```

---

## 🔗 API Endpoints (Flask Backend)

### 1. GET `/archery/api/athlete/<athlete_id>/results`
**Purpose:** Get filtered competition results for an athlete

**Parameters:**
- `athlete_id` (path): Athlete tessera number
- `competition_type` (query): Filter by type
- `start_date` (query): Not supported by external API (filtered client-side)
- `end_date` (query): Not supported by external API (filtered client-side)
- `category` (query): Filter by category (Indoor, Outdoor, etc.)

**Response:**
```json
[
  {
    "athlete": "Cesarotto Giovanni Igor",
    "competition_name": "10 Torneo Carraresi",
    "competition_type": "70/60mt Round - 50mt Round",
    "date": "2025-07-06",
    "position": 3,
    "score": 540,
    "club_code": "06084",
    "club_name": "A.S.D.COMPAGNIA ARCIERI CARRARESI"
  }
]
```

**Implementation:** `app/routes/archery.py` line 82

---

### 2. GET `/archery/api/athlete/<athlete_id>/statistics`
**Purpose:** Get comprehensive statistics (career + filtered)

**Parameters:**
- `athlete_id` (path): Athlete tessera number
- `competition_type` (query): Filter statistics by type
- `from_date` (query): Start date for filtering (YYYY-MM-DD)
- `to_date` (query): End date for filtering (YYYY-MM-DD)

**Response:**
```json
{
  "athlete_id": "93229",
  "career": {
    "total_competitions": 91,
    "gold_medals": 12,
    "silver_medals": 8,
    "bronze_medals": 15,
    "avg_position": 8.7,
    "avg_percentile": 29.0,
    "top_finishes": 15,
    "recent_competitions_analyzed": 10,
    "best_score": 1057,
    "best_score_competition": "8° Trofeo delle Tigri",
    "best_scores_by_category": {
      "Indoor 18m": {
        "score": 553,
        "competition": "32° indoor GATTAMELATA",
        "date": "2023-11-25",
        "type": "18 m"
      }
    },
    "category_breakdown": {
      "Indoor 18m": {"count": 65, "best_score": 553},
      "Outdoor 70m": {"count": 18, "best_score": 576}
    }
  },
  "filtered": {
    "total_competitions": 45,
    "gold_medals": 8,
    "best_score": 553
  },
  "chart_data": {
    "labels": ["2023-01", "2023-07", "2024-01"],
    "datasets": [{
      "name": "Cesarotto Giovanni Igor",
      "data": [520, 535, 548]
    }]
  }
}
```

**Implementation:** `app/routes/archery.py` line 158

---

### 3. GET `/archery/api/competition_types`
**Purpose:** Get list of all available competition types

**Response:**
```json
[
  "18 m",
  "25+18",
  "70/60mt Round - 50mt Round",
  "Trofeo Pinocchio"
]
```

**Implementation:** `app/routes/archery.py` line 349

---

## 🔄 Data Flow

### Statistics Loading Flow

```
1. User opens /archery/analysis page
   └─> Loads archery-analysis.js

2. User clicks "Analyze Results" button
   └─> analyzeResults() function called
       └─> loadStatistics(athleteId) for each athlete
           
3. loadStatistics() makes AJAX call
   └─> GET /archery/api/athlete/{id}/statistics
       
4. Flask route: get_athlete_statistics()
   ├─> Calls OrionAPIClient.get_statistics()
   │   └─> GET https://api.orion-project.it/api/stats
   │       └─> Returns chart data
   │
   └─> Calls OrionAPIClient.get_athlete_results()
       └─> GET https://api.orion-project.it/api/athlete/{id}/results
           └─> Returns {summary, results}
           
5. Flask processes results
   ├─> Extracts results array from wrapper
   ├─> Transforms field names (atleta→athlete, punteggio→score)
   ├─> Calculates career statistics
   │   ├─> Medal count (calculate_medal_count)
   │   ├─> Percentile stats (calculate_percentile_stats)
   │   ├─> Best scores by category (get_best_score_by_category)
   │   └─> Category breakdown
   │
   └─> Calculates filtered statistics (if filters applied)
   
6. Returns JSON to frontend
   └─> archery-analysis.js receives data
       ├─> Updates statistics display
       ├─> Renders medals (updateMedals)
       ├─> Updates best scores table
       └─> Renders chart (renderChart)
```

### Error Handling Flow

```
API Call Fails
└─> OrionAPIClient catches exception
    └─> Logs error with traceback
        └─> Returns None or raises exception
            └─> Flask route catches exception
                ├─> Logs error details
                ├─> Returns 500 or 502 with error JSON
                    └─> Frontend displays error message
                        └─> User sees "Failed to load statistics"
```

---

## 🎨 Frontend Components

### archery-analysis.js Key Functions

#### 1. `analyzeResults()` (line 236)
**Purpose:** Main entry point for loading statistics

```javascript
async function analyzeResults() {
    const athleteIds = getSelectedAthleteIds(); // From form
    const filters = {
        competition_type: document.getElementById('competition-type-filter').value,
        from_date: document.getElementById('from-date-filter').value,
        to_date: document.getElementById('to-date-filter').value
    };
    
    for (const athleteId of athleteIds) {
        await loadStatistics(athleteId, filters);
    }
    
    if (athleteIds.length > 1) {
        await loadComparisonStatistics(athleteIds, filters);
    }
}
```

---

#### 2. `loadStatistics()` (line 619)
**Purpose:** Load statistics for a single athlete

```javascript
async function loadStatistics(athleteId, filters = {}) {
    const params = new URLSearchParams({
        competition_type: filters.competition_type || '',
        from_date: filters.from_date || '',
        to_date: filters.to_date || ''
    });
    
    const response = await fetch(`/archery/api/athlete/${athleteId}/statistics?${params}`);
    const data = await response.json();
    
    updateStatisticsDisplay(athleteId, data);
    updateMedals(athleteId, data.career);
    updateBestScores(athleteId, data.career.best_scores_by_category);
}
```

---

#### 3. `renderChart()` (line 491)
**Purpose:** Render performance chart using Chart.js

```javascript
function renderChart(chartData, comparisonMode = false) {
    const ctx = document.getElementById('performance-chart').getContext('2d');
    
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: chartData.labels,
            datasets: chartData.datasets.map(ds => ({
                label: ds.name,
                data: ds.data,
                borderColor: getAthleteColor(ds.name),
                tension: 0.4
            }))
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: comparisonMode },
                tooltip: { mode: 'index' }
            }
        }
    });
}
```

---

### HTML Structure (analysis.html)

```html
<div class="athlete-form">
    <select name="athlete_1" class="athlete-select">
        <option value="">Select Athlete 1</option>
        <!-- Populated from database -->
    </select>
    
    <select name="athlete_2" class="athlete-select">
        <option value="">Select Athlete 2 (Optional)</option>
    </select>
</div>

<div class="filters">
    <select id="competition-type-filter">
        <option value="">All Types</option>
        <!-- Populated from /api/competition_types -->
    </select>
    
    <input type="date" id="from-date-filter">
    <input type="date" id="to-date-filter">
</div>

<button onclick="analyzeResults()">Analyze Results</button>

<div id="statistics-container">
    <!-- Career Statistics -->
    <div class="stat-card">
        <h3>Career Statistics</h3>
        <div class="medals">🥇 <span id="gold-medals">0</span></div>
        <div class="stats">
            <p>Total Competitions: <span id="total-comps">0</span></p>
            <p>Avg Position: <span id="avg-position">-</span></p>
            <p>Best Score: <span id="best-score">-</span></p>
        </div>
    </div>
    
    <!-- Performance Chart -->
    <canvas id="performance-chart"></canvas>
</div>
```

---

## 🛡️ Error Handling

### API Client Error Handling
**Location:** `app/api/__init__.py`

```python
def get_athlete_results(self, athlete_id, ...):
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        current_app.logger.error(f"API error: {str(e)}")
        return None
```

**Error Types Handled:**
- `ConnectionError`: Cannot reach API server
- `Timeout`: Request took longer than 30 seconds
- `HTTPError`: API returned 4xx or 5xx status
- `JSONDecodeError`: Invalid JSON response

---

### Flask Route Error Handling
**Location:** `app/routes/archery.py`

```python
@bp.route('/api/athlete/<athlete_id>/statistics')
def get_athlete_statistics(athlete_id):
    try:
        # ... main logic ...
        return jsonify(response)
    except Exception as e:
        import traceback
        current_app.logger.error(f"Error: {str(e)}")
        current_app.logger.error(f"Type: {type(e).__name__}")
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to fetch statistics', 'details': str(e)}), 500
```

**Error Response Format:**
```json
{
  "error": "Failed to fetch athlete statistics",
  "details": "KeyError: 'results'"
}
```

---

### Frontend Error Handling
**Location:** `app/static/js/archery-analysis.js`

```javascript
async function loadStatistics(athleteId, filters = {}) {
    try {
        const response = await fetch(`/archery/api/athlete/${athleteId}/statistics?${params}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        if (!data.career || !data.career.total_competitions) {
            throw new Error('Invalid data structure');
        }
        
        updateStatisticsDisplay(athleteId, data);
    } catch (error) {
        console.error('Error loading statistics:', error);
        showErrorMessage(`Failed to load statistics for athlete ${athleteId}`);
    }
}
```

---

### None Value Handling
**Critical Fix:** `app/routes/archery.py` lines 262-273

```python
# Filter out results with None or 0 scores before finding max
valid_scores = [r for r in transformed_results 
                if r.get('score') is not None and r.get('score') > 0]

if valid_scores:
    best_result = max(valid_scores, key=lambda x: x.get('score', 0))
    career_statistics['best_score'] = best_result.get('score')
else:
    career_statistics['best_score'] = None
```

**Why This Matters:** Some competitions have `null` scores (e.g., DNS - Did Not Start). Without filtering, `max()` would raise `TypeError: '>' not supported between instances of 'NoneType' and 'NoneType'`.

---

## 🧪 Testing Guide

### Manual Testing Checklist

#### 1. Single Athlete Statistics
```
✅ Open /archery/analysis
✅ Select athlete from dropdown (e.g., "Cesarotto Giovanni Igor")
✅ Click "Analyze Results"
✅ Verify:
   - Total competitions shown (should be ~91)
   - Medals displayed correctly
   - Best score shown with competition name
   - Chart renders with data points
   - No console errors
```

#### 2. Filtered Statistics
```
✅ Select athlete
✅ Set competition type filter to "18 m"
✅ Click "Analyze Results"
✅ Verify:
   - Filtered competition count < total competitions
   - Only Indoor 18m competitions counted
   - Chart updates to show filtered data
```

#### 3. Date Range Filtering
```
✅ Select athlete
✅ Set from_date to "2024-01-01"
✅ Set to_date to "2024-12-31"
✅ Click "Analyze Results"
✅ Verify:
   - Only 2024 competitions counted
   - Medals reflect 2024 results only
```

#### 4. Multi-Athlete Comparison
```
✅ Select athlete 1 (e.g., ID 93229)
✅ Select athlete 2 (e.g., ID 149020)
✅ Click "Analyze Results"
✅ Verify:
   - Two stat cards displayed
   - Chart shows two lines (different colors)
   - Legend displays both athlete names
   - Comparison table shows side-by-side stats
```

#### 5. Error Scenarios
```
✅ Test with invalid athlete ID
   → Should show "Failed to load statistics"
   
✅ Stop API container (simulate API down)
   → Should show 502 error message
   
✅ Set invalid date range (to_date < from_date)
   → Should handle gracefully (no results)
```

---

### API Testing with cURL

#### Test /api/stats endpoint
```bash
curl -X GET "https://api.orion-project.it/api/stats?athlete_ids=93229&event_type=18%20m&from_date=2023-01-01&to_date=2025-12-31&period_months=6"
```

**Expected Response:**
```json
{
  "labels": ["2023-01", "2023-07", "2024-01", "2024-07", "2025-01", "2025-07"],
  "datasets": [{
    "name": "Cesarotto Giovanni Igor",
    "data": [520, 535, 548, 542, 550, 540]
  }]
}
```

---

#### Test /api/athlete/{tessera}/results endpoint
```bash
curl -X GET "https://api.orion-project.it/api/athlete/93229/results?event_type=18%20m&limit=10"
```

**Expected Response:**
```json
{
  "summary": {
    "count": 65,
    "best_score": 553,
    "avg_score": 526.4,
    "avg_position": 7.2
  },
  "results": [
    {
      "tessera": "93229",
      "atleta": "Cesarotto Giovanni Igor",
      "nome_gara": "32° indoor GATTAMELATA",
      "tipo_gara": "18 m",
      "data_gara": "2023-11-25",
      "posizione": 1,
      "punteggio": 553
    }
  ]
}
```

---

### Docker Logs Monitoring

```bash
# Watch logs in real-time
docker-compose logs -f web

# Check for errors
docker-compose logs web | grep ERROR

# Check API calls
docker-compose logs web | grep "API returned"
```

**Key Log Messages:**
```
✅ API returned wrapped format: <class 'dict'>
✅ Extracting results array (91 items) from wrapper
✅ Processing 91 results
✅ Transformed 91 results

❌ ERROR in archery: API returned None for all_results
❌ ERROR in archery: Unexpected API payload
❌ ERROR in archery: Error fetching athlete statistics: KeyError
```

---

## 🔧 Troubleshooting

### Issue 1: "Failed to load statistics" Error

**Symptoms:**
- Frontend shows error message
- Console shows `GET /archery/api/athlete/93229/statistics 500`

**Check:**
1. Docker logs: `docker-compose logs web | grep ERROR`
2. Look for exception traceback
3. Check API connectivity: `curl https://api.orion-project.it/api/stats`

**Common Causes:**
- External API is down
- Network connectivity issue
- Database query failed
- Invalid athlete ID

**Solution:**
```bash
# Restart containers
docker-compose restart web

# Check API health
curl https://api.orion-project.it/api/stats

# Verify database connection
docker-compose exec web python -c "from app import create_app; app = create_app(); print('DB OK')"
```

---

### Issue 2: Chart Not Rendering

**Symptoms:**
- Statistics load correctly
- Chart area is blank
- No console errors

**Check:**
1. Verify Chart.js is loaded: `console.log(Chart)`
2. Check canvas element exists: `document.getElementById('performance-chart')`
3. Inspect `chartData` structure in browser console

**Common Causes:**
- Chart.js not loaded (CDN issue)
- Canvas element ID mismatch
- Invalid chart data format

**Solution:**
```javascript
// Add to archery-analysis.js for debugging
console.log('Chart data:', chartData);
console.log('Canvas element:', document.getElementById('performance-chart'));
console.log('Chart.js version:', Chart.version);
```

---

### Issue 3: Wrong Number of Competitions

**Symptoms:**
- Shows 2 competitions instead of 91
- Using old `/api/iscrizioni` endpoint

**Check:**
1. Verify API endpoint in logs: `grep "Calling API" logs.txt`
2. Check OrionAPIClient code uses correct endpoint

**Solution:**
Ensure `app/api/__init__.py` line 105 uses `/api/athlete/{tessera}/results`:
```python
url = f"{self.base_url}/api/athlete/{athlete_id}/results"
```

---

### Issue 4: KeyError: 0

**Symptoms:**
- Error: `KeyError: 0`
- Traceback shows `all_results[0]`

**Root Cause:**
API returns wrapper dict `{summary, results}` but code tries to access `all_results[0]` before extracting array.

**Solution:**
Ensure wrapper extraction happens BEFORE accessing first element:
```python
# WRONG ORDER (causes KeyError: 0)
if all_results and len(all_results) > 0:
    print(all_results[0])  # Tries dict[0] before extraction

if not isinstance(all_results, list):
    all_results = all_results['results']  # Too late!

# CORRECT ORDER
if not isinstance(all_results, list):
    all_results = all_results['results']  # Extract first

if all_results and len(all_results) > 0:
    print(all_results[0])  # Now it's a list
```

**Fixed in:** `app/routes/archery.py` lines 203-217 (Oct 30, 2025)

---

### Issue 5: TypeError: '>' not supported between NoneType

**Symptoms:**
- Error when calculating best score
- Some competitions have `null` scores

**Root Cause:**
`max()` function fails when comparing None values.

**Solution:**
Filter out None/0 scores before finding max:
```python
# Filter out invalid scores
valid_scores = [r for r in results 
                if r.get('score') is not None and r.get('score') > 0]

if valid_scores:
    best_result = max(valid_scores, key=lambda x: x.get('score', 0))
else:
    best_result = None
```

**Fixed in:** `app/routes/archery.py` lines 262-273 (Oct 30, 2025)

---

### Issue 6: ZeroDivisionError in Percentile Calculation

**Symptoms:**
- Error: `ZeroDivisionError: division by zero`
- Traceback in `calculate_percentile_stats()`

**Root Cause:**
All positions are None, resulting in empty list and division by 0.

**Solution:**
Check for empty positions list before division:
```python
positions = [r.get('position') for r in recent if r.get('position')]

if not positions or len(positions) == 0:
    return {'avg_position': None, 'avg_percentile': None, 'top_finishes': 0}

avg_position = sum(positions) / len(positions)  # Safe now
```

**Fixed in:** `app/archery_utils.py` lines 171-179 (Oct 30, 2025)

---

## 📊 Statistics Calculations

### Medal Counting Logic
**Location:** `app/archery_utils.py` line 82

```python
def calculate_medal_count(results: List[Dict]) -> Dict:
    medals = {'gold': 0, 'silver': 0, 'bronze': 0}
    
    for result in results:
        position = result.get('position')
        if position == 1:
            medals['gold'] += 1
        elif position == 2:
            medals['silver'] += 1
        elif position == 3:
            medals['bronze'] += 1
    
    return medals
```

---

### Percentile Calculation
**Location:** `app/archery_utils.py` line 149

**Formula:**
```
avg_position = sum(positions) / len(positions)
estimated_percentile = min(100, (avg_position / 30) * 100)
```

**Assumptions:**
- Average of ~30 participants per competition
- Lower position = better performance
- Position 1 = ~3.3 percentile (top 3.3%)
- Position 10 = ~33 percentile

---

### Category Mapping
**Location:** `app/archery_utils.py` line 39

```python
COMPETITION_CATEGORIES = {
    "Indoor 18m": ["18 m"],
    "Indoor 25m": ["25 m", "25+18"],
    "Outdoor 70m": [
        "70/60mt Round",
        "70/60mt Round - 50mt Round",
        "70/60mt Round - 50mt Round - 36 Frecce"
    ],
    "Outdoor 50m": ["50 m", "50mt Round"],
    "Youth": ["Trofeo Pinocchio"],
    "Other": []  # Catch-all
}
```

---

## 🚀 Deployment Notes

### Environment Variables
```bash
# .env file
ORION_API_BASE_URL=https://api.orion-project.it
ORION_API_KEY=your_api_key_here  # If authentication added later
DATABASE_URL=mysql://user:pass@localhost/orion_db
FLASK_ENV=production
SECRET_KEY=your_secret_key
```

---

### Production Checklist

```
✅ Environment variables set
✅ API base URL points to production (api.orion-project.it)
✅ Database migrations applied
✅ Static files collected/served
✅ HTTPS enabled
✅ CORS configured if needed
✅ Logging configured (errors to file)
✅ Rate limiting enabled (if high traffic)
✅ Monitoring/alerts set up
✅ Backup strategy in place
```

---

### Docker Deployment

```bash
# Build image
docker build -t orion-archery:latest .

# Run container
docker run -d \
  --name orion-web \
  -p 5000:5000 \
  -e ORION_API_BASE_URL=https://api.orion-project.it \
  -e DATABASE_URL=mysql://user:pass@db:3306/orion_db \
  orion-archery:latest

# Check logs
docker logs -f orion-web

# Restart container
docker restart orion-web
```

---

## 📝 Key Decisions & Rationale

### Why Real-Time API Calls Instead of Database Storage?

**Decision:** Fetch competition results from API in real-time, don't cache in database.

**Rationale:**
1. **Data Freshness:** Always shows latest results without sync lag
2. **Single Source of Truth:** External API is authoritative
3. **Reduced Complexity:** No sync jobs, no data staleness issues
4. **Storage Efficiency:** Don't duplicate large datasets

**Trade-offs:**
- ❌ Slower load times (API latency)
- ❌ Dependency on external service availability
- ✅ Always current data
- ✅ Simpler architecture

---

### Why Wrapper Format Support?

**Decision:** Support both direct array and `{summary, results}` wrapper formats.

**Rationale:**
1. **Backward Compatibility:** Old API returns direct array
2. **Future-Proofing:** New API returns wrapper with metadata
3. **Graceful Degradation:** Works with both formats transparently

**Implementation:**
```python
if isinstance(all_results, dict) and 'results' in all_results:
    all_results = all_results['results']
```

---

### Why Transform Field Names?

**Decision:** Map Italian API field names to English internal names.

**Rationale:**
1. **Code Consistency:** English codebase uses English field names
2. **Clarity:** `score` clearer than `punteggio` to non-Italian speakers
3. **Maintainability:** Easier to work with consistent naming

**Mapping:**
```python
{
    'atleta': 'athlete',
    'nome_gara': 'competition_name',
    'tipo_gara': 'competition_type',
    'data_gara': 'date',
    'posizione': 'position',
    'punteggio': 'score'
}
```

---

## 🎓 Learning Resources

### Understanding the API
- **API Spec:** `docs/api/APIspec.md`
- **External API:** https://api.orion-project.it/docs (FastAPI auto-docs)
- **Example Calls:** See "API Testing with cURL" section above

### Code References
- **Flask Routes:** https://flask.palletsprojects.com/routing/
- **Chart.js:** https://www.chartjs.org/docs/
- **Requests Library:** https://requests.readthedocs.io/

---

## 🔄 Recent Changes Log

### October 30, 2025
**Major API Integration Update**

**Changes:**
1. ✅ Updated API client to use `/api/athlete/{tessera}/results` endpoint
2. ✅ Added support for wrapper format `{summary, results}`
3. ✅ Fixed KeyError: 0 by reordering wrapper extraction before access
4. ✅ Fixed TypeError on None comparisons by filtering scores before max()
5. ✅ Fixed ZeroDivisionError by checking empty positions list
6. ✅ Added comprehensive error logging with traceback
7. ✅ Updated field mappings to match exact API response format

**Files Modified:**
- `app/api/__init__.py` (lines 105-127, 134-148)
- `app/routes/archery.py` (lines 82-120, 158-345)
- `app/archery_utils.py` (lines 171-179)
- `docs/api/APIspec.md` (lines 495-547)

**Testing Status:**
- ✅ Single athlete statistics: WORKING (91 competitions)
- ✅ Multi-athlete comparison: WORKING
- ✅ Chart rendering: WORKING
- ✅ Medal counting: WORKING
- ✅ Filtered statistics: WORKING
- ✅ Error handling: WORKING

---

## 📞 Support & Maintenance

### Common Maintenance Tasks

#### Update Competition Type Mappings
**File:** `app/archery_utils.py` line 39

```python
# Add new competition type to existing category
COMPETITION_CATEGORIES = {
    "Indoor 18m": ["18 m", "18m Indoor Round"],  # Added variant
    # ...
}
```

#### Adjust Percentile Calculation
**File:** `app/archery_utils.py` line 181

```python
# Change assumed participant count
estimated_percentile = min(100, (avg_position / 40) * 100)  # Changed from 30
```

#### Add New Statistics Fields
1. Update `get_statistics_summary()` in `archery_utils.py`
2. Update response format in `get_athlete_statistics()` in `routes/archery.py`
3. Update frontend display in `archery-analysis.js`

---

### Contact Information
- **Developer:** [Your Name]
- **Repository:** https://github.com/TheIgorMC/mysite
- **API Documentation:** https://api.orion-project.it/docs
- **Issue Tracker:** GitHub Issues

---

## ✅ Final Status

**System Status:** 🟢 FULLY OPERATIONAL

**Integration Status:**
- ✅ `/api/stats` endpoint: 100% complete
- ✅ `/api/athlete/{tessera}/results` endpoint: 100% complete
- ✅ `/api/event_types` endpoint: 100% complete

**Known Issues:** None

**Next Steps:**
1. Monitor production logs for any edge cases
2. Consider caching API responses (Redis) for performance
3. Add more granular filtering options (by location, organizer)
4. Export statistics to PDF/Excel

---

**Document Version:** 1.0  
**Last Updated:** October 30, 2025, 14:10 UTC  
**Author:** GitHub Copilot + User Collaboration  
**Status:** Complete & Ready for Production

---

## 📋 Quick Reference Card

### Most Common Commands
```bash
# View logs
docker-compose logs -f web

# Restart service
docker-compose restart web

# Test API
curl "https://api.orion-project.it/api/athlete/93229/results?limit=5"

# Check database
docker-compose exec db mysql -u root -p orion_db
```

### Most Important Files
- `app/routes/archery.py` - Flask routes (statistics endpoints)
- `app/api/__init__.py` - API client (external API calls)
- `app/archery_utils.py` - Statistics calculations
- `app/static/js/archery-analysis.js` - Frontend logic
- `docs/api/APIspec.md` - Complete API specification

### Emergency Fixes
```python
# If API changes field names, update mapping:
# app/routes/archery.py line 236
transformed_results.append({
    'score': result.get('NEW_FIELD_NAME')  # Change here
})

# If statistics calculation fails, add defensive check:
# app/archery_utils.py
if not results or len(results) == 0:
    return default_value
```

---

**END OF DOCUMENTATION**
