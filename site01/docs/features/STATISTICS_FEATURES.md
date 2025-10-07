# Advanced Statistics Features

## Overview
The archery analysis system now supports:
1. **Dual Statistics View**: Career stats + Filtered period stats (when filters applied)
2. **Multi-Athlete Comparison**: Side-by-side statistics comparison for up to 5 athletes
3. **Dynamic Updates**: Statistics automatically refresh when athletes are added/removed

## Features

### 1. Career vs Filtered Statistics (Single Athlete)

#### How It Works
When analyzing a single athlete:
- **Career Statistics** are ALWAYS shown (entire competition history)
- **Filtered Statistics** are shown ADDITIONALLY when any filter is applied

#### Filters Supported
- Date Range (start date and/or end date)
- Competition Type (e.g., "1/2 FITA", "Indoor", etc.)
- Category (e.g., "FITA", "Indoor", "3D")

#### Visual Distinction
- Career stats: Standard white/gray cards
- Filtered stats: Highlighted with accent color border and "Filtered" badge

#### Example Use Cases
1. **"How did I perform in 2024?"**
   - Set date range: 01/01/2024 - 31/12/2024
   - See career stats (all time) vs 2024 stats side by side

2. **"How am I doing in Indoor competitions?"**
   - Select Category: Indoor
   - Compare overall career vs Indoor-specific performance

3. **"Recent FITA performance vs career"**
   - Select Type: "1/2 FITA"
   - Set start date: last 6 months
   - Compare career FITA stats vs recent FITA performance

#### Statistics Displayed

**Career Statistics:**
- Total Competitions (all time)
- Medals: Gold, Silver, Bronze (all time)
- Average Position & Percentile (last 10 competitions)
- Best Score Ever (with competition name)

**Filtered Statistics:**
- Competitions (in filtered period)
- Medals (in filtered period)
- Average Position & Percentile (last 10 in period)
- Best Score (in filtered period)

### 2. Multi-Athlete Comparison

#### How It Works
When 2 or more athletes are selected:
- Statistics display switches to **comparison mode**
- Shows side-by-side table comparing all athletes
- Individual highlight cards for each athlete below table

#### Selection Behavior
- Add athletes using search
- Up to 5 athletes can be compared simultaneously
- **Auto-refresh**: Adding/removing athlete automatically re-runs analysis
- Filters apply to ALL athletes in comparison

#### Comparison Table Columns
| Column | Description |
|--------|-------------|
| Athlete | Name of athlete |
| Competitions | Total competitions (filtered or career) |
| 🥇 | Gold medals count |
| 🥈 | Silver medals count |
| 🥉 | Bronze medals count |
| Avg Position | Average finishing position |
| Best Score | Highest score achieved |

#### Filtered vs Career in Comparison
- **No filters**: Shows career statistics for all athletes
- **With filters**: Shows filtered statistics for all athletes
- Title changes to indicate which mode: "Career Statistics Comparison" vs "Filtered Statistics Comparison"

#### Individual Highlight Cards
Below the comparison table, each athlete gets a card showing:
- Best score with competition name
- Performance percentile and average position
- Podium finishes (top 3) in recent competitions

### 3. Dynamic Updates

#### Automatic Refresh Triggers
Statistics automatically refresh when:
1. **Adding an athlete** (if analysis already performed)
2. **Removing an athlete** (if analysis already performed)
3. **Clicking Analyze** button (always)

#### Behavior by State

**No Athletes Selected:**
- Chart empty
- Statistics hidden
- Analyze button requires at least 1 athlete

**1 Athlete Selected:**
- Shows detailed career + filtered statistics
- Full statistical breakdown
- Individual athlete focus

**2+ Athletes Selected:**
- Switches to comparison mode
- Comparative table view
- Maintains filter context

**Adding 2nd Athlete:**
- Automatically switches from detailed view to comparison view
- Re-fetches statistics for both athletes
- Updates chart with both datasets

**Removing to 1 Athlete:**
- Automatically switches from comparison to detailed view
- Shows career + filtered stats for remaining athlete
- Updates chart to show single athlete

## Backend API Changes

### `/api/athlete/<athlete_id>/statistics`

#### Request Parameters (Query String)
- `competition_type` (optional): Filter by competition type
- `category` (optional): Filter by category
- `start_date` (optional): Filter from this date (YYYY-MM-DD)
- `end_date` (optional): Filter to this date (YYYY-MM-DD)

#### Response Structure
```json
{
  "career": {
    "total_competitions": 45,
    "gold_medals": 3,
    "silver_medals": 5,
    "bronze_medals": 7,
    "avg_position": 8.5,
    "avg_percentile": 28.3,
    "top_finishes": 15,
    "recent_competitions_analyzed": 10,
    "best_score": 550,
    "best_score_competition": "Campionato Regionale 2024",
    "best_scores_by_category": {...},
    "category_breakdown": {...}
  },
  "filtered": {
    // Same structure as career, but only for filtered period
    // null if no filters applied
  },
  "athlete_id": "12345",
  "chart_data": {...}
}
```

#### Key Points
- `career`: Always present, shows all-time statistics
- `filtered`: Only present when filters are applied, shows period-specific stats
- Both use same structure for easy comparison
- Backend applies all filters (date, type, category) before calculating filtered stats

## Frontend Components

### JavaScript Functions

#### `loadStatistics(athleteId, competitionType, category, startDate, endDate)`
- Loads statistics for single athlete
- Displays career stats always
- Displays filtered stats when filters present
- Creates visually distinct cards for each section

#### `loadComparisonStatistics(athletes, competitionType, category, startDate, endDate)`
- Loads statistics for multiple athletes
- Creates comparison table
- Shows individual highlight cards
- Handles filtered vs career mode automatically

#### `analyzeResults()`
- Main analysis trigger
- Decides between single athlete vs comparison mode
- Passes filters to appropriate statistics function
- Auto-called when adding/removing athletes (if already analyzed)

### UI Updates

#### Statistics Section Layout

**Single Athlete:**
```
┌─────────────────────────────────────┐
│ Career Statistics                   │
├─────────┬─────────┬─────────┬───────┤
│  Total  │ Medals  │   Avg   │ Best  │
│  Comps  │ 🥇🥈🥉  │   Pos   │ Score │
└─────────┴─────────┴─────────┴───────┘

┌─────────────────────────────────────┐ ← Only if filters applied
│ Filtered Period Statistics          │ ← Accent colored
├─────────┬─────────┬─────────┬───────┤
│  Comps  │ Medals  │   Avg   │ Best  │
│   (F)   │ 🥇🥈🥉  │   Pos   │ Score │
└─────────┴─────────┴─────────┴───────┘
```

**Multiple Athletes:**
```
┌────────────────────────────────────────┐
│ [Career/Filtered] Statistics Comparison│
├─────────┬──────┬────┬────┬────┬───────┤
│ Athlete │Comps │ 🥇 │ 🥈 │ 🥉 │ Best  │
├─────────┼──────┼────┼────┼────┼───────┤
│ John    │  45  │ 3  │ 5  │ 7  │  550  │
│ Jane    │  38  │ 5  │ 4  │ 6  │  565  │
└─────────┴──────┴────┴────┴────┴───────┘

Individual Highlights
┌─────────────────┐ ┌─────────────────┐
│ John            │ │ Jane            │
│ Best: 550       │ │ Best: 565       │
│ Top 28%         │ │ Top 22%         │
│ 15 podiums      │ │ 18 podiums      │
└─────────────────┘ └─────────────────┘
```

## Usage Examples

### Example 1: Analyze Single Athlete with Filters
1. Search and select "John Smith"
2. Set date range: 01/01/2024 - 31/12/2024
3. Select category: "Indoor"
4. Click "Analyze"
5. **Result**: See both career Indoor stats AND 2024 Indoor stats

### Example 2: Compare Multiple Athletes
1. Search and add "John Smith"
2. Search and add "Jane Doe"
3. Search and add "Mike Brown"
4. Click "Analyze"
5. **Result**: Comparison table with all three athletes

### Example 3: Filtered Comparison
1. Add multiple athletes (as above)
2. Set competition type: "1/2 FITA"
3. Click "Analyze"
4. **Result**: Compare only their FITA performance

### Example 4: Dynamic Updates
1. Add "John Smith" and analyze
2. Add "Jane Doe" → **Auto-refresh**: switches to comparison
3. Remove "Jane Doe" → **Auto-refresh**: switches back to detailed view
4. Add "Mike Brown" → **Auto-refresh**: comparison with John and Mike

## Technical Details

### Data Flow

```
User Action (Analyze/Add/Remove Athlete)
    ↓
Frontend: analyzeResults()
    ↓
Determine: Single or Multiple Athletes?
    ↓
    ├── Single → loadStatistics(id, filters)
    │       ↓
    │       Backend: /api/athlete/{id}/statistics?filters
    │       ↓
    │       Calculate career + filtered stats
    │       ↓
    │       Display career cards + filtered cards
    │
    └── Multiple → loadComparisonStatistics(athletes, filters)
            ↓
            Backend: Multiple calls to /api/athlete/{id}/statistics?filters
            ↓
            Aggregate all statistics
            ↓
            Display comparison table + highlight cards
```

### Performance Considerations
- Each athlete requires 1 API call for statistics
- Comparing 5 athletes = 5 API calls (run in parallel)
- Results cached in browser until next analysis
- Auto-refresh only when athletes change, not when filters change alone

## Testing Checklist

### Single Athlete
- [ ] Career stats display correctly without filters
- [ ] Career + filtered stats display when date filter applied
- [ ] Career + filtered stats display when type filter applied
- [ ] Career + filtered stats display when category filter applied
- [ ] Career + filtered stats display when multiple filters combined
- [ ] Filtered section has accent color border
- [ ] Filtered section shows "Filtered" badge

### Multiple Athletes
- [ ] Comparison table displays for 2 athletes
- [ ] Comparison table displays for 3+ athletes
- [ ] Table columns align correctly
- [ ] Highlight cards show below table
- [ ] Title changes based on filter presence
- [ ] Statistics are accurate for each athlete

### Dynamic Updates
- [ ] Adding 2nd athlete switches to comparison mode
- [ ] Removing to 1 athlete switches to detailed mode
- [ ] Auto-refresh works when adding athlete
- [ ] Auto-refresh works when removing athlete
- [ ] Chart updates along with statistics
- [ ] No errors in console during transitions

## Files Modified
1. `app/routes/archery.py` - Backend statistics endpoint with filtering
2. `app/static/js/archery-analysis.js` - Frontend statistics display logic
3. Statistics now support both career and filtered views
4. Comparison mode for multiple athletes added

## Related Documentation
- `DATE_HANDLING_GUIDE.md` - Date normalization and handling
- `DATA_FLOW_ARCHITECTURE.md` - Overall system architecture
- `API_USAGE_GUIDE.md` - API endpoint documentation
