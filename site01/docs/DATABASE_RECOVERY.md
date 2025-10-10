# 🚨 Database Recovery Guide - Orange Pi Server

## Problem: Database Missing or Corrupted

If your database got deleted/nuked on the Orange Pi, here's how to recover.

---

## 🔍 Step 1: Diagnose the Problem

### On Orange Pi (via SSH):

```bash
cd /path/to/your/site01  # Update with your actual path

# Check if database exists
ls -lh instance/site.db

# If it exists, check size
du -h instance/site.db

# Check when it was modified
stat instance/site.db
```

### Common Issues:
- ❌ **File not found** → Database was deleted
- ❌ **Size: 0 KB** → Database was corrupted/wiped
- ❌ **Old modification date** → Database hasn't been updated (app not writing)

---

## 🛠️ Step 2: Run Diagnostic Script

### Copy the check script to server:

```bash
# On your local machine
scp site01/check_db.sh user@orangepi:/path/to/site01/

# On Orange Pi
cd /path/to/site01
chmod +x check_db.sh
bash check_db.sh
```

This will:
- ✅ Check if database file exists
- ✅ Test database connection
- ✅ Count users and admins
- ✅ Create a backup (if database exists)
- ✅ List available backups

---

## 💾 Step 3: Recovery Options

### Option A: Restore from Backup (BEST if you have backups)

```bash
cd /path/to/site01

# List available backups
ls -lh instance/backups/

# Restore from latest backup
cp instance/backups/site_backup_YYYYMMDD_HHMMSS.db instance/site.db

# Verify
python3 db_recovery.py  # Choose option 1 to check status
```

### Option B: Recreate Database from Scratch

```bash
cd /path/to/site01

# Activate virtual environment (if you have one)
source venv/bin/activate  # or source .venv/bin/activate

# Run all migrations
python3 migrations/add_authorized_athletes.py

# Create admin user
python3 create_admin.py

# Verify
python3 db_recovery.py
```

### Option C: Use Recovery Utility (Interactive)

```bash
cd /path/to/site01
python3 db_recovery.py
```

Menu options:
1. **Check Database Status** - See what's wrong
2. **Create Backup** - Backup current state
3. **List Backups** - See available backups
4. **Restore from Backup** - Restore from a backup file
5. **Recreate Tables** - Nuclear option (loses all data)

---

## 🔐 Step 4: Recreate Admin User

If you restored/recreated but have no admin:

```bash
cd /path/to/site01
python3 create_admin.py
```

Or manually via SQLite:

```bash
sqlite3 instance/site.db

-- Make existing user admin
UPDATE users SET is_admin = 1 WHERE username = 'your_username';

-- Check it worked
SELECT id, username, email, is_admin FROM users;

-- Exit
.quit
```

---

## 🔄 Step 5: Restart Services

```bash
# Restart Flask app (depends on your setup)

# If using systemd:
sudo systemctl restart mysite

# If using screen/tmux:
# Kill the running process and restart
pkill -f "python.*run.py"
cd /path/to/site01
python3 run.py

# If using gunicorn:
pkill gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

---

## 📋 Preventive Measures

### 1. Set up Automatic Backups

Create a cron job to backup daily:

```bash
# Edit crontab
crontab -e

# Add this line (backup every day at 2 AM)
0 2 * * * cd /path/to/site01 && python3 -c "from db_recovery import create_backup; create_backup()"
```

### 2. Check Disk Space

```bash
# Check available space
df -h

# Check if /tmp is full (SQLite uses temp files)
df -h /tmp
```

Low disk space can cause database corruption!

### 3. Check File Permissions

```bash
cd /path/to/site01

# Database file should be writable by Flask app user
ls -l instance/site.db

# If wrong, fix permissions
chmod 644 instance/site.db
chown your_user:your_user instance/site.db
```

### 4. Monitor Database Health

Add this to your monitoring script:

```bash
#!/bin/bash
# Save as check_db_health.sh

DB_FILE="/path/to/site01/instance/site.db"

if [ ! -f "$DB_FILE" ]; then
    echo "CRITICAL: Database file missing!"
    # Send alert (email, Discord, etc.)
    exit 1
fi

DB_SIZE=$(stat -c%s "$DB_FILE")
if [ $DB_SIZE -lt 10000 ]; then
    echo "WARNING: Database file is too small ($DB_SIZE bytes)"
    exit 1
fi

echo "OK: Database file exists and has data"
```

Run it periodically:
```bash
crontab -e
*/30 * * * * /path/to/check_db_health.sh
```

---

## 🐛 Common Causes of Database Loss

### 1. Disk Full
- **Check**: `df -h`
- **Fix**: Clean up space, increase disk size

### 2. Improper Shutdown
- **Issue**: Server crashed, database file corrupted
- **Fix**: Always use proper shutdown (`shutdown -h now`)

### 3. Permission Issues
- **Check**: `ls -l instance/site.db`
- **Fix**: `chmod 644 instance/site.db`

### 4. Multiple Flask Instances
- **Issue**: Two Flask apps trying to use same database
- **Fix**: Check for multiple processes: `ps aux | grep "python.*run.py"`

### 5. Code Error During Migration
- **Issue**: Migration script failed mid-way
- **Fix**: Restore from backup, fix migration, re-run

### 6. Accidental Deletion
- **Issue**: `rm` command or deployment script deleted it
- **Fix**: Check deployment scripts, restore from backup

---

## 📞 Emergency Recovery Checklist

- [ ] SSH into Orange Pi
- [ ] Check if database file exists (`ls -lh instance/site.db`)
- [ ] Check disk space (`df -h`)
- [ ] Check if app is running (`ps aux | grep python`)
- [ ] Check logs (`tail -f /var/log/mysite.log` or wherever logs are)
- [ ] Run diagnostic script (`bash check_db.sh`)
- [ ] List backups (`ls -lh instance/backups/`)
- [ ] Restore from latest backup
- [ ] Verify admin user exists
- [ ] Restart Flask app
- [ ] Test login at website

---

## 🔧 Quick Commands Reference

```bash
# Check database
sqlite3 instance/site.db "SELECT COUNT(*) FROM users;"

# Create backup manually
cp instance/site.db instance/backups/manual_backup_$(date +%Y%m%d).db

# Restore backup
cp instance/backups/BACKUP_FILE.db instance/site.db

# Check Flask can access DB
python3 -c "from app import create_app, db; app = create_app(); app.app_context().push(); from app.models import User; print(f'Users: {User.query.count()}')"

# Make user admin
sqlite3 instance/site.db "UPDATE users SET is_admin = 1 WHERE username = 'USERNAME';"

# Check disk space
df -h

# Check app logs
journalctl -u mysite -n 50  # if using systemd
tail -100 /var/log/mysite.log  # if logging to file
```

---

## ✅ Verification After Recovery

1. **Test database access**:
   ```bash
   python3 db_recovery.py  # Option 1
   ```

2. **Test website**:
   - Open browser → `http://your-orangepi-ip:5000`
   - Try to login
   - Check admin panel

3. **Test athlete management**:
   - Login as admin
   - Go to `/admin/manage-athletes`
   - Try to add an athlete

4. **Check authorized athletes**:
   ```bash
   sqlite3 instance/site.db "SELECT COUNT(*) FROM authorized_athletes;"
   ```

---

## 📝 Post-Recovery Actions

1. ✅ Set up automatic backups (cron job)
2. ✅ Document what caused the issue
3. ✅ Fix the root cause (disk space, permissions, etc.)
4. ✅ Test recovery procedure
5. ✅ Update documentation

---

**Need help?** Check the logs first:
```bash
tail -100 /var/log/syslog | grep python
journalctl -u mysite --since "1 hour ago"
```

Good luck with the recovery! 🚀
