# Gallery Item Fix - TypeError Resolution

## Issue
```
TypeError: 'title' is an invalid keyword argument for GalleryItem
```

## Root Cause
The `GalleryItem` model uses **bilingual fields** (`title_en`, `title_it`, `description_en`, `description_it`, `main_image`), but the route and form were using single-language fields (`title`, `description`, `image_path`).

## Model Structure (Correct)
```python
class GalleryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_it = db.Column(db.String(256), nullable=False)
    title_en = db.Column(db.String(256), nullable=False)
    description_it = db.Column(db.Text)
    description_en = db.Column(db.Text)
    category = db.Column(db.String(64))  # 3dprinting, electronics
    main_image = db.Column(db.String(256))  # Not image_path!
    images = db.Column(db.Text)  # JSON array
    external_url = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
```

## Changes Made

### 1. Fixed Route (`app/routes/main.py`)

**Before (Incorrect):**
```python
title = request.form.get('title')
description = request.form.get('description')

item = GalleryItem(
    title=title,              # ❌ Wrong field name
    category=category,
    description=description,   # ❌ Wrong field name
    image_path=unique_filename, # ❌ Wrong field name
    is_active=True
)
```

**After (Correct):**
```python
title_en = request.form.get('title_en', '')
title_it = request.form.get('title_it', '')
description_en = request.form.get('description_en', '')
description_it = request.form.get('description_it', '')
external_url = request.form.get('external_url', '')

# Validation
if not title_en or not title_it:
    flash('Title is required in both languages', 'error')
    return redirect(url_for('main.admin') + '#gallery')

item = GalleryItem(
    title_en=title_en,         # ✅ Correct
    title_it=title_it,         # ✅ Correct
    category=category,
    description_en=description_en,  # ✅ Correct
    description_it=description_it,  # ✅ Correct
    main_image=unique_filename,     # ✅ Correct (not image_path)
    external_url=external_url if external_url else None,
    is_active=True
)
```

### 2. Fixed Admin Form (`app/templates/admin.html`)

**Before (Incorrect):**
```html
<input type="text" name="title" required>
<textarea name="description"></textarea>
<input type="file" name="image" required>
```

**After (Correct):**
```html
<!-- Bilingual Title Fields -->
<input type="text" name="title_en" required placeholder="Project title in English">
<input type="text" name="title_it" required placeholder="Titolo del progetto in italiano">

<!-- Bilingual Description Fields -->
<textarea name="description_en" placeholder="Project description in English"></textarea>
<textarea name="description_it" placeholder="Descrizione del progetto in italiano"></textarea>

<!-- External URL (New) -->
<input type="url" name="external_url" placeholder="https://printables.com/...">

<!-- Image (Now Optional) -->
<input type="file" name="image" accept="image/*">
```

### 3. Fixed Gallery Display

**Before (Incorrect):**
```html
<img src="{{ url_for('static', filename='uploads/' + item.image_path) }}">
<h3>{{ item.title }}</h3>
```

**After (Correct):**
```html
{% if item.main_image %}
<img src="{{ url_for('static', filename='uploads/' + item.main_image) }}">
{% else %}
<div class="w-full h-48 bg-gray-200 flex items-center justify-center">
    <i class="fas fa-image text-4xl text-gray-400"></i>
</div>
{% endif %}

<h3>{{ item.title_it if session.get('language') == 'it' else item.title_en }}</h3>

{% if item.external_url %}
<a href="{{ item.external_url }}" target="_blank">
    <i class="fas fa-external-link-alt"></i>View Project
</a>
{% endif %}
```

## New Features Added

1. **Bilingual Support**: Full Italian and English translations for all gallery items
2. **External URLs**: Link to Printables, GitHub, or other external resources
3. **Optional Images**: Gallery items can be created without images
4. **Better Validation**: Checks for required bilingual fields
5. **Fallback Display**: Shows placeholder when no image is uploaded
6. **Language-Aware Display**: Shows correct language based on user preference

## Form Fields Reference

| Field Name | Required | Type | Purpose |
|-----------|----------|------|---------|
| `title_en` | Yes | text | English title |
| `title_it` | Yes | text | Italian title |
| `category` | Yes | select | 3dprinting or electronics |
| `description_en` | No | textarea | English description |
| `description_it` | No | textarea | Italian description |
| `external_url` | No | url | Link to external resource |
| `image` | No | file | Project image |

## Testing

### Test Case 1: Create Gallery Item with All Fields
```
Title (EN): "Custom Archery Target"
Title (IT): "Bersaglio da Tiro con l'Arco Personalizzato"
Category: 3dprinting
Description (EN): "3D printed archery target with custom design"
Description (IT): "Bersaglio stampato in 3D con design personalizzato"
External URL: https://printables.com/model/12345
Image: target.jpg
```

**Expected**: ✅ Item created successfully

### Test Case 2: Missing Required Field
```
Title (EN): "Test Project"
Title (IT): [empty]
Category: electronics
```

**Expected**: ❌ Error: "Title is required in both languages"

### Test Case 3: Without Image
```
Title (EN): "Open Source Project"
Title (IT): "Progetto Open Source"
Category: electronics
External URL: https://github.com/user/project
Image: [none]
```

**Expected**: ✅ Item created with placeholder image

## Database Migration

If you already have old gallery items with incorrect field names, you may need to:

1. **Option A: Drop and recreate** (if no important data):
```python
python
from app import create_app, db
app = create_app()
with app.app_context():
    db.drop_all()
    db.create_all()
```

2. **Option B: Migrate data** (if preserving data):
```python
# Create migration script to rename columns
flask db migrate -m "Fix gallery item field names"
flask db upgrade
```

## Files Modified

1. ✅ `site01/app/routes/main.py` - Fixed `add_gallery_item()` route
2. ✅ `site01/app/templates/admin.html` - Updated form and display
3. 📝 `site01/docs/GALLERY_FIX.md` - This documentation

## Status

✅ **FIXED** - Gallery items can now be added successfully with proper bilingual support

---

**Date Fixed**: October 9, 2025  
**Error Type**: TypeError  
**Severity**: High (blocking feature)  
**Resolution**: Field name mismatch corrected
