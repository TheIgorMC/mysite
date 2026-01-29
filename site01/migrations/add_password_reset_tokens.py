"""Add password reset token fields to users table

This migration adds reset_token and reset_token_expiry columns to the users table.
Can be run safely multiple times (checks if columns exist first).

Usage:
    python migrations/add_password_reset_tokens.py
"""

import sys
import os

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from sqlalchemy import text

def upgrade():
    """Add password reset columns if they don't exist"""
    with app.app_context():
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        print(f"Current columns in 'users' table: {columns}")
        
        if 'reset_token' not in columns:
            print("Adding 'reset_token' column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN reset_token VARCHAR(256)'))
                conn.commit()
            print("✓ Added 'reset_token' column")
        else:
            print("✓ Column 'reset_token' already exists")
        
        if 'reset_token_expiry' not in columns:
            print("Adding 'reset_token_expiry' column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME'))
                conn.commit()
            print("✓ Added 'reset_token_expiry' column")
        else:
            print("✓ Column 'reset_token_expiry' already exists")
        
        # Check and create index
        indexes = [idx['name'] for idx in inspector.get_indexes('users')]
        if 'ix_users_reset_token' not in indexes:
            print("Creating index on 'reset_token'...")
            with db.engine.connect() as conn:
                conn.execute(text('CREATE INDEX ix_users_reset_token ON users(reset_token)'))
                conn.commit()
            print("✓ Created index 'ix_users_reset_token'")
        else:
            print("✓ Index 'ix_users_reset_token' already exists")
        
        print("\n✅ Migration completed successfully!")


def downgrade():
    """Remove password reset columns"""
    with app.app_context():
        inspector = db.inspect(db.engine)
        
        # Check and drop index
        indexes = [idx['name'] for idx in inspector.get_indexes('users')]
        if 'ix_users_reset_token' in indexes:
            print("Dropping index 'ix_users_reset_token'...")
            with db.engine.connect() as conn:
                conn.execute(text('DROP INDEX ix_users_reset_token'))
                conn.commit()
            print("✓ Dropped index")
        
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'reset_token_expiry' in columns:
            print("Dropping 'reset_token_expiry' column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users DROP COLUMN reset_token_expiry'))
                conn.commit()
            print("✓ Dropped column")
        
        if 'reset_token' in columns:
            print("Dropping 'reset_token' column...")
            with db.engine.connect() as conn:
                conn.execute(text('ALTER TABLE users DROP COLUMN reset_token'))
                conn.commit()
            print("✓ Dropped column")
        
        print("\n✅ Rollback completed successfully!")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        print("Running downgrade (removing columns)...")
        downgrade()
    else:
        print("Running upgrade (adding columns)...")
        upgrade()
