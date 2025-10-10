"""
Migration: Add authorized_athletes table
Created: 2025-10-10

This migration adds a table to store which athletes each user is authorized to manage.
This is a website-level feature that can be used across all sections (archery, shop, etc.)

Usage:
    python migrations/add_authorized_athletes.py
"""

from app import app, db
from sqlalchemy import text

def upgrade():
    """Create authorized_athletes table"""
    
    with app.app_context():
        print("Creating authorized_athletes table...")
        
        # Create table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS authorized_athletes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                tessera_atleta VARCHAR(10) NOT NULL,
                nome_atleta VARCHAR(100) NOT NULL,
                cognome_atleta VARCHAR(100) NOT NULL,
                data_nascita DATE,
                categoria VARCHAR(10),
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (added_by) REFERENCES users(id) ON DELETE SET NULL,
                
                UNIQUE(user_id, tessera_atleta)
            )
        """))
        
        # Create indexes
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_authorized_athletes_user 
            ON authorized_athletes(user_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_authorized_athletes_tessera 
            ON authorized_athletes(tessera_atleta)
        """))
        
        db.session.commit()
        print("✅ Table authorized_athletes created successfully!")
        print("✅ Indexes created successfully!")

def downgrade():
    """Drop authorized_athletes table"""
    
    with app.app_context():
        print("Dropping authorized_athletes table...")
        
        db.session.execute(text("DROP TABLE IF EXISTS authorized_athletes"))
        db.session.commit()
        
        print("✅ Table authorized_athletes dropped successfully!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
