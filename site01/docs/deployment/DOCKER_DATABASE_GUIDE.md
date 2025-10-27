# Docker Database Location Guide

## The Mystery Solved! 🔍

Your database **DOES exist**, but it's hidden inside a Docker volume!

### Where is the database?

1. **Inside the container**: `/app/data/orion.db`
2. **On the Orange Pi host**: In Docker's volume storage (typically `/var/lib/docker/volumes/mysite_orion-data/_data/`)
3. **That's why `find` didn't find it** - it's not in the normal filesystem!

---

## Quick Commands for Orange Pi

### Check if container is running
```bash
docker ps | grep orion-project
```

### Find the database file
```bash
# Inside container
docker exec orion-project ls -lh /app/data/orion.db

# Find the volume location on host
docker volume inspect orion-data | grep Mountpoint
```

### Check database has data
```bash
# Count users
docker exec orion-project python -c "
from app import create_app
from app.models import User
app = create_app('production')
with app.app_context():
    print(f'Total users: {User.query.count()}')
    print(f'Admin users: {User.query.filter_by(is_admin=True).count()}')
"
```

### Create a backup
```bash
# Quick backup to current directory
docker cp orion-project:/app/data/orion.db ./orion_backup_$(date +%Y%m%d).db

# Or use docker exec
docker exec orion-project cat /app/data/orion.db > orion_backup.db
```

### Access database directly
```bash
# Open SQLite shell inside container
docker exec -it orion-project sqlite3 /app/data/orion.db

# Inside SQLite shell:
# .tables          - List all tables
# .schema users    - Show users table structure
# SELECT * FROM users;  - List all users
# .quit            - Exit
```

### View container logs
```bash
docker logs orion-project --tail 50
docker logs orion-project -f  # Follow logs in real-time
```

---

## Using the Recovery Tools

### Option 1: Interactive Python Tool
```bash
cd /path/to/mysite/site01
python docker_db_recovery.py
```

Features:
- Check database status
- Create backups
- Restore from backup
- Recreate database
- Create admin users
- All with confirmation prompts!

### Option 2: Bash Health Check Script
```bash
cd /path/to/mysite/site01
chmod +x check_docker_db.sh
./check_docker_db.sh
```

Features:
- Automatic health check
- Creates backup automatically
- Shows all database stats
- Lists recent backups

---

## Common Scenarios

### Scenario 1: "I can't find the database!"
**Answer**: It's in the Docker volume. Use:
```bash
docker exec orion-project ls -lh /app/data/
```

### Scenario 2: "The database exists but seems empty"
**Answer**: Check if tables exist:
```bash
docker exec orion-project python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    inspector = db.inspect(db.engine)
    print('Tables:', inspector.get_table_names())
"
```

If no tables, recreate them:
```bash
docker exec orion-project python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
    print('Tables created!')
"
```

### Scenario 3: "I need to restore a backup"
**Answer**: Use the Python tool or manually:
```bash
# Copy backup into container
docker cp ./backup.db orion-project:/app/data/orion.db

# Restart container
docker-compose restart
```

### Scenario 4: "I need to create an admin user"
**Answer**: Use the Python tool (option 5) or manually:
```bash
docker exec -it orion-project python

# In Python shell:
from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app('production')
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com',
        password_hash=generate_password_hash('your-password'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print('Admin created!')
```

### Scenario 5: "Database is corrupted"
**Answer**: 
1. Create backup first: `docker cp orion-project:/app/data/orion.db ./backup.db`
2. Check integrity: `sqlite3 backup.db "PRAGMA integrity_check;"`
3. If corrupted, restore from older backup or recreate

---

## Understanding Docker Volumes

Your `docker-compose.yml` defines:
```yaml
volumes:
  orion-data:
    driver: local
```

This creates a **persistent volume** that:
- ✅ Survives container restarts
- ✅ Survives container deletion
- ✅ Can be backed up with `docker volume backup`
- ⚠️ But is NOT visible with normal `find` commands!

### Volume Operations

```bash
# List all volumes
docker volume ls

# Inspect volume (see where it's stored)
docker volume inspect orion-data

# Backup entire volume
docker run --rm -v orion-data:/data -v $(pwd):/backup ubuntu tar czf /backup/orion-data-backup.tar.gz /data

# Restore volume
docker run --rm -v orion-data:/data -v $(pwd):/backup ubuntu tar xzf /backup/orion-data-backup.tar.gz -C /

# ⚠️ Delete volume (DANGER!)
docker volume rm orion-data
```

---

## Automatic Backups

Set up a cron job to backup daily:

```bash
# Edit crontab
crontab -e

# Add this line for daily backup at 3 AM:
0 3 * * * docker cp orion-project:/app/data/orion.db ~/backups/orion_$(date +\%Y\%m\%d).db

# Or use the Python tool:
0 3 * * * cd /path/to/mysite/site01 && python docker_db_recovery.py --backup
```

---

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs orion-project

# Check if volume exists
docker volume ls | grep orion-data

# Restart with fresh logs
docker-compose down
docker-compose up -d
docker logs orion-project -f
```

### Can't access database from container
```bash
# Check file permissions
docker exec orion-project ls -la /app/data/

# Check if directory exists
docker exec orion-project mkdir -p /app/data

# Check environment variables
docker exec orion-project env | grep DATABASE
```

### Database file is too small (< 1KB)
This usually means the database was never properly initialized. Run:
```bash
docker exec orion-project python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
"
```

---

## Files Created

1. **`docker_db_recovery.py`** - Interactive recovery tool with menu
2. **`check_docker_db.sh`** - Automated health check script
3. **`DOCKER_DATABASE_GUIDE.md`** - This guide!

All tools are safe to use and will create backups before destructive operations.

---

## Quick Reference Card

| What I want to do | Command |
|-------------------|---------|
| Check if database exists | `docker exec orion-project ls -lh /app/data/orion.db` |
| Backup database | `docker cp orion-project:/app/data/orion.db ./backup.db` |
| Count users | `docker exec orion-project python -c "from app import create_app; from app.models import User; app=create_app('production'); app.app_context().push(); print(User.query.count())"` |
| Access SQLite shell | `docker exec -it orion-project sqlite3 /app/data/orion.db` |
| Create tables | `docker exec orion-project python -c "from app import create_app, db; app=create_app('production'); app.app_context().push(); db.create_all()"` |
| View logs | `docker logs orion-project --tail 50` |
| Restart container | `docker-compose restart` |
| Interactive recovery | `python docker_db_recovery.py` |
| Health check | `./check_docker_db.sh` |

---

## Why This Happened

You have an admin user because:
1. ✅ The database **does exist** in the Docker volume
2. ✅ The volume persists between container restarts
3. ✅ Flask can access it via `/app/data/orion.db`
4. ❌ But `find` can't see it because it's in Docker's internal storage!

It's like having a file in a ZIP archive - it exists, but `find` won't find it unless you look inside the archive (or in this case, inside the Docker volume).
