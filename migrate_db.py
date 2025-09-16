#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database migration script to add last_login field to User model
Run this script to update existing database schema
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add last_login column to users table if it doesn't exist"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    
    if not os.path.exists(db_path):
        print("Database file not found. The database will be created when the app runs.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if last_login column exists
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_login' not in columns:
            print("Adding last_login column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN last_login DATETIME")
            conn.commit()
            print("✅ Successfully added last_login column")
        else:
            print("✅ last_login column already exists")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🔄 Running database migration...")
    migrate_database()
    print("✅ Migration completed!")