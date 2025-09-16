#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check database schema to verify the last_login column exists
"""

import sqlite3
import os

def check_schema():
    """Check the current database schema"""
    
    db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    
    if not os.path.exists(db_path):
        print("Database file not found.")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table info
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        
        print("Current user table schema:")
        for column in columns:
            print(f"  {column[1]} ({column[2]}) - {'NOT NULL' if column[3] else 'NULL'}")
        
        # Check if last_login exists
        column_names = [column[1] for column in columns]
        
        if 'last_login' in column_names:
            print("\n✅ last_login column exists")
        else:
            print("\n❌ last_login column missing")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    check_schema()