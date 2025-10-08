# Translation Testing Checklist

## Quick Test Plan

### 1. Initial Setup
- [ ] Open browser with Developer Console (F12)
- [ ] Navigate to archery analysis page
- [ ] Check console for `window.translations` object
- [ ] Run `t('common.loading')` in console - should return translation

---

## 2. Italian Language Tests

### Switch to Italian
- [ ] Click settings/language selector
- [ ] Select "Italiano (IT)"
- [ ] Page should reload

### Test Loading Messages
- [ ] Search for athlete - should see "Ricerca in corso..."
- [ ] Change category dropdown - should see "Caricamento..."
- [ ] Click "Analizza" - should see "Caricamento risultati gare..."
- [ ] Stats should show "Caricamento statistiche..."

### Test Error Messages (simulate by disconnecting)
- [ ] Trigger search error - should see Italian error message
- [ ] Trigger load error - should see Italian error message

### Test User Feedback
- [ ] Select same athlete twice - alert should be in Italian
- [ ] Try to select 6th athlete - alert should be in Italian
- [ ] Empty athlete list - should see "Nessun atleta trovato"

### Test Other Features
- [ ] Newsletter subscription success - Italian message
- [ ] Add to cart - Italian confirmation

---

## 3. English Language Tests

### Switch to English
- [ ] Click settings/language selector
- [ ] Select "English (EN)"
- [ ] Page should reload

### Test Loading Messages
- [ ] Search for athlete - should see "Searching..."
- [ ] Change category dropdown - should see "Loading..."
- [ ] Click "Analyze" - should see "Loading competition results..."
- [ ] Stats should show "Loading statistics..."

### Test Error Messages
- [ ] Trigger search error - should see English error message
- [ ] Trigger load error - should see English error message

### Test User Feedback
- [ ] Select same athlete twice - alert should be in English
- [ ] Try to select 6th athlete - alert should be in English
- [ ] Empty athlete list - should see "No athletes found"

### Test Other Features
- [ ] Newsletter subscription success - English message
- [ ] Add to cart - English confirmation

---

## 4. Console Tests

Open browser console and test:

```javascript
// Check translations loaded
console.log(window.translations);

// Test translation function
console.log(t('common.loading'));
console.log(t('messages.athlete_already_selected'));
console.log(t('errors.loading_data'));

// Test all common translations
console.log(t('common.searching'));
console.log(t('common.please_try_again'));
console.log(t('common.no_results'));

// Test all error translations
console.log(t('errors.loading_results'));
console.log(t('errors.loading_statistics'));
console.log(t('errors.loading_types'));
console.log(t('errors.searching_athletes'));

// Test all message translations
console.log(t('messages.loading_competition_results'));
console.log(t('messages.loading_statistics'));
console.log(t('messages.no_athletes_found'));
console.log(t('messages.max_athletes'));
console.log(t('messages.add_athletes_to_compare'));
```

**Expected:** All should return translated text, none should return the key itself.

---

## 5. Visual Inspection

### Italian UI
Check these elements display in Italian:
- [ ] Navigation menu
- [ ] Page headings
- [ ] Button labels
- [ ] Form labels
- [ ] Loading spinners text
- [ ] Error messages
- [ ] Alert dialogs
- [ ] Dropdown options

### English UI
Check these elements display in English:
- [ ] Navigation menu
- [ ] Page headings
- [ ] Button labels
- [ ] Form labels
- [ ] Loading spinners text
- [ ] Error messages
- [ ] Alert dialogs
- [ ] Dropdown options

---

## 6. Edge Cases

### Missing Translations
- [ ] In console, try: `t('nonexistent.key')`
- [ ] **Expected:** Should return 'nonexistent.key' (the key itself)
- [ ] **Should NOT:** Crash or show error

### Rapid Language Switching
- [ ] Switch IT → EN → IT → EN rapidly
- [ ] **Expected:** All switches work smoothly
- [ ] **Should NOT:** Mixed languages or errors

### Special Characters
- [ ] Check Italian accented characters display correctly
  - "à", "è", "é", "ì", "ò", "ù"
- [ ] Check apostrophes in Italian text
  - "l'arco", "iscrizioni all'Orion"

---

## 7. Performance

### Load Time
- [ ] Page loads quickly with translations
- [ ] No noticeable delay from translation system
- [ ] Console shows no performance warnings

### Memory
- [ ] Open DevTools → Memory tab
- [ ] Check `window.translations` size is reasonable
- [ ] No memory leaks on language switching

---

## 8. Browser Compatibility

Test in multiple browsers:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if available)
- [ ] Mobile browser

---

## 9. Mobile Testing

On mobile device:
- [ ] Loading messages readable on small screen
- [ ] Alert dialogs display properly
- [ ] Language switching works
- [ ] All translations appear correctly

---

## 10. Integration with Existing Features

### Multi-Athlete Comparison
- [ ] Select multiple athletes
- [ ] Check all loading messages translate
- [ ] Check comparison table headers translate
- [ ] Check error messages translate

### Date Filters
- [ ] Apply date range filter
- [ ] Check loading messages translate
- [ ] Check error messages translate

### Competition Type Filters
- [ ] Change competition type
- [ ] Check loading messages translate
- [ ] Check dropdown text translates

---

## Common Issues & Solutions

### Issue: English text still appears
**Check:**
1. Hard refresh browser (Ctrl+Shift+R)
2. Clear browser cache
3. Check console for JavaScript errors
4. Verify translation key exists in JSON files

### Issue: Translation shows key name
**Cause:** Key doesn't exist or misspelled
**Solution:**
1. Check exact key name in en.json/it.json
2. Check key is in window.translations
3. Check for typos in t() call

### Issue: Mixed languages
**Cause:** Page not fully reloaded after language change
**Solution:**
1. Force page reload (F5)
2. Check session language setting
3. Clear browser cache

---

## Test Results Template

```
Date: _____________
Tester: ___________
Browser: __________

✅ Italian loading messages work
✅ English loading messages work
✅ Italian error messages work
✅ English error messages work
✅ Italian alerts work
✅ English alerts work
✅ Console tests pass
✅ Visual inspection pass
✅ Edge cases handled
✅ Performance acceptable

Issues Found:
1. _______________________
2. _______________________
3. _______________________

Overall Status: ✅ PASS / ❌ FAIL
```

---

## Automated Testing (Future)

Potential automated tests to add:

```javascript
// Example test structure
describe('Internationalization', () => {
  it('should load translations on page load', () => {
    expect(window.translations).toBeDefined();
  });
  
  it('should translate common keys', () => {
    expect(t('common.loading')).not.toBe('common.loading');
  });
  
  it('should handle missing keys gracefully', () => {
    expect(t('nonexistent.key')).toBe('nonexistent.key');
  });
  
  it('should switch languages', () => {
    // Test language switching logic
  });
});
```

---

## Sign-Off

Once all tests pass:

**Tested By:** ___________________
**Date:** ___________________
**Signature:** ___________________

**Ready for Production:** ✅ YES / ❌ NO

---

## Quick Commands for Testing

```javascript
// Test all translations quickly
Object.keys(window.translations).forEach(category => {
  console.log(`\n${category}:`);
  Object.keys(window.translations[category]).forEach(key => {
    console.log(`  ${key}: ${t(category + '.' + key)}`);
  });
});

// Test missing key fallback
console.log('Missing key test:', t('this.does.not.exist'));

// Test all archery-analysis messages
['loading_competition_results', 'loading_statistics', 'no_athletes_found',
 'athlete_already_selected', 'max_athletes', 'add_athletes_to_compare']
  .forEach(key => console.log(`${key}: ${t('messages.' + key)}`));
```
