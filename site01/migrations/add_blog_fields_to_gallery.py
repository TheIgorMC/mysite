#!/usr/bin/env python
"""
Migration: Add blog post fields to gallery_items table
Created: 2026-02-04

Adds fields to transform gallery items into full blog posts:
- content_it, content_en: Full article content
- slug: URL-friendly identifier
- pcb_background: PCB screenshot for parallax effect (electronics)
- updated_at: Last modification timestamp
- view_count: Popularity tracking

Usage:
    python migrations/add_blog_fields_to_gallery.py
"""

import sys
import os

print("=" * 50)
print("Starting gallery blog fields migration...")
print("=" * 50)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Importing app and db...")
    from app import create_app, db
    from sqlalchemy import text
    print("✓ Imports successful")
    
    print("\nCreating app...")
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    print("✓ App created")
    
    print("\nConnecting to database...")
    with app.app_context():
        print("✓ App context created")
        
        # Add content fields
        try:
            print("\nAdding content_it column...")
            db.session.execute(text('ALTER TABLE gallery_items ADD COLUMN content_it TEXT'))
            db.session.commit()
            print("✓ Added content_it")
        except Exception as e:
            print(f"⚠ content_it: {str(e)}")
            db.session.rollback()
        
        try:
            print("\nAdding content_en column...")
            db.session.execute(text('ALTER TABLE gallery_items ADD COLUMN content_en TEXT'))
            db.session.commit()
            print("✓ Added content_en")
        except Exception as e:
            print(f"⚠ content_en: {str(e)}")
            db.session.rollback()
        
        # Add slug
        try:
            print("\nAdding slug column...")
            db.session.execute(text('ALTER TABLE gallery_items ADD COLUMN slug VARCHAR(256)'))
            db.session.commit()
            print("✓ Added slug")
            
            # Create index on slug
            try:
                print("Creating index on slug...")
                db.session.execute(text('CREATE UNIQUE INDEX ix_gallery_items_slug ON gallery_items(slug)'))
                db.session.commit()
                print("✓ Created slug index")
            except Exception as e:
                print(f"⚠ slug index: {str(e)}")
                db.session.rollback()
        except Exception as e:
            print(f"⚠ slug: {str(e)}")
            db.session.rollback()
        
        # Add PCB background
        try:
            print("\nAdding pcb_background column...")
            db.session.execute(text('ALTER TABLE gallery_items ADD COLUMN pcb_background VARCHAR(256)'))
            db.session.commit()
            print("✓ Added pcb_background")
        except Exception as e:
            print(f"⚠ pcb_background: {str(e)}")
            db.session.rollback()
        
        # Add updated_at
        try:
            print("\nAdding updated_at column...")
            db.session.execute(text('ALTER TABLE gallery_items ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP'))
            db.session.commit()
            print("✓ Added updated_at")
        except Exception as e:
            print(f"⚠ updated_at: {str(e)}")
            db.session.rollback()
        
        # Add view_count
        try:
            print("\nAdding view_count column...")
            db.session.execute(text('ALTER TABLE gallery_items ADD COLUMN view_count INTEGER DEFAULT 0'))
            db.session.commit()
            print("✓ Added view_count")
        except Exception as e:
            print(f"⚠ view_count: {str(e)}")
            db.session.rollback()
        
        # Generate slugs for existing items
        try:
            print("\nGenerating slugs for existing items...")
            from app.models import GalleryItem
            import re
            
            items = GalleryItem.query.filter(GalleryItem.slug.is_(None)).all()
            for item in items:
                # Create slug from English title
                slug = re.sub(r'[^a-z0-9]+', '-', item.title_en.lower()).strip('-')
                # Ensure uniqueness
                base_slug = slug
                counter = 1
                while GalleryItem.query.filter_by(slug=slug).first():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                item.slug = slug
            
            db.session.commit()
            print(f"✓ Generated {len(items)} slugs")
        except Exception as e:
            print(f"⚠ slug generation: {str(e)}")
            db.session.rollback()
        
        print("\n" + "=" * 50)
        print("✅ Migration complete!")
        print("=" * 50)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
