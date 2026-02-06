"""
Migration script to convert GalleryItem content to BlogPost
Creates blog posts from gallery items that have content_it/content_en
Run with: python migrations/migrate_gallery_to_blog.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import GalleryItem, BlogPost, User

def migrate():
    """Convert gallery items with content to blog posts"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting migration from GalleryItem to BlogPost...")
        
        # Get admin user (or first user)
        admin = User.query.filter_by(is_admin=True).first()
        if not admin:
            admin = User.query.first()
        
        if not admin:
            print("❌ Error: No users found. Create a user first.")
            return False
        
        print(f"✅ Using author: {admin.username}")
        
        # Find all gallery items with content
        items_with_content = GalleryItem.query.filter(
            (GalleryItem.content_it != None) | (GalleryItem.content_en != None)
        ).all()
        
        print(f"📊 Found {len(items_with_content)} gallery items with content")
        
        migrated = 0
        skipped = 0
        
        for item in items_with_content:
            # Check if already migrated (slug exists in BlogPost)
            existing = BlogPost.query.filter_by(slug=item.slug).first()
            if existing:
                print(f"⏭️  Skipped: {item.slug} (already exists)")
                skipped += 1
                continue
            
            # Create blog post
            post = BlogPost(
                project_id=item.id,
                author_id=admin.id,
                
                # Italian content
                title_it=item.title_it or "Titolo mancante",
                excerpt_it=item.description_it,
                content_it=item.content_it or "",
                
                # English content
                title_en=item.title_en or "Missing title",
                excerpt_en=item.description_en,
                content_en=item.content_en or "",
                
                # SEO
                slug=item.slug,
                
                # Media
                cover_image=None,  # Will use project's main_image
                images=item.images,
                
                # Categorization
                tags=item.tags,
                
                # Publishing
                is_published=True,
                published_at=item.created_at or datetime.utcnow(),
                
                # Metadata
                created_at=item.created_at or datetime.utcnow(),
                updated_at=item.updated_at or datetime.utcnow(),
                view_count=item.view_count or 0
            )
            
            db.session.add(post)
            migrated += 1
            print(f"✅ Migrated: {item.slug}")
        
        # Commit all changes
        db.session.commit()
        
        print(f"\n✅ Migration completed!")
        print(f"   - Migrated: {migrated} posts")
        print(f"   - Skipped: {skipped} posts")
        
        return True

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
