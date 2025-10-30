#!/bin/bash
# Save Current Uploads Before Applying Fix
# Run this BEFORE restarting with the new docker-compose.yml

set -e

echo "🖼️  Saving Current Uploaded Images"
echo "=================================="

# Check if container is running
if ! docker ps | grep -q orion-project; then
    echo "❌ Error: orion-project container is not running"
    echo "   Start it first with: docker compose up -d"
    exit 1
fi

# Create backup directory with timestamp
BACKUP_DIR="./uploads_backup_$(date +%Y%m%d_%H%M%S)"
echo ""
echo "📁 Creating backup directory: $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Copy uploads from container
echo "📥 Copying uploads from container..."
docker cp orion-project:/app/site01/app/static/uploads/. "$BACKUP_DIR/"

# Check what was backed up
FILE_COUNT=$(find "$BACKUP_DIR" -type f | wc -l)
echo ""
echo "✅ Backup complete!"
echo "   Files backed up: $FILE_COUNT"
echo "   Location: $BACKUP_DIR"

# List contents
echo ""
echo "📋 Backed up files:"
find "$BACKUP_DIR" -type f -ls | head -20

if [ $FILE_COUNT -gt 20 ]; then
    echo "   ... and $((FILE_COUNT - 20)) more files"
fi

echo ""
echo "🔄 Next steps:"
echo "   1. Update docker-compose.yml (already done if you pulled latest)"
echo "   2. Run: docker compose down"
echo "   3. Run: docker compose up -d"
echo "   4. Wait 10 seconds for startup"
echo "   5. Run: ./restore_uploads.sh $BACKUP_DIR"
echo ""

# Create restoration script
cat > restore_uploads.sh << 'RESTORE_SCRIPT'
#!/bin/bash
# Restore Uploads to Persistent Volume

set -e

if [ -z "$1" ]; then
    echo "Usage: ./restore_uploads.sh <backup_directory>"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Error: Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "🔄 Restoring uploads from: $BACKUP_DIR"

# Check if container is running
if ! docker ps | grep -q orion-project; then
    echo "❌ Error: orion-project container is not running"
    echo "   Start it first with: docker compose up -d"
    exit 1
fi

# Copy files back
echo "📤 Copying files to container..."
docker cp "$BACKUP_DIR/." orion-project:/app/site01/app/static/uploads/

# Fix permissions
echo "🔐 Setting correct permissions..."
docker exec orion-project chmod -R 755 /app/site01/app/static/uploads
docker exec orion-project chown -R root:root /app/site01/app/static/uploads

# Verify
FILE_COUNT=$(docker exec orion-project find /app/site01/app/static/uploads -type f | wc -l)

echo ""
echo "✅ Restoration complete!"
echo "   Files restored: $FILE_COUNT"
echo ""
echo "🧪 Verify by visiting your shop page"
echo "   Images should now be visible and persist across restarts"
RESTORE_SCRIPT

chmod +x restore_uploads.sh

echo "✅ Restoration script created: ./restore_uploads.sh"
echo ""
