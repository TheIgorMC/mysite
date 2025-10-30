# 🔒 Locked Section Access Control - Implementation Guide

**Status:** ✅ FULLY IMPLEMENTED  
**Security Level:** HIGH  
**Last Updated:** October 30, 2025

---

## Overview

The Locked Section Access Control system provides an additional authorization layer for highly sensitive areas of the website. This is separate from:
- **Login/Authentication** - Basic user login
- **Admin Access** - Site administration privileges  
- **Club Member Access** - Archery club member features

---

## 🎯 Architecture

### Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                    AUTHORIZATION LAYERS                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Authentication (@login_required)                   │
│           ↓ User must be logged in                           │
│  Layer 2: Role-Based Access                                  │
│           ↓ Admin / Club Member / Regular User              │
│  Layer 3: Locked Section Access (@locked_section_required)   │
│           ↓ HIGHEST SECURITY - Explicit grant required      │
│  🔐 HIGHLY RESTRICTED CONTENT                               │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

**New Field Added to `users` table:**
```python
has_locked_section_access = db.Column(db.Boolean, default=False, index=True)
```

- **Type:** Boolean
- **Default:** False (deny by default)
- **Indexed:** Yes (for performance)
- **Nullable:** No

---

## 🛠️ Implementation Details

### 1. Database Model (`app/models.py`)

```python
class User(UserMixin, db.Model):
    # ... existing fields ...
    has_locked_section_access = db.Column(db.Boolean, default=False, index=True)
```

### 2. Migration Script

**File:** `site01/migrations/add_locked_section_access.py`

**Run with:**
```bash
cd site01
python migrations/add_locked_section_access.py
```

**What it does:**
- Adds the `has_locked_section_access` column
- Sets default value to False for all existing users
- Creates performance index

### 3. Access Control Decorator (`app/utils.py`)

```python
from app.utils import locked_section_required

@bp.route('/locked/secret')
@login_required
@locked_section_required
def secret_page():
    return render_template('locked/secret.html')
```

**Security Features:**
- ✅ Checks if user is authenticated first
- ✅ Then checks locked section access
- ✅ Redirects with appropriate error messages
- ✅ Prevents access by default

### 4. Admin Interface

**Location:** Admin Panel > User Management

**Features:**
- 🔒 Lock icon column in user table
- Red lock = Access granted
- Gray lock = Access denied
- Click to toggle (admin only)
- Visual feedback with color changes

### 5. API Endpoints

**Route:** `/admin/toggle_locked_section/<user_id>`
**Method:** POST
**Access:** Admin only
**Function:** Toggle locked section access for a user

```python
@bp.route('/admin/toggle_locked_section/<int:user_id>', methods=['POST'])
@login_required
def toggle_locked_section(user_id):
    """Toggle locked section access - HIGHLY RESTRICTED"""
    if not current_user.is_admin:
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)
    user.has_locked_section_access = not user.has_locked_section_access
    db.session.commit()
    
    status = 'granted' if user.has_locked_section_access else 'revoked'
    flash(f'Locked section access {status} for {user.username}', 'success')
    return redirect(url_for('main.admin'))
```

---

## 📋 Usage Guide

### For Administrators

#### Grant Access via Admin Panel
1. Log in as admin
2. Navigate to Admin Panel
3. Find user in User Management table
4. Click the lock icon (🔒) to toggle access
5. Red lock = Access granted

#### Grant Access via CLI
```bash
# When creating a new admin with locked section access
flask create-admin --locked-section

# Or list users to check status
flask list-users
# Output shows: 🔒 LOCKED badge for users with access
```

### For Developers

#### Protect a Route
```python
from flask import Blueprint
from flask_login import login_required
from app.utils import locked_section_required

bp = Blueprint('locked', __name__, url_prefix='/locked')

@bp.route('/dashboard')
@login_required
@locked_section_required
def dashboard():
    """Protected route - only accessible to authorized users"""
    return render_template('locked/dashboard.html')
```

#### Check Access in Template
```html
{% if current_user.is_authenticated and current_user.has_locked_section_access %}
    <a href="{{ url_for('locked.dashboard') }}">
        🔒 Locked Section
    </a>
{% endif %}
```

#### Check Access in Python
```python
if current_user.has_locked_section_access:
    # Allow access to sensitive data
    pass
else:
    # Deny access
    flash('Access denied', 'error')
```

---

## 🚀 Creating a Locked Section Blueprint

### Example: Creating `/locked` routes

**File:** `site01/app/routes/locked.py`

```python
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils import locked_section_required

bp = Blueprint('locked', __name__, url_prefix='/locked')

@bp.route('/')
@login_required
@locked_section_required
def index():
    """Locked section landing page"""
    return render_template('locked/index.html')

@bp.route('/dashboard')
@login_required
@locked_section_required
def dashboard():
    """Locked section dashboard"""
    return render_template('locked/dashboard.html')
```

**Register blueprint in `app/__init__.py`:**
```python
from app.routes import locked
app.register_blueprint(locked.bp)
```

**Create template:** `site01/app/templates/locked/index.html`
```html
{% extends "base.html" %}

{% block title %}Locked Section - {{ super() }}{% endblock %}

{% block content %}
<section class="py-12 bg-gray-100 dark:bg-gray-900 min-h-screen">
    <div class="container mx-auto px-4">
        <h1 class="text-4xl font-bold text-center mb-8">
            🔒 Restricted Access Area
        </h1>
        <p class="text-center text-gray-600 dark:text-gray-400">
            You have access to this highly secure section.
        </p>
    </div>
</section>
{% endblock %}
```

---

## 🔐 Security Best Practices

### ✅ DO:
- Always use `@login_required` BEFORE `@locked_section_required`
- Set `has_locked_section_access=False` as default
- Audit who has access regularly
- Use secure communication for locked section content
- Log access attempts for security monitoring

### ❌ DON'T:
- Don't grant access by default
- Don't expose locked section routes publicly
- Don't rely on this alone for critical security (use additional measures)
- Don't forget to revoke access when no longer needed

---

## 🧪 Testing

### Manual Testing Checklist

#### 1. Database Migration
```bash
cd site01
python migrations/add_locked_section_access.py
# Should see: ✓ Migration completed successfully!
```

#### 2. Admin Panel
- [ ] Log in as admin
- [ ] Navigate to Admin Panel
- [ ] Verify lock icon column appears
- [ ] Click lock icon (should toggle access)
- [ ] Verify color changes (gray ↔ red)
- [ ] Check flash message appears

#### 3. Access Control
- [ ] Create test route with `@locked_section_required`
- [ ] Try accessing as user WITHOUT access (should redirect)
- [ ] Grant access via admin panel
- [ ] Try accessing again (should work)

#### 4. CLI Commands
```bash
# Create admin with locked section access
flask create-admin --locked-section

# List users and verify 🔒 badge
flask list-users
```

---

## 📊 Status Indicators

### In Admin Panel
| Icon | Color | Meaning |
|------|-------|---------|
| 🔒 | Red | Access GRANTED |
| 🔒 | Gray | Access DENIED |

### In CLI
| Badge | Meaning |
|-------|---------|
| 🔒 LOCKED | User has locked section access |
| (none) | User does not have access |

---

## 🔄 Migration Path

### Existing Database
1. Run migration script: `python migrations/add_locked_section_access.py`
2. All existing users will have `has_locked_section_access=False`
3. Grant access to specific users via admin panel

### New Installation
- Migration runs automatically on first startup
- All users created will have `has_locked_section_access=False` by default

---

## 📝 Translation Keys

### English (`translations/en.json`)
```json
"locked_section_access": "Locked Section Access",
"locked_section_granted": "Locked section access granted for {username}",
"locked_section_revoked": "Locked section access revoked for {username}",
"locked_section_denied": "You do not have permission to access this section.",
"locked_section_title": "Restricted Access"
```

### Italian (`translations/it.json`)
```json
"locked_section_access": "Accesso Sezione Riservata",
"locked_section_granted": "Accesso alla sezione riservata concesso per {username}",
"locked_section_revoked": "Accesso alla sezione riservata revocato per {username}",
"locked_section_denied": "Non hai i permessi per accedere a questa sezione.",
"locked_section_title": "Accesso Riservato"
```

---

## 🎯 Next Steps

### To Create Your Locked Section:

1. **Create Blueprint** (see example above)
2. **Create Templates** in `templates/locked/`
3. **Register Blueprint** in `app/__init__.py`
4. **Test Access Control**
5. **Add Navigation** (only show to authorized users)

### Alternative: Separate Server with Nginx

If you need even higher security isolation:

```nginx
# Nginx configuration for separate locked server
location /locked {
    proxy_pass http://localhost:5001;  # Separate server
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Run two Flask instances:
- Port 5000: Main website
- Port 5001: Locked section (completely separate codebase)

---

## 📞 Support

For questions or issues:
1. Check this documentation
2. Review the implementation in:
   - `app/models.py` (database model)
   - `app/utils.py` (decorator)
   - `app/routes/main.py` (toggle endpoint)
   - `app/templates/admin.html` (UI)

---

**Remember:** This is a HIGH SECURITY feature. Always verify access control is working correctly before deploying sensitive content! 🔒
