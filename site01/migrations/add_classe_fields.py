"""
Migration: Add classe fields for athlete competition class and subscription age class
Created: 2025-10-10

Adds:
- authorized_athletes.classe (Competition class: CO, OL, AN)
- competition_subscriptions.classe (Age class: GM, GF, RM, RF, AM, AF, JM, JF, SM, SF, MM, MF)

Usage:
    python migrations/add_classe_fields.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def upgrade():
    """Add classe fields"""
    
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    with app.app_context():
        print("Adding classe fields...")
        
        # Add classe to authorized_athletes
        try:
            db.session.execute(text("""
                ALTER TABLE authorized_athletes 
                ADD COLUMN classe VARCHAR(10)
            """))
            print("✅ Added classe column to authorized_athletes")
        except Exception as e:
            print(f"⚠️  Column might already exist in authorized_athletes: {e}")
        
        # Add classe to competition_subscriptions
        try:
            db.session.execute(text("""
                ALTER TABLE competition_subscriptions 
                ADD COLUMN classe VARCHAR(10)
            """))
            print("✅ Added classe column to competition_subscriptions")
        except Exception as e:
            print(f"⚠️  Column might already exist in competition_subscriptions: {e}")
        
        db.session.commit()
        print("✅ Migration completed successfully!")

def downgrade():
    """Remove classe fields"""
    
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    with app.app_context():
        print("Removing classe fields...")
        
        # SQLite doesn't support DROP COLUMN directly, so we need to recreate tables
        # For now, just print a warning
        print("⚠️  WARNING: SQLite doesn't support DROP COLUMN.")
        print("⚠️  To downgrade, you need to recreate the tables without classe columns.")
        print("⚠️  This migration cannot be automatically reversed.")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
