#!/usr/bin/env python
import sys
import os

print("=" * 50)
print("Starting migration...")
print("=" * 50)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Importing app and db...")
    from app import app, db
    from sqlalchemy import text
    print("✓ Imports successful")
    
    print("\nConnecting to database...")
    with app.app_context():
        print("✓ App context created")
        
        try:
            print("\nAdding reset_token column...")
            db.session.execute(text('ALTER TABLE users ADD COLUMN reset_token VARCHAR(256)'))
            db.session.commit()
            print("✓ Added reset_token")
        except Exception as e:
            print(f"⚠ reset_token: {str(e)}")
            db.session.rollback()
        
        try:
            print("\nAdding reset_token_expiry column...")
            db.session.execute(text('ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME'))
            db.session.commit()
            print("✓ Added reset_token_expiry")
        except Exception as e:
            print(f"⚠ reset_token_expiry: {str(e)}")
            db.session.rollback()
        
        try:
            print("\nCreating index...")
            db.session.execute(text('CREATE INDEX ix_users_reset_token ON users(reset_token)'))
            db.session.commit()
            print("✓ Created index")
        except Exception as e:
            print(f"⚠ index: {str(e)}")
            db.session.rollback()
        
        print("\n" + "=" * 50)
        print("✅ Migration complete!")
        print("=" * 50)
        
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
