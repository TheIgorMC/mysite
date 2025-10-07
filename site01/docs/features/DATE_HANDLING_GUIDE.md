# Date Handling in Archery Analysis System

## Overview
This document explains how dates are processed throughout the archery analysis system to ensure reliable statistics and proper chart display when comparing athletes.

## The Problem
When comparing multiple athletes, dates could appear in different formats from the API (e.g., "2024-01-15", "15/01/2024", "15-01-2024"), causing:
- Incorrect chronological ordering in charts
- Misaligned data points when comparing athletes
- Statistics calculated on incorrectly sorted data
- Chart labels showing wrong or inconsistent dates

## The Solution

### 1. Backend Date Normalization (Python)

#### `app/routes/archery.py`
Added `normalize_date()` function that:
- Accepts multiple input formats: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`, etc.
- Always returns dates in standard `YYYY-MM-DD` format
- Handles ISO format dates with timezone info
- Falls back gracefully if parsing fails

```python
def normalize_date(date_str):
    """Normalize date strings to YYYY-MM-DD format"""
    if not date_str:
        return None
    
    try:
        for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y']:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Try ISO format
        date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date_obj.strftime('%Y-%m-%d')
    except (ValueError, AttributeError) as e:
        print(f"Warning: Could not parse date '{date_str}': {e}")
        return date_str  # Return original if parsing fails
```

**Applied to:**
- `/api/athlete/<athlete_id>/results` - Normalizes all result dates
- `/api/athlete/<athlete_id>/statistics` - Normalizes dates for statistics calculation

#### `app/archery_utils.py`
Added `parse_date_safely()` function for CSV operations:
- Same normalization logic as backend routes
- Used in statistics sorting and calculations
- Provides default value if parsing fails

### 2. Frontend Date Handling (JavaScript)

#### `app/static/js/archery-analysis.js`
Completely rewrote `updateChart()` function with:

**Date Normalization:**
```javascript
const normalizeDate = (dateStr) => {
    // Handles YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY formats
    // Returns normalized YYYY-MM-DD format
};
```

**Unified Timeline:**
- Collects ALL unique dates from ALL athletes
- Sorts them chronologically
- Creates a common X-axis for all datasets

**Proper Data Alignment:**
- Maps each athlete's results to the common timeline
- Uses `null` for dates where an athlete has no result
- Enables `spanGaps: true` to connect lines across missing data

**Display Formatting:**
- Shows dates as DD/MM/YYYY (Italian format) for readability
- Internal processing always uses YYYY-MM-DD for reliability

## Data Flow

```
API Response (various formats)
    ↓
Backend normalize_date() → YYYY-MM-DD
    ↓
JSON Response to Frontend
    ↓
Frontend normalizeDate() → YYYY-MM-DD (verification)
    ↓
Chronological Sorting & Alignment
    ↓
formatDateForDisplay() → DD/MM/YYYY
    ↓
Chart Display
```

## Benefits

### ✅ Accurate Comparisons
- All athletes plotted on same chronological timeline
- No misalignment of data points
- Proper chronological ordering

### ✅ Reliable Statistics
- Sorted correctly regardless of input format
- Consistent date-based filtering
- Accurate "recent competitions" analysis

### ✅ Robust Error Handling
- Multiple format support reduces parsing errors
- Graceful fallbacks prevent crashes
- Console warnings for debugging

### ✅ International Format Support
- European format: DD/MM/YYYY
- American format: MM/DD/YYYY
- ISO format: YYYY-MM-DD
- Display in Italian format for users

## Example Scenarios

### Single Athlete Analysis
**Before:** Dates might sort incorrectly if in DD/MM/YYYY format
**After:** All dates normalized and sorted properly

### Multiple Athletes Comparison
**Before:** Chart used only first athlete's dates, causing misalignment
```
Athlete A: [Jan 15, Feb 20, Mar 10]
Athlete B: [Jan 20, Feb 15, Mar 5]  ← Misaligned!
```

**After:** Unified timeline with all dates
```
Timeline:   [Jan 15, Jan 20, Feb 15, Feb 20, Mar 5, Mar 10]
Athlete A:  [  ✓   ,  null ,  null ,   ✓   , null,   ✓  ]
Athlete B:  [ null ,   ✓   ,   ✓   ,  null ,  ✓  , null ]
```

### Statistics Calculation
**Before:** "Last 10 competitions" might be wrong order due to date format
**After:** Always gets truly most recent competitions

## Testing Date Formats

The system now handles:
- ✅ `2024-01-15` (ISO format from API)
- ✅ `15/01/2024` (Italian format)
- ✅ `15-01-2024` (Alternative format)
- ✅ `2024/01/15` (Alternative ISO)
- ✅ `01/15/2024` (American format)
- ✅ `2024-01-15T10:30:00Z` (ISO with time)
- ✅ Mixed formats in same dataset

## Maintenance Notes

### Adding New Date Formats
To support additional formats, add to the format list in both:
1. `app/routes/archery.py` - `normalize_date()`
2. `app/archery_utils.py` - `parse_date_safely()`
3. `app/static/js/archery-analysis.js` - `normalizeDate()`

### Debugging Date Issues
If dates appear wrong:
1. Check browser console for "Error parsing date" messages
2. Check Python console for "Could not parse date" warnings
3. Verify API response format hasn't changed
4. Test with API_USAGE_GUIDE.md examples

## Related Files
- `app/routes/archery.py` - Backend date normalization
- `app/archery_utils.py` - CSV processing date handling
- `app/static/js/archery-analysis.js` - Frontend chart date logic
- `APIspec.json` - API date field documentation

## Performance Impact
- Minimal: Date parsing happens once per result during transformation
- Caching: Frontend normalizes dates once when building chart
- No impact on API calls or database queries
