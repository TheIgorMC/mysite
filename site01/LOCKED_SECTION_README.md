# 🔒 Locked Section - Quick Start

## What Was Added

A complete access control system for highly restricted content, with:
- ✅ Database field: `has_locked_section_access`
- ✅ Security decorator: `@locked_section_required`
- ✅ Admin UI with lock icon toggle
- ✅ CLI support for granting access
- ✅ Template blueprint with examples
- ✅ Full documentation

## Quick Setup (3 Steps)

### 1. Run Migration
```bash
cd site01
python migrations/add_locked_section_access.py
```

### 2. Enable Blueprint (Optional)
To activate the demo locked section, edit `site01/app/__init__.py`:

```python
# Find this section (around line 54):
from app.routes import main, auth, archery, printing, electronics, shop, admin, api_routes, api

# Add locked to the import:
from app.routes import main, auth, archery, printing, electronics, shop, admin, api_routes, api, locked

# Then find this section (around line 64):
app.register_blueprint(api.bp)  # Website-level API

# Add below it:
app.register_blueprint(locked.bp)  # Locked section (RESTRICTED)
```

### 3. Grant Access
```bash
# Via CLI when creating admin:
flask create-admin --locked-section

# Or via Admin Panel:
# 1. Log in as admin
# 2. Go to Admin Panel
# 3. Click lock icon next to user
```

## File Structure

```
site01/
├── app/
│   ├── models.py                    # ✅ User.has_locked_section_access added
│   ├── utils.py                     # ✅ @locked_section_required decorator
│   ├── routes/
│   │   ├── main.py                  # ✅ toggle_locked_section endpoint
│   │   └── locked.py                # ✅ Demo blueprint (template)
│   └── templates/
│       ├── admin.html               # ✅ Lock icon in user table
│       └── locked/                  # ✅ Demo templates
│           ├── index.html
│           ├── dashboard.html
│           └── settings.html
├── migrations/
│   └── add_locked_section_access.py # ✅ Migration script
├── translations/
│   ├── en.json                      # ✅ Translations added
│   └── it.json                      # ✅ Translations added
└── docs/
    └── LOCKED_SECTION_GUIDE.md      # ✅ Full documentation
```

## Usage Examples

### Protect a Route
```python
from flask_login import login_required
from app.utils import locked_section_required

@bp.route('/secret')
@login_required
@locked_section_required
def secret_page():
    return render_template('secret.html')
```

### Check Access in Template
```html
{% if current_user.has_locked_section_access %}
    <a href="{{ url_for('locked.index') }}">🔒 Locked Section</a>
{% endif %}
```

### Check Access in Python
```python
if current_user.has_locked_section_access:
    # Allow access
    pass
```

## Testing

1. **Visit Admin Panel** - See lock icon in user list ✓
2. **Toggle Access** - Click lock to grant/revoke ✓
3. **Visit Demo** - Go to `/locked` after enabling blueprint ✓
4. **Test Decorator** - Try accessing without permission ✓

## Security Notes

⚠️ **IMPORTANT:**
- Access is **DENIED by default** for all users
- Only **admins** can grant access
- Always use `@login_required` **BEFORE** `@locked_section_required`
- This is separate from admin/club member access
- Consider running on separate server for maximum isolation

## Demo Pages (After Enabling)

- `/locked` - Landing page
- `/locked/dashboard` - Sample dashboard
- `/locked/settings` - Sample settings
- `/locked/api/data` - Protected API endpoint

## Next Steps

1. ✅ **Migration done?** Run the script
2. ✅ **UI working?** Check admin panel
3. 🔧 **Customize** the demo blueprint for your needs
4. 🚀 **Deploy** with confidence!

## Full Documentation

See `docs/LOCKED_SECTION_GUIDE.md` for:
- Complete security model
- Architecture diagrams
- Code examples
- Best practices
- Troubleshooting

---

**Status:** Ready to use! 🎉  
**Security:** HIGH 🔒  
**Complexity:** Low ⭐⭐⭐
