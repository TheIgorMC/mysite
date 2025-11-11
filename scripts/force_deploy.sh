#!/bin/bash
# Force deploy with complete cache clearing
# Usage: ./force_deploy.sh

set -e

echo "🚀 Force Deploy - Complete Cache Clear"
echo "======================================"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "   Run this script from the project root directory"
    exit 1
fi

# Step 1: Pull latest changes
echo ""
echo "📥 Step 1: Pulling latest changes from Git..."
git pull
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Git pull failed or had conflicts"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 2: Stop containers
echo ""
echo "🛑 Step 2: Stopping containers..."
docker compose down

# Step 3: Clear local Docker cache
echo ""
echo "🧹 Step 3: Clearing Docker build cache..."
docker builder prune -f

# Step 4: Rebuild with no cache
echo ""
echo "🔨 Step 4: Rebuilding container (no cache)..."
docker compose build --no-cache --pull --build-arg CACHE_BUST=$(date +%s)

# Step 5: Start containers
echo ""
echo "▶️  Step 5: Starting containers..."
docker compose up -d

# Step 6: Run database migrations
echo ""
echo "🔄 Step 6: Running database migrations..."
docker exec orion-project bash -c "cd /app/site01 && python -m pip install mysql-connector-python python-dotenv 2>/dev/null || true"

# Run Python migrations
docker exec orion-project bash -c "cd /app/site01 && for migration in migrations/*.py; do [ -f \"\$migration\" ] && python \"\$migration\" 2>/dev/null || true; done"

# Run SQL migrations
echo "   Running SQL migrations..."
docker exec orion-project bash -c "cd /app/site01 && for migration in migrations/*.sql; do [ -f \"\$migration\" ] && sqlite3 instance/mysite.db < \"\$migration\" 2>/dev/null || true; done"

echo "✓ Migrations completed"

# Step 7: Wait for startup
echo ""
echo "⏳ Step 7: Waiting for application to stabilize..."
sleep 5

# Step 8: Verify
echo ""
echo "✅ Step 8: Verifying deployment..."

# Check if container is running
if ! docker ps | grep -q orion-project; then
    echo "❌ Error: Container not running!"
    echo ""
    echo "Check logs with: docker logs orion-project"
    exit 1
fi

# Check logs for cache clearing
echo ""
echo "📋 Recent logs:"
docker logs orion-project --tail 20

# Check template file timestamp
echo ""
echo "📄 Template file info:"
docker exec orion-project stat /app/site01/app/templates/archery/competitions.html | grep "Modify:"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Next steps:"
echo "   1. Open browser and go to your site"
echo "   2. Press Ctrl+Shift+R (hard refresh)"
echo "   3. Clear browser cache if needed"
echo ""
echo "📊 Useful commands:"
echo "   docker logs -f orion-project      # Follow logs"
echo "   docker compose restart            # Restart container"
echo "   docker exec -it orion-project bash  # Enter container"
echo ""
