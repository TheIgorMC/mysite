#!/bin/bash
# Fast deploy with selective cache clearing
# Usage: ./force_deploy.sh [full|quick]
# - quick (default): Only rebuild app code (fast)
# - full: Complete rebuild including dependencies (slow)

set -e

MODE="${1:-quick}"

if [ "$MODE" == "full" ]; then
    echo "🚀 Full Deploy - Complete Cache Clear"
else
    echo "⚡ Quick Deploy - App Code Only"
fi
echo "======================================"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "   Run this script from the project root directory"
    exit 1
fi

# Step 1: Pull latest changes
echo ""
echo "📥 Pulling latest changes from Git..."
git pull || echo "⚠️  Warning: Git pull had issues, continuing..."

# Step 2: Update CACHE_BUST in docker-compose.yml to force rebuild from COPY step
echo ""
echo "🔄 Updating cache bust value..."
TIMESTAMP=$(date +%s)
sed -i.bak "s/CACHE_BUST: .*/CACHE_BUST: $TIMESTAMP/" docker-compose.yml

# Step 3: Rebuild
echo ""
if [ "$MODE" == "full" ]; then
    echo "🛑 Stopping containers..."
    docker compose down
    
    echo "🧹 Clearing Docker build cache..."
    docker builder prune -f
    
    echo "🔨 Full rebuild (no cache)..."
    docker compose build --no-cache --pull
else
    echo "🔨 Quick rebuild (reusing dependency cache)..."
    # This will rebuild from CACHE_BUST onwards, keeping Python deps cached
    docker compose build
fi

# Step 4: Start containers
echo ""
echo "▶️  Starting containers..."
docker compose up -d

# Step 5: Wait for startup
echo ""
echo "⏳ Waiting for startup (3 seconds)..."
sleep 3

# Step 6: Verify
echo ""
echo "✅ Verifying deployment..."

# Check if container is running
if ! docker ps | grep -q orion-project; then
    echo "❌ Error: Container not running!"
    echo ""
    echo "Check logs with: docker logs orion-project"
    exit 1
fi

# Show recent logs
echo ""
echo "📋 Recent logs:"
docker logs orion-project --tail 15

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Quick access:"
echo "   Browser: http://localhost:6080 (Ctrl+Shift+R to hard refresh)"
echo ""
echo "📊 Useful commands:"
echo "   docker logs -f orion-project           # Follow logs"
echo "   docker exec -it orion-project bash     # Enter container"
echo "   ./scripts/force_deploy.sh full        # Full rebuild with deps"
echo ""
