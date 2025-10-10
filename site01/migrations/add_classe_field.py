"""
Migration: Add classe field to authorized_athletes table
Created: 2025-10-10

This migration adds the 'classe' field to store competition class (CO, OL, AN)

Usage:
    python migrations/add_classe_field.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def upgrade():
    """Add classe column to authorized_athletes table"""
    
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    with app.app_context():
        print("Adding classe column to authorized_athletes table...")
        
        try:
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT COUNT(*) as count
                FROM pragma_table_info('authorized_athletes')
                WHERE name='classe'
            """))
            
            exists = result.scalar() > 0
            
            if exists:
                print("⚠️  Column 'classe' already exists, skipping...")
                return
            
            # Add column
            db.session.execute(text("""
                ALTER TABLE authorized_athletes
                ADD COLUMN classe VARCHAR(10)
            """))
            
            # Set default value for existing records
            db.session.execute(text("""
                UPDATE authorized_athletes
                SET classe = 'CO'
                WHERE classe IS NULL
            """))
            
            db.session.commit()
            print("✅ Column 'classe' added successfully!")
            print("✅ Existing records updated with default value 'CO'")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            raise

def downgrade():
    """Remove classe column from authorized_athletes table"""
    
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    with app.app_context():
        print("Removing classe column from authorized_athletes table...")
        
        # SQLite doesn't support DROP COLUMN directly
        # We need to recreate the table without the column
        print("⚠️  SQLite doesn't support DROP COLUMN.")
        print("⚠️  To remove the column, you need to recreate the table.")
        print("⚠️  This operation is not automated to prevent data loss.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
