#!/bin/bash
# Docker entrypoint script - runs migrations and starts the application

set -e

echo "🚀 Starting Orion Project container..."

# Wait a moment for database volume to be ready
sleep 2

# Run database migrations
echo "📦 Running database migrations..."

# Run add_classe_field migration if needed
if [ -f "/app/site01/migrations/add_classe_field.py" ]; then
    echo "  → Running add_classe_field migration..."
    python /app/site01/migrations/add_classe_field.py || true
fi

echo "✅ Migrations complete!"

# Clear any runtime Python cache aggressively
echo "🧹 Clearing Python cache..."
find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find /app -type f -name "*.pyc" -delete 2>/dev/null || true
find /app -type f -name "*.pyo" -delete 2>/dev/null || true

# Touch all templates to force Jinja to recompile
echo "🔄 Forcing template recompilation..."
find /app/site01/app/templates -type f -name "*.html" -exec touch {} + 2>/dev/null || true

# Clear Jinja cache if it exists
if [ -d "/tmp/__pycache__" ]; then
    rm -rf /tmp/__pycache__
fi

echo "✅ Cache cleared and templates refreshed!"

# Start the application
echo "🌟 Starting Flask application..."
cd /app/site01
# Use --reload to watch for file changes (only in production with auto-reload enabled)
# Disable preload to ensure workers load fresh code
exec python -m gunicorn -b 0.0.0.0:5000 -w 4 --timeout 120 --max-requests 1000 --max-requests-jitter 100 wsgi:app
