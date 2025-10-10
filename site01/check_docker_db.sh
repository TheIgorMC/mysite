#!/bin/bash
#
# Docker Database Health Check Script
# This script checks the SQLite database inside the Docker container
#

CONTAINER_NAME="orion-project"
DB_PATH="/app/data/orion.db"
BACKUP_DIR="./backups"

echo "=================================================="
echo "   Docker Database Health Check"
echo "=================================================="
echo ""

# Check if container is running
echo "1. Checking if container is running..."
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo "❌ ERROR: Container '$CONTAINER_NAME' is not running!"
    echo ""
    echo "Start it with: docker-compose up -d"
    exit 1
fi
echo "✅ Container is running"
echo ""

# Check if database file exists
echo "2. Checking if database file exists..."
if docker exec "$CONTAINER_NAME" test -f "$DB_PATH"; then
    DB_SIZE=$(docker exec "$CONTAINER_NAME" stat -f%z "$DB_PATH" 2>/dev/null || docker exec "$CONTAINER_NAME" stat -c%s "$DB_PATH" 2>/dev/null)
    DB_SIZE_HUMAN=$(docker exec "$CONTAINER_NAME" ls -lh "$DB_PATH" | awk '{print $5}')
    echo "✅ Database file exists: $DB_PATH"
    echo "   Size: $DB_SIZE_HUMAN ($DB_SIZE bytes)"
    
    if [ "$DB_SIZE" -lt 1000 ]; then
        echo "⚠️  WARNING: Database file is very small! It might be empty or corrupted."
    fi
else
    echo "❌ ERROR: Database file does not exist at $DB_PATH"
    echo ""
    echo "This might mean:"
    echo "  - The database was never created"
    echo "  - The Docker volume is corrupted"
    echo "  - The path in docker-compose.yml is wrong"
    exit 2
fi
echo ""

# Check Python/Flask database connection
echo "3. Testing database connection from Flask..."
DB_TEST=$(docker exec "$CONTAINER_NAME" python -c "
from app import create_app, db
from app.models import User
import sys

try:
    app = create_app('production')
    with app.app_context():
        # Try to query the database
        user_count = User.query.count()
        print(f'SUCCESS:{user_count}')
        sys.exit(0)
except Exception as e:
    print(f'ERROR:{str(e)}')
    sys.exit(1)
" 2>&1)

if echo "$DB_TEST" | grep -q "SUCCESS:"; then
    USER_COUNT=$(echo "$DB_TEST" | grep "SUCCESS:" | cut -d':' -f2)
    echo "✅ Database connection successful"
    echo "   Total users: $USER_COUNT"
    
    if [ "$USER_COUNT" -eq 0 ]; then
        echo "⚠️  WARNING: No users found in database!"
    fi
else
    echo "❌ ERROR: Cannot connect to database"
    echo "   Error: $DB_TEST"
    exit 1
fi
echo ""

# Count admin users
echo "4. Checking for admin users..."
ADMIN_COUNT=$(docker exec "$CONTAINER_NAME" python -c "
from app import create_app, db
from app.models import User

app = create_app('production')
with app.app_context():
    admin_count = User.query.filter_by(is_admin=True).count()
    print(admin_count)
" 2>&1)

if [ "$ADMIN_COUNT" -gt 0 ]; then
    echo "✅ Found $ADMIN_COUNT admin user(s)"
else
    echo "⚠️  WARNING: No admin users found!"
    echo "   You may need to create an admin user."
fi
echo ""

# Check Docker volume
echo "5. Checking Docker volume..."
VOLUME_INFO=$(docker volume inspect orion-data 2>&1)
if [ $? -eq 0 ]; then
    VOLUME_MOUNTPOINT=$(echo "$VOLUME_INFO" | grep Mountpoint | cut -d'"' -f4)
    echo "✅ Docker volume 'orion-data' exists"
    echo "   Host path: $VOLUME_MOUNTPOINT"
    
    # Check actual file on host (requires sudo)
    if [ -f "$VOLUME_MOUNTPOINT/orion.db" ]; then
        HOST_SIZE=$(ls -lh "$VOLUME_MOUNTPOINT/orion.db" 2>/dev/null | awk '{print $5}')
        echo "   Database on host: $HOST_SIZE"
    fi
else
    echo "⚠️  WARNING: Docker volume 'orion-data' not found"
fi
echo ""

# Create backup
echo "6. Creating backup..."
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/orion_db_backup_$(date +%Y%m%d_%H%M%S).db"

if docker exec "$CONTAINER_NAME" cat "$DB_PATH" > "$BACKUP_FILE" 2>/dev/null; then
    BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo "✅ Backup created: $BACKUP_FILE"
    echo "   Size: $BACKUP_SIZE"
else
    echo "❌ ERROR: Failed to create backup"
fi
echo ""

# List recent backups
echo "7. Recent backups:"
if [ -d "$BACKUP_DIR" ]; then
    ls -lht "$BACKUP_DIR"/*.db 2>/dev/null | head -5 | awk '{print "   " $9 " (" $5 ")"}'
    BACKUP_COUNT=$(ls "$BACKUP_DIR"/*.db 2>/dev/null | wc -l)
    echo "   Total backups: $BACKUP_COUNT"
else
    echo "   No backups found"
fi
echo ""

# Summary
echo "=================================================="
echo "   Health Check Complete"
echo "=================================================="
echo ""
echo "Next steps:"
echo "  • To access database inside container:"
echo "    docker exec -it $CONTAINER_NAME sqlite3 $DB_PATH"
echo ""
echo "  • To copy database to host:"
echo "    docker cp $CONTAINER_NAME:$DB_PATH ./orion_backup.db"
echo ""
echo "  • To restore a backup:"
echo "    docker cp ./backup.db $CONTAINER_NAME:$DB_PATH"
echo "    docker-compose restart"
echo ""
echo "  • To view logs:"
echo "    docker logs $CONTAINER_NAME --tail 50"
echo ""
echo "  • To recreate database (CAUTION!):"
echo "    docker exec -it $CONTAINER_NAME python"
echo "    >>> from app import create_app, db"
echo "    >>> app = create_app('production')"
echo "    >>> with app.app_context(): db.create_all()"
echo ""
