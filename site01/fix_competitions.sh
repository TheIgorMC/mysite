#!/bin/bash
# Quick fix script to remove duplicate try statement in competitions.html

echo "Fixing competitions.html inside Docker container..."

docker exec orion-project bash -c "
# Create backup first
cp /app/site01/app/templates/archery/competitions.html /app/site01/app/templates/archery/competitions.html.backup

# Remove the two problematic lines
sed -i '/\/\/ Load competitions from FastAPI/d' /app/site01/app/templates/archery/competitions.html
sed -i '246s/^[[:space:]]*try {$//' /app/site01/app/templates/archery/competitions.html

echo 'File fixed!'
echo 'Backup saved at: /app/site01/app/templates/archery/competitions.html.backup'
"

echo "Restarting container..."
docker-compose restart

echo "Done! Try refreshing your browser now."
