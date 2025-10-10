#!/bin/bash
# Database Recovery Script for Orange Pi Server
# Run this on your Orange Pi to check database status

echo "=================================================="
echo "  ORANGE PI DATABASE CHECK & RECOVERY"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Find the Flask app directory
APP_DIR="/path/to/your/site01"  # UPDATE THIS PATH
DB_FILE="$APP_DIR/instance/site.db"

echo -e "\n${YELLOW}Step 1: Checking paths...${NC}"
echo "App directory: $APP_DIR"
echo "Expected database: $DB_FILE"

# Check if directory exists
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ App directory not found!${NC}"
    echo "Please update APP_DIR in this script"
    exit 1
fi

echo -e "${GREEN}✅ App directory found${NC}"

# Check if database file exists
echo -e "\n${YELLOW}Step 2: Checking database file...${NC}"
if [ -f "$DB_FILE" ]; then
    echo -e "${GREEN}✅ Database file exists${NC}"
    DB_SIZE=$(du -h "$DB_FILE" | cut -f1)
    echo "   Size: $DB_SIZE"
    echo "   Last modified: $(stat -c %y "$DB_FILE" 2>/dev/null || stat -f "%Sm" "$DB_FILE")"
else
    echo -e "${RED}❌ Database file NOT found!${NC}"
    echo "   Expected location: $DB_FILE"
    
    # Check if instance directory exists
    if [ ! -d "$APP_DIR/instance" ]; then
        echo -e "${YELLOW}   Creating instance directory...${NC}"
        mkdir -p "$APP_DIR/instance"
    fi
    
    # Check for backups
    echo -e "\n${YELLOW}Searching for backups...${NC}"
    if [ -d "$APP_DIR/instance/backups" ]; then
        echo "Found backups directory:"
        ls -lh "$APP_DIR/instance/backups/"
    else
        echo -e "${RED}No backups directory found${NC}"
    fi
    
    echo -e "\n${YELLOW}Database needs to be recreated or restored${NC}"
    exit 1
fi

# Check if Python environment is set up
echo -e "\n${YELLOW}Step 3: Checking Python environment...${NC}"
cd "$APP_DIR" || exit 1

if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    source venv/bin/activate
elif [ -d ".venv" ]; then
    echo -e "${GREEN}✅ Virtual environment found${NC}"
    source .venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found${NC}"
fi

# Check if Flask app can load
echo -e "\n${YELLOW}Step 4: Testing database connection...${NC}"
python3 << 'PYTHON_SCRIPT'
import sys
sys.path.insert(0, '.')
try:
    from app import create_app, db
    from app.models import User
    
    app = create_app()
    with app.app_context():
        # Try to query users
        user_count = User.query.count()
        admin_count = User.query.filter_by(is_admin=True).count()
        
        print(f"✅ Database connection successful")
        print(f"   Users: {user_count}")
        print(f"   Admins: {admin_count}")
        
        if user_count == 0:
            print("⚠️  WARNING: No users found in database!")
            sys.exit(2)
        
        if admin_count == 0:
            print("⚠️  WARNING: No admin users found!")
            sys.exit(3)
        
except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)
PYTHON_SCRIPT

DB_CHECK_RESULT=$?

if [ $DB_CHECK_RESULT -eq 0 ]; then
    echo -e "\n${GREEN}✅ Database is healthy!${NC}"
elif [ $DB_CHECK_RESULT -eq 2 ]; then
    echo -e "\n${RED}❌ Database is empty (no users)${NC}"
    echo "Options:"
    echo "  1. Restore from backup"
    echo "  2. Recreate database and create admin user"
elif [ $DB_CHECK_RESULT -eq 3 ]; then
    echo -e "\n${YELLOW}⚠️  No admin users (but database has users)${NC}"
    echo "You need to make a user admin"
else
    echo -e "\n${RED}❌ Database has errors${NC}"
    echo "Options:"
    echo "  1. Restore from backup"
    echo "  2. Recreate database from migrations"
fi

# Create backup
echo -e "\n${YELLOW}Step 5: Creating backup (just in case)...${NC}"
BACKUP_DIR="$APP_DIR/instance/backups"
mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/site_backup_${TIMESTAMP}.db"

if [ -f "$DB_FILE" ]; then
    cp "$DB_FILE" "$BACKUP_FILE"
    echo -e "${GREEN}✅ Backup created: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠️  No database to backup${NC}"
fi

# Show backups
echo -e "\n${YELLOW}Available backups:${NC}"
if [ -d "$BACKUP_DIR" ]; then
    ls -lh "$BACKUP_DIR/"
else
    echo "No backups found"
fi

echo -e "\n=================================================="
echo "  RECOVERY OPTIONS"
echo "=================================================="
echo ""
echo "If database was deleted or corrupted:"
echo ""
echo "1. RESTORE FROM BACKUP:"
echo "   cd $APP_DIR"
echo "   cp instance/backups/LATEST_BACKUP.db instance/site.db"
echo ""
echo "2. RECREATE DATABASE:"
echo "   cd $APP_DIR"
echo "   python3 migrations/add_authorized_athletes.py"
echo "   python3 create_admin.py"
echo ""
echo "3. USE RECOVERY UTILITY:"
echo "   cd $APP_DIR"
echo "   python3 db_recovery.py"
echo ""
echo "=================================================="
