"""
Migration: Add customization flags to products table
Date: 2025-10-27
Description: Adds is_custom_string and is_custom_print boolean flags to enable customizers
"""

import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

def run_migration():
    """Add customization flags to products table"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Adding customization flags to products table...")
            
            # Check if columns already exist
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('products')]
            
            if 'is_custom_string' in columns and 'is_custom_print' in columns:
                print("✓ Columns already exist, skipping migration")
                return
            
            # Add columns using raw SQL (works for both SQLite and MySQL)
            with db.engine.connect() as conn:
                if 'is_custom_string' not in columns:
                    if 'sqlite' in str(db.engine.url):
                        conn.execute(text("ALTER TABLE products ADD COLUMN is_custom_string BOOLEAN DEFAULT 0"))
                    else:
                        conn.execute(text("ALTER TABLE products ADD COLUMN is_custom_string BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                    print("✓ Added is_custom_string column")
                
                if 'is_custom_print' not in columns:
                    if 'sqlite' in str(db.engine.url):
                        conn.execute(text("ALTER TABLE products ADD COLUMN is_custom_print BOOLEAN DEFAULT 0"))
                    else:
                        conn.execute(text("ALTER TABLE products ADD COLUMN is_custom_print BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                    print("✓ Added is_custom_print column")
            
            print("\n✅ Migration completed successfully!")
            
            # Show updated columns
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('products')]
            print(f"\nProducts table now has {len(columns)} columns:")
            for col in columns:
                print(f"  - {col}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

def rollback_migration():
    """Remove customization flags from products table"""
    
    app = create_app()
    
    with app.app_context():
        try:
            print("Rolling back customization flags from products table...")
            
            # Check database type
            if 'sqlite' in str(db.engine.url):
                print("⚠️  SQLite doesn't support DROP COLUMN easily.")
                print("   You'll need to recreate the table manually or use a migration tool.")
                return
            
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE products DROP COLUMN is_custom_string"))
                print("✓ Removed is_custom_string column")
                
                conn.execute(text("ALTER TABLE products DROP COLUMN is_custom_print"))
                print("✓ Removed is_custom_print column")
                
                conn.commit()
            
            print("\n✅ Rollback completed successfully!")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_migration()
    else:
        run_migration()
