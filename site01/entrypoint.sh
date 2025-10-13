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

# Clear any runtime Python cache
echo "🧹 Clearing Python cache..."
find /app -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find /app -type f -name "*.pyc" -delete 2>/dev/null || true

echo "✅ Cache cleared!"

# Start the application
echo "🌟 Starting Flask application..."
cd /app/site01
exec python -m gunicorn -b 0.0.0.0:5000 -w 4 --timeout 120 wsgi:app
