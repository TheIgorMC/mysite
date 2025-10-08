# Internationalization (i18n) System

## Overview

The Orion Project implements a complete bilingual system supporting English (EN) and Italian (IT), with Italian as the preferred default language. All user-facing text uses the translation system to ensure consistent language support across the application.

## Translation Files

Translation data is stored in JSON files:

- **Location**: `site01/translations/`
- **English**: `en.json`
- **Italian**: `it.json`

### Structure

```json
{
  "category": {
    "key": "Translation text"
  }
}
```

### Main Categories

1. **site** - Site title and tagline
2. **nav** - Navigation menu items
3. **home** - Homepage content
4. **archery** - Archery section
5. **competitions** - Competition management
6. **printing** - 3D printing section
7. **electronics** - Electronics section
8. **shop** - Shop and cart
9. **auth** - Authentication forms
10. **footer** - Footer content
11. **common** - Common UI elements
12. **errors** - Error messages
13. **messages** - User feedback messages

## Backend (Python/Flask)

### Using Translations in Templates

Use the `t()` function in Jinja2 templates:

```html
<h1>{{ t('site.title') }}</h1>
<p>{{ t('archery.analysis_desc') }}</p>
<button>{{ t('common.save') }}</button>
```

### Using Translations in Python Code

Import and use the translation utility:

```python
from app.utils import t

message = t('errors.loading_data')
```

## Frontend (JavaScript)

### Translation Object

Translations are injected into JavaScript via the `base.html` template:

```javascript
window.translations = {
    common: { loading: "Loading...", ... },
    errors: { loading_data: "Error loading data", ... },
    messages: { newsletter_success: "Successfully subscribed!", ... }
};
```

### Using Translations in JavaScript

Use the global `t()` function:

```javascript
// Simple usage
showLoading(element, t('common.loading'));
alert(t('messages.athlete_already_selected'));

// With concatenation
const errorMsg = `${t('errors.loading_results')}. ${t('common.please_try_again')}`;
showError(element, errorMsg);

// In template literals
element.innerHTML = `<p>${t('messages.no_athletes_found')}</p>`;
```

## Adding New Translations

### Step 1: Add to Translation Files

Add the key to both `en.json` and `it.json`:

**en.json:**
```json
{
  "messages": {
    "new_key": "English text"
  }
}
```

**it.json:**
```json
{
  "messages": {
    "new_key": "Testo italiano"
  }
}
```

### Step 2: Add to Base Template (for JavaScript)

If the translation will be used in JavaScript, add it to `base.html`:

```html
<script>
    window.translations = {
        messages: {
            new_key: "{{ t('messages.new_key') }}"
        }
    };
</script>
```

### Step 3: Use in Code

**In Templates:**
```html
{{ t('messages.new_key') }}
```

**In JavaScript:**
```javascript
t('messages.new_key')
```

## Common Translation Keys

### Loading States

- `common.loading` - "Loading..."
- `common.searching` - "Searching..."
- `messages.loading_competition_results` - "Loading competition results..."
- `messages.loading_statistics` - "Loading statistics..."

### Error Messages

- `errors.loading_data` - "Error loading data"
- `errors.loading_results` - "Error loading results"
- `errors.loading_statistics` - "Error loading statistics"
- `common.please_try_again` - "Please try again."

### User Feedback

- `messages.athlete_already_selected` - "Athlete already selected"
- `messages.max_athletes` - "Maximum 5 athletes can be compared"
- `messages.no_athletes_found` - "No athletes found"
- `messages.newsletter_success` - "Successfully subscribed to newsletter!"

### UI Elements

- `common.save` - "Save"
- `common.cancel` - "Cancel"
- `common.delete` - "Delete"
- `common.close` - "Close"

## Language Switching

### User Preference

Language selection is managed through the settings menu and stored in the session:

```python
session['language'] = 'it'  # or 'en'
```

### Default Language

Italian (IT) is the default language as specified in `specifications.md`.

## Best Practices

### 1. Never Hardcode Text

❌ **Bad:**
```javascript
alert('Athlete already selected');
showLoading(element, 'Loading...');
```

✅ **Good:**
```javascript
alert(t('messages.athlete_already_selected'));
showLoading(element, t('common.loading'));
```

### 2. Consistent Key Naming

- Use dot notation: `category.subcategory.key`
- Use snake_case for keys: `athlete_already_selected`
- Group related translations in the same category

### 3. Context-Specific Messages

Create specific keys for different contexts rather than reusing generic messages:

```json
{
  "messages": {
    "loading_competition_results": "Loading competition results...",
    "loading_statistics": "Loading statistics...",
    "loading_types": "Loading types..."
  }
}
```

### 4. Avoid HTML in Translations

Keep HTML in code, only translate text content:

❌ **Bad:**
```json
{
  "message": "<p class='error'>Error occurred</p>"
}
```

✅ **Good:**
```json
{
  "message": "Error occurred"
}
```

Then in code:
```javascript
element.innerHTML = `<p class='error'>${t('message')}</p>`;
```

## Testing Translations

### 1. Test Both Languages

Always verify translations work in both EN and IT:

1. Switch to Italian in settings
2. Navigate through features
3. Switch to English
4. Verify all text changes properly

### 2. Check Dynamic Content

Pay special attention to:
- Loading messages
- Error messages
- Alert dialogs
- Dynamically generated HTML

### 3. Verify JavaScript Integration

Check browser console for:
- Translation function availability
- Correct translation loading
- Missing translation keys (will return the key itself)

## Troubleshooting

### Issue: Translations Not Showing

**Check:**
1. Is the key present in both `en.json` and `it.json`?
2. Is the key added to `window.translations` in `base.html`?
3. Is the `t()` function being called correctly?

### Issue: English Text Still Appears

**Verify:**
1. All hardcoded strings are replaced with `t()` calls
2. JavaScript files use the global `t()` function
3. Templates use `{{ t() }}` syntax

### Issue: Key Name Appears Instead of Translation

**Cause:** The translation key doesn't exist or is misspelled

**Solution:**
1. Check the exact key name in translation files
2. Verify the key is added to `window.translations`
3. Check for typos in the key name

## Files Modified for i18n

### Translation Files
- `site01/translations/en.json`
- `site01/translations/it.json`

### Templates
- `site01/app/templates/base.html` - Translation injection

### JavaScript Files
- `site01/app/static/js/main.js` - Core utilities
- `site01/app/static/js/archery-analysis.js` - Archery features

### Documentation
- `site01/docs/features/internationalization.md` - This file

## Future Enhancements

Potential improvements to the i18n system:

1. **Automatic Translation Loading** - Load translations via API instead of template injection
2. **Language Detection** - Detect user browser language preference
3. **Additional Languages** - Support for more languages
4. **Translation Management UI** - Admin interface for managing translations
5. **Pluralization Support** - Handle singular/plural forms automatically
6. **Date/Number Formatting** - Locale-specific formatting
