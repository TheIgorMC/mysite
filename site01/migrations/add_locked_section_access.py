"""
Migration: Add locked_section_access field to users table

This migration adds a boolean field to control access to highly restricted sections.
Execute with: python migrations/add_locked_section_access.py

SECURITY NOTE: This field defaults to False for all existing users.
Only admins can grant this access via the admin panel.
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def run_migration():
    """Add locked_section_access column to users table"""
    app = create_app()
    
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text("""
                SELECT COUNT(*) as count 
                FROM pragma_table_info('users') 
                WHERE name='has_locked_section_access'
            """))
            
            exists = result.scalar() > 0
            
            if exists:
                print("✓ Column 'has_locked_section_access' already exists")
                return
            
            # Add the column with default value False
            print("Adding 'has_locked_section_access' column to users table...")
            db.session.execute(text("""
                ALTER TABLE users 
                ADD COLUMN has_locked_section_access BOOLEAN DEFAULT 0 NOT NULL
            """))
            
            # Create index for performance
            print("Creating index on 'has_locked_section_access'...")
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_users_locked_section 
                ON users(has_locked_section_access)
            """))
            
            db.session.commit()
            print("✓ Migration completed successfully!")
            print("  - Column 'has_locked_section_access' added")
            print("  - Index created for performance")
            print("  - All existing users have access set to False by default")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Migration failed: {e}")
            raise

if __name__ == '__main__':
    run_migration()
