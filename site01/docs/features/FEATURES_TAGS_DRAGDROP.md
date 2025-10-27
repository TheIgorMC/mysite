# New Features: Drag-and-Drop, Tags, and Archery Category

## Overview
Three major enhancements added to improve the admin experience and product organization.

## 1. 🖼️ Drag-and-Drop Image Upload

### Features
- **Click or Drag**: Click to browse files OR drag-and-drop images directly
- **Live Preview**: See image preview before uploading
- **File Validation**:
  - Only image files accepted
  - Maximum 10MB file size
  - Visual feedback for invalid files
- **Visual Feedback**: Drop zone highlights when dragging over it
- **Easy Removal**: Remove selected image with one click

### How to Use
1. Go to **Admin Panel** → **Gallery** tab
2. Scroll to "Add Gallery Item" form
3. Find the **Image** field with dashed border
4. Either:
   - **Click** anywhere in the zone to browse files
   - **Drag** an image from your computer and drop it in the zone
5. Preview appears with filename
6. Click "Remove" to clear and select different image
7. Submit form to upload

### Technical Details
```javascript
// Supported Events
- dragenter: Highlight drop zone
- dragover: Maintain highlight
- dragleave: Remove highlight
- drop: Handle file and show preview

// Validation
- File type: image/* (PNG, JPG, GIF, WebP, etc.)
- File size: Max 10MB
- Preview: Data URL for instant preview
```

### Visual States
- **Default**: Dashed border with upload icon
- **Hover**: Border becomes primary color
- **Dragging Over**: Blue highlight
- **File Selected**: Shows preview with filename
- **Invalid File**: Alert message

## 2. 🏷️ Tags System

### Features
- **Flexible Tagging**: Add multiple comma-separated tags
- **Easy Searching**: Future-ready for tag-based filtering
- **Visual Display**: Tags shown as colored badges
- **Optional Field**: No tags required, use when helpful

### Tag Examples

#### Gallery Items
```
3D Printing Tags:
- arduino, enclosure, compact, parametric
- voron, mod, toolhead, extruder
- organizer, desk, modular, honeycomb
- miniature, tabletop, terrain, dnd

Electronics Tags:
- ESP32, wifi, sensor, smart-home
- arduino, beginner, tutorial, led
- robot, motor, controller, autonomous
- power-supply, 5v, adjustable, compact
```

#### Shop Products
```
Archery Tags:
- arrows, carbon, spine-500, competition
- target, foam, 60cm, outdoor
- bow, recurve, traditional, 30lbs
- finger-tab, leather, medium, cordovan

3D Printing Tags:
- filament, PLA, 1kg, black
- nozzle, brass, 0.4mm, hardened
- bed, glass, 220x220, textured

Electronics Tags:
- microcontroller, development-board, wifi
- sensor, temperature, humidity, i2c
- display, oled, 128x64, ssd1306
```

### How to Add Tags

#### In Admin Panel
1. Go to **Gallery** or **Shop** tab
2. Find the **Tags** field
3. Enter tags separated by commas
4. Example: `arduino, led, beginner, compact`
5. Submit form

#### Tag Best Practices
- **Be specific**: `ESP32` better than `microcontroller`
- **Use lowercase**: Consistent formatting
- **Separate words**: Use hyphens for multi-word tags (`smart-home`, not `smart home`)
- **Think searchable**: What would users search for?
- **5-10 tags**: Not too few, not too many
- **Include synonyms**: `3d-print, printing, 3dp`

### Tag Display
```html
<!-- Tags appear as colored badges -->
<span class="badge">arduino</span>
<span class="badge">sensor</span>
<span class="badge">ESP32</span>
```

### Database Structure
```python
# Products
tags = db.Column(db.Text)  # "arduino, led, sensor, esp32"

# Gallery Items
tags = db.Column(db.Text)  # "voron, mod, extruder, toolhead"
```

### Future Enhancements
- Tag autocomplete from existing tags
- Tag-based search/filtering
- Popular tags sidebar
- Tag cloud visualization
- Click tag to filter by that tag

## 3. 🏹 Archery Category in Shop

### Features
- **New Category**: Archery added to shop categories
- **Consistent UI**: Same style as other categories
- **Mobile Support**: Dropdown includes archery option
- **Bilingual**: Translation support via `t('shop.archery')`

### Category List
Now supporting **4 categories**:
1. **All** - Show all products
2. **Archery** - Bows, arrows, targets, accessories
3. **3D Printing** - Filament, parts, tools, upgrades
4. **Electronics** - Components, boards, sensors, kits

### URL Structure
```
/shop?category=all          # All products
/shop?category=archery      # Archery products only
/shop?category=3dprinting   # 3D printing products
/shop?category=electronics  # Electronics products
```

### Example Archery Products
```
Products:
- Carbon Arrows (Set of 12) - €45.00
- Recurve Bow Riser (25") - €120.00
- Target Face (60cm) - €12.00
- Finger Tab (Leather) - €18.00
- Arrow Rest (Magnetic) - €25.00
- Bowstring (Custom Length) - €15.00
```

## Implementation Details

### Files Modified

#### 1. Models (`app/models.py`)
```python
# Product model
tags = db.Column(db.Text)  # Added

# GalleryItem model  
tags = db.Column(db.Text)  # Added
```

#### 2. Routes (`app/routes/main.py`)
```python
def add_gallery_item():
    # ...
    tags = request.form.get('tags', '')
    # ...
    item = GalleryItem(
        # ...
        tags=tags.strip() if tags else None,
        # ...
    )
```

#### 3. Admin Template (`app/templates/admin.html`)
```html
<!-- Tags Input -->
<input type="text" name="tags" placeholder="arduino, led, sensor">

<!-- Drag-and-Drop Zone -->
<div id="gallery-drop-zone" class="border-2 border-dashed...">
    <input type="file" id="gallery-image-input" class="hidden">
    <!-- Drop zone content -->
</div>

<!-- Tags Display -->
{% for tag in item.tags.split(',') %}
    <span class="badge">{{ tag.strip() }}</span>
{% endfor %}

<!-- JavaScript -->
<script>
    // Drag-and-drop handlers
    // File validation
    // Preview generation
</script>
```

#### 4. Shop Template (`app/templates/shop/index.html`)
```html
<!-- Archery category already present -->
<a href="{{ url_for('shop.index', category='archery') }}">
    {{ t('shop.archery') }}
</a>
```

## Database Migration

After updating models, run migration:

```bash
# Option 1: Auto-migration
cd site01
flask db migrate -m "Add tags to products and gallery items"
flask db upgrade

# Option 2: Manual (if no flask-migrate)
python
from app import create_app, db
app = create_app()
with app.app_context():
    from sqlalchemy import text
    db.session.execute(text('ALTER TABLE products ADD COLUMN tags TEXT'))
    db.session.execute(text('ALTER TABLE gallery_items ADD COLUMN tags TEXT'))
    db.session.commit()
```

## Testing

### Test Drag-and-Drop
1. ✅ Click zone to browse files
2. ✅ Drag image from desktop to zone
3. ✅ See preview with filename
4. ✅ Remove and try different image
5. ✅ Submit form with image
6. ✅ Try invalid file (PDF, MP3) - see error
7. ✅ Try large file (>10MB) - see error

### Test Tags
1. ✅ Add gallery item without tags (optional)
2. ✅ Add item with single tag
3. ✅ Add item with multiple tags: `arduino, led, sensor`
4. ✅ View item - see tags as badges
5. ✅ Add product with tags
6. ✅ View product - see tags

### Test Archery Category
1. ✅ Go to shop page
2. ✅ See 4 category buttons (desktop)
3. ✅ See 4 options in dropdown (mobile)
4. ✅ Click "Archery" - filter works
5. ✅ Add product with category="archery"
6. ✅ Verify it appears in archery filter

## Browser Compatibility

### Drag-and-Drop
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ⚠️ IE11: Fallback to click only (no drag)

### File API
- ✅ All modern browsers
- ✅ FileReader for preview
- ✅ DataTransfer for drag-and-drop

## Keyboard Accessibility

- **Tab**: Navigate to drop zone
- **Enter/Space**: Open file picker (when focused)
- **Esc**: Clear preview (future enhancement)

## Mobile Experience

### Drag-and-Drop
- On mobile: Tap to browse files (drag not available)
- Works with native file picker
- Preview still shows

### Tags
- Easy to type on mobile keyboard
- Consider autocomplete for future

### Categories
- Dropdown menu on mobile (already implemented)
- Easy thumb-friendly tapping

## Performance

- **Image Preview**: Instant (Data URL, no upload)
- **File Validation**: Client-side (no server round-trip)
- **Tag Storage**: Text field (minimal space)
- **Query**: Add index for faster tag searches

```sql
-- Future optimization
CREATE INDEX idx_products_tags ON products(tags);
CREATE INDEX idx_gallery_tags ON gallery_items(tags);
```

## Security

- **File Type Validation**: Client + Server side
- **File Size Limit**: 10MB enforced
- **XSS Protection**: Tags are escaped in template
- **CSRF Protection**: Flask forms (built-in)

## Future Roadmap

### Phase 2 (Next Updates)
- [ ] Tag autocomplete from existing tags
- [ ] Click tag to filter
- [ ] Tag-based search
- [ ] Popular tags widget

### Phase 3 (Advanced)
- [ ] Tag recommendations
- [ ] Multi-tag filtering (AND/OR)
- [ ] Tag synonyms (e.g., "3dp" = "3d-printing")
- [ ] Tag hierarchy/categories

---

**Date Implemented**: October 9, 2025  
**Status**: ✅ Ready for production  
**Breaking Changes**: None (backward compatible)
