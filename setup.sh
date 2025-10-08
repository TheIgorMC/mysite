#!/bin/bash

# Orion Project - Quick Setup Script
# This script helps you set up the Orion Project quickly on your server

set -e

echo "🎯 Orion Project - Quick Setup"
echo "================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    echo "Please install Docker first: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed!"
    echo "Please install Docker Compose first: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    
    # Generate a secret key
    echo "🔐 Generating secure SECRET_KEY..."
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    
    # Replace the secret key in .env
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your-secret-key-here-change-this/$SECRET_KEY/" .env
    else
        # Linux
        sed -i "s/your-secret-key-here-change-this/$SECRET_KEY/" .env
    fi
    
    echo "✅ .env file created with secure SECRET_KEY"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your credentials:"
    echo "   - Cloudflare Access credentials (if using)"
    echo "   - Email configuration (if using)"
    echo ""
    
    read -p "Press Enter to continue or Ctrl+C to exit and edit .env first..."
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🐳 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting Orion Project..."
docker-compose up -d

echo ""
echo "⏳ Waiting for application to start..."
sleep 5

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Orion Project is running!"
    echo ""
    echo "📍 Access your application at:"
    echo "   http://localhost:5000"
    echo "   or"
    echo "   http://$(hostname -I | awk '{print $1}'):5000"
    echo ""
    echo "📊 View logs:"
    echo "   docker-compose logs -f"
    echo ""
    echo "🛑 Stop the application:"
    echo "   docker-compose down"
    echo ""
    echo "🔄 Update the application:"
    echo "   git pull && docker-compose build && docker-compose up -d"
else
    echo "❌ Failed to start Orion Project"
    echo "Check logs with: docker-compose logs"
    exit 1
fi
