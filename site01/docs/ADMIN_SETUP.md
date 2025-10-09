# Admin Account Setup Guide

## Overview
The Orion Project doesn't create a default admin account automatically. You need to create one manually using one of the methods below.

## Method 1: Using Flask CLI (Recommended)

### Create Admin User
```bash
cd site01
flask create-admin
```

You'll be prompted for:
- Username
- Email
- Password (will be hidden)
- First name (optional)
- Last name (optional)

**Example:**
```bash
$ flask create-admin
Username: admin
Email: admin@orion-project.it
Password: ********
Repeat for confirmation: ********
First name: 
Last name: 
✅ Admin user "admin" created successfully!
   Email: admin@orion-project.it
   Admin: Yes
```

### List All Users
```bash
flask list-users
```

**Output:**
```
=== Users ===
  1. admin                 (admin@orion-project.it)           👑 ADMIN
  2. mattia                (mattia@example.com)
  3. john                  (john@example.com)                 🏹 CLUB
```

### Make Existing User Admin
```bash
flask make-admin <user_id>
```

**Example:**
```bash
$ flask make-admin 2
✅ User "mattia" is now an admin!
```

## Method 2: Using Python Script

### Run the Script
```bash
cd site01
python create_admin.py
```

**Interactive Prompts:**
```
=== Create Admin User ===

Enter admin username: admin
Enter admin email: admin@orion-project.it
Enter admin password: mySecurePassword123
Enter first name (optional): Admin
Enter last name (optional): User

✅ Admin user 'admin' created successfully!
   Email: admin@orion-project.it
   Admin: Yes

You can now log in at: http://localhost:5000/auth/login
```

## Method 3: Using Python Console

```bash
cd site01
python
```

```python
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    # Create admin user
    admin = User(
        username='admin',
        email='admin@orion-project.it',
        first_name='Admin',
        last_name='User',
        is_admin=True,
        is_club_member=False,
        preferred_language='it'
    )
    admin.set_password('your_secure_password_here')
    
    db.session.add(admin)
    db.session.commit()
    print("Admin user created!")
```

## Method 4: Docker Environment

### Using Docker Exec
```bash
# Enter the container
docker exec -it orion-flask bash

# Create admin
cd /app/site01
flask create-admin
```

### Using Docker Compose Exec
```bash
docker-compose exec web flask create-admin
```

## Admin Features

Once logged in as admin, you can access:

### Admin Panel
URL: `http://localhost:5000/admin`

**Features:**
- View all registered users
- Toggle admin status for users
- Toggle club member status
- Delete users
- View gallery items

### Admin-Only Routes
- `/admin` - Admin panel
- `/admin/toggle_admin/<user_id>` - Toggle admin status
- `/admin/toggle_club_member/<user_id>` - Toggle club member status
- `/admin/delete_user/<user_id>` - Delete user

## User Model Fields

```python
class User:
    id                  # Unique user ID
    username            # Unique username
    email               # Unique email
    password_hash       # Hashed password
    first_name          # Optional
    last_name           # Optional
    avatar              # Profile picture (default: 'default-avatar.png')
    is_admin            # Admin flag (default: False)
    is_club_member      # Club member flag (default: False)
    club_name           # Club name if member
    preferred_language  # 'it' or 'en' (default: 'it')
    created_at          # Registration timestamp
    last_login          # Last login timestamp
```

## Security Best Practices

### Strong Password Requirements
- Minimum 6 characters (enforced by script)
- Recommended: 12+ characters with mixed case, numbers, symbols
- Example: `MyStr0ng!P@ssw0rd2025`

### Production Setup
1. **Change default admin password immediately**
2. **Use environment-specific credentials**
3. **Enable HTTPS in production**
4. **Set strong SECRET_KEY in .env**

### .env Configuration
```bash
# Generate a strong secret key
python -c "import secrets; print(secrets.token_hex(32))"

# Add to .env
SECRET_KEY=your_generated_secret_key_here
```

## Troubleshooting

### Error: Username already exists
```
❌ Error: Username "admin" already exists
```
**Solution:** Choose a different username or use `flask list-users` to see existing users

### Error: Email already exists
```
❌ Error: Email "admin@example.com" already exists
```
**Solution:** Use a different email address

### Error: Module not found
```
ModuleNotFoundError: No module named 'app'
```
**Solution:** Make sure you're in the `site01` directory:
```bash
cd site01
python create_admin.py
```

### Error: Database not found
```
sqlalchemy.exc.OperationalError: no such table: users
```
**Solution:** Initialize the database first:
```bash
flask db upgrade
# or
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

## Testing Admin Access

### 1. Create Admin User
```bash
flask create-admin
```

### 2. Test Login
Visit: `http://localhost:5000/auth/login`
- Username: `admin`
- Password: `your_password`

### 3. Access Admin Panel
After login, visit: `http://localhost:5000/admin`

You should see:
- List of all users
- Admin controls (toggle admin, toggle club member, delete)
- Gallery items

### 4. Verify Admin Privileges
- Check if you can access `/admin` route
- Check if you see admin controls in the UI
- Test toggling another user's admin status

## Quick Reference

| Command | Description |
|---------|-------------|
| `flask create-admin` | Create new admin user interactively |
| `flask list-users` | List all users with roles |
| `flask make-admin <id>` | Promote user to admin |
| `python create_admin.py` | Create admin via Python script |
| `/admin` | Admin panel URL |

## Default Credentials

**⚠️ IMPORTANT:** There are **NO** default credentials. You **must** create an admin account manually using one of the methods above.

For security reasons, the application does not include any pre-configured admin accounts.

---

**Last Updated:** October 9, 2025  
**Status:** ✅ Ready for production use
