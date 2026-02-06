"""
Migration script to add blog_posts table
Run with: python migrations/add_blog_posts.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import BlogPost

def migrate():
    """Add blog_posts table"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting blog_posts migration...")
        
        # Create tables
        db.create_all()
        print("✅ blog_posts table created")
        
        # Verify table creation
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'blog_posts' in tables:
            columns = [col['name'] for col in inspector.get_columns('blog_posts')]
            print(f"✅ Columns created: {', '.join(columns)}")
            print("\n✅ Migration completed successfully!")
        else:
            print("❌ Error: blog_posts table not found")
            return False
        
        return True

if __name__ == '__main__':
    try:
        migrate()
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
