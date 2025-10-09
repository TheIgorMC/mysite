#!/bin/bash

# Image Upload Script for Orion Project
# This script helps you upload the new images to the media folder

echo "🖼️  Orion Project - Image Upload Script"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -d "media" ]; then
    echo "❌ Error: 'media' directory not found!"
    echo "   Please run this script from the project root directory"
    exit 1
fi

echo "📁 Current media directory contents:"
ls -lh media/
echo ""

# List of required images
REQUIRED_IMAGES=(
    "3d_gallery.jpg"
    "3d_quote.jpg"
    "3d_shop.jpg"
    "el_gallery.jpg"
    "el_shop.jpg"
)

echo "📋 Required images:"
for img in "${REQUIRED_IMAGES[@]}"; do
    if [ -f "media/$img" ]; then
        echo "   ✅ $img (already exists)"
    else
        echo "   ❌ $img (missing)"
    fi
done
echo ""

# Count missing images
MISSING_COUNT=0
for img in "${REQUIRED_IMAGES[@]}"; do
    if [ ! -f "media/$img" ]; then
        ((MISSING_COUNT++))
    fi
done

if [ $MISSING_COUNT -eq 0 ]; then
    echo "🎉 All images are present!"
    echo ""
    echo "✅ Ready to deploy!"
    exit 0
fi

echo "⚠️  $MISSING_COUNT image(s) missing"
echo ""
echo "📥 Upload Instructions:"
echo ""
echo "Option 1: Local Upload (if on server)"
echo "   cp /path/to/your/images/*.jpg media/"
echo ""
echo "Option 2: SCP Upload (from local machine)"
echo "   scp 3d_gallery.jpg user@server:/path/to/mysite/media/"
echo "   scp 3d_quote.jpg user@server:/path/to/mysite/media/"
echo "   scp 3d_shop.jpg user@server:/path/to/mysite/media/"
echo "   scp el_gallery.jpg user@server:/path/to/mysite/media/"
echo "   scp el_shop.jpg user@server:/path/to/mysite/media/"
echo ""
echo "Option 3: Docker Copy (if using Docker)"
echo "   docker cp 3d_gallery.jpg orion-project:/app/site01/app/static/media/"
echo "   docker cp 3d_quote.jpg orion-project:/app/site01/app/static/media/"
echo "   docker cp 3d_shop.jpg orion-project:/app/site01/app/static/media/"
echo "   docker cp el_gallery.jpg orion-project:/app/site01/app/static/media/"
echo "   docker cp el_shop.jpg orion-project:/app/site01/app/static/media/"
echo ""
echo "💡 Tip: Run this script again after uploading to verify all images are present"
echo ""
