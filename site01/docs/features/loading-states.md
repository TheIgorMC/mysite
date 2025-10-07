# Loading States Implementation

## Overview
All API calls in the archery analysis system now feature visual loading indicators to provide feedback during data fetching operations.

## Loading Indicator Design

### Visual Elements
- **Animated Spinner**: CSS-based rotating border animation
- **Loading Message**: Contextual text indicating what's loading
- **Dark Mode Support**: Automatically adapts colors for dark theme
- **Non-blocking**: Users can see loading state while waiting

### Component Appearance
```
┌─────────────────────────────┐
│                             │
│    ╭─────────╮             │
│    │   ⟳    │  ← Spinning │
│    ╰─────────╯    circle   │
│                             │
│    Loading...               │
│                             │
└─────────────────────────────┘
```

## Loading Functions

### Core Functions (`main.js`)

#### `showLoading(element, message = 'Loading...')`
Displays loading spinner with custom message.

```javascript
showLoading(chartContainer, 'Loading competition results...');
```

**Features:**
- Dark mode aware
- Customizable message
- Centered layout
- Accessible markup

#### `hideLoading(element)`
Placeholder function - content should be immediately replaced when ready.

#### `showError(element, message)`
Displays error message with icon.

```javascript
showError(container, 'Error loading data. Please try again.');
```

**Features:**
- Dark mode support
- Error icon
- Clear messaging
- Proper contrast

## Loading States by Feature

### 1. Athlete Search
**Trigger**: User types in search box (3+ characters)

**Loading State:**
- Small inline spinner
- "Searching..." message
- Appears in search results dropdown

**Duration**: 100-500ms (API dependent)

**Implementation:**
```javascript
resultsDiv.innerHTML = `
    <div class="p-4 flex items-center justify-center">
        <div class="w-6 h-6 border-2 ... animate-spin mr-2"></div>
        <span>Searching...</span>
    </div>
`;
```

### 2. Category Change
**Trigger**: User selects a category

**Loading State:**
- "Loading..." in competition type dropdown
- Dropdown disabled during load
- Automatically re-enabled when complete

**Duration**: 50-200ms (local operation)

**Implementation:**
```javascript
typeSelect.innerHTML = '<option value="">Loading...</option>';
typeSelect.disabled = true;
// ... fetch data ...
typeSelect.disabled = false;
```

### 3. Competition Results Analysis
**Trigger**: User clicks "Analyze" button

**Loading State:**
- Large spinner in chart area
- "Loading competition results..." message
- Statistics area shows "Loading statistics..." 
- Both areas load in parallel

**Duration**: 500-2000ms (depending on athlete count and filters)

**Implementation:**
```javascript
showLoading(chartContainer, 'Loading competition results...');
showLoading(statsGrid, 'Loading statistics...');
// ... fetch and process data ...
// Replace with actual content
```

### 4. Statistics Loading
**Trigger**: After chart loads OR when athletes added/removed

**Loading State:**
- Spinner in statistics section
- "Loading statistics..." message
- Statistics section visible during load

**Duration**: 200-1000ms (API dependent)

### 5. Comparison Statistics
**Trigger**: Multiple athletes analyzed simultaneously

**Loading State:**
- Single loading indicator
- "Loading statistics..." message
- Parallel API calls in background

**Duration**: 500-2000ms (N athletes = N API calls)

## Error Handling

### Error Display
When API call fails:
```
┌─────────────────────────────┐
│ ⚠️ Error loading data       │
│    Please try again.        │
└─────────────────────────────┘
```

**Features:**
- Warning icon
- Clear error message
- Action suggestion
- Red color scheme (adapts to dark mode)

### Auto-Recovery
Some errors auto-recover:
- Category type loading: Reverts to "All Types" after 2s
- Others: Persist until user retries

## CSS Implementation

### Spinner Animation
```css
.animate-spin {
    animation: spin 1s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
```

### Border Style
- 4px border width
- Gray background color
- Primary color for rotating section
- Rounded full circle

### Colors by Theme

| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Background | border-gray-200 | border-gray-700 |
| Accent | border-t-primary | border-t-primary |
| Text | text-gray-700 | text-gray-300 |
| Error BG | bg-red-100 | bg-red-900/30 |
| Error Text | text-red-700 | text-red-300 |

## User Experience

### Loading Flow

#### Quick Operations (<200ms)
```
User Action → [Brief Flash] → Result
```
Loading indicator may be barely visible - acceptable.

#### Medium Operations (200-1000ms)
```
User Action → [Spinner 0.5s] → Result
```
Clear feedback that system is working.

#### Long Operations (>1000ms)
```
User Action → [Spinner + Message] → Result
```
Message provides context about what's loading.

### Best Practices
1. **Show immediately**: Display loading state as soon as action triggered
2. **Be specific**: Use contextual messages ("Loading results..." not just "Loading...")
3. **Replace completely**: When done, replace entire loading element with content
4. **Handle errors gracefully**: Show clear error messages with recovery options

## Accessibility

### Screen Reader Support
```html
<div role="status" aria-live="polite" aria-label="Loading data">
    <div class="spinner" aria-hidden="true"></div>
    <span>Loading...</span>
</div>
```

### Keyboard Navigation
- Loading states don't trap focus
- Disabled controls (e.g., dropdown during load) skip in tab order
- Error messages are readable by screen readers

### Reduced Motion
For users with `prefers-reduced-motion`:
```css
@media (prefers-reduced-motion: reduce) {
    .animate-spin {
        animation: none;
        opacity: 0.6;
    }
}
```

## Performance Considerations

### Debouncing
Athlete search includes natural debouncing:
- Only triggers on 3+ characters
- Each keystroke restarts the search
- Browser naturally throttles rapid API calls

### Parallel Loading
When analyzing multiple athletes:
- All athlete results fetched in parallel
- Chart displays as soon as first athlete ready
- Statistics aggregate when all complete

### Caching
- Competition types: Loaded once on page load
- Categories: Loaded once on page load
- Results: Fresh on each analysis (no caching)

## Testing

### Test Scenarios

#### 1. Search Loading
```
1. Type 3 characters in search
2. Verify spinner appears
3. Verify results replace spinner
4. Repeat with invalid name
5. Verify "No athletes found" message
```

#### 2. Analysis Loading
```
1. Select athlete
2. Click Analyze
3. Verify chart shows loading
4. Verify statistics show loading
5. Verify both complete
6. Add second athlete
7. Verify auto-refresh shows loading
```

#### 3. Error Handling
```
1. Disconnect network
2. Try to search athlete
3. Verify error message appears
4. Reconnect network
5. Retry - verify recovery
```

#### 4. Dark Mode
```
1. Start in light mode
2. Trigger loading
3. Switch to dark mode during load
4. Verify colors adapt correctly
```

## Browser Compatibility

### Supported Browsers
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

### Fallbacks
- CSS animations gracefully degrade
- Spinners work without JavaScript (pure CSS)
- Messages remain readable if styles fail

## Future Enhancements

### Potential Improvements
1. **Progress Indicators**: Show % complete for multi-athlete loads
2. **Skeleton Screens**: Show placeholder content instead of spinners
3. **Optimistic Updates**: Display previous results while loading new ones
4. **Cancel Actions**: Allow users to cancel long-running operations
5. **Retry Buttons**: Built-in retry for failed operations

## Related Files
- `app/static/js/main.js` - Core loading functions
- `app/static/js/archery-analysis.js` - Feature-specific implementations
- `app/templates/archery/analysis.html` - Container elements

## Documentation
- Loading states added to all API operations
- Contextual messages for different operations
- Error handling with recovery options
- Full dark mode support
