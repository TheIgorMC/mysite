#!/usr/bin/env python3
"""
Database migration script to add tags column to Product and GalleryItem tables.
This script can be run directly on the Orange Pi to update the database schema.

Usage:
    python migrate_add_tags.py
"""

import os
import sys
import sqlite3

def migrate_database():
    """Add tags column to Product and GalleryItem tables if not exists"""
    
    # Get the database path - production database location
    db_path = '/app/data/orion.db'
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        print("Please make sure the database exists at /data/orion.db")
        print("If your database is in a different location, edit this script to update db_path")
        return False
    
    print(f"Connecting to database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Found tables: {', '.join(tables)}")
        
        migrations_performed = []
        
        # Add tags column to products table if it exists and doesn't have the column
        if 'products' in tables:
            cursor.execute("PRAGMA table_info(products)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'tags' not in columns:
                print("\n[products] Adding 'tags' column...")
                cursor.execute("ALTER TABLE products ADD COLUMN tags TEXT")
                migrations_performed.append("Added 'tags' column to products table")
                print("✓ Successfully added 'tags' column to products table")
            else:
                print("\n[products] 'tags' column already exists, skipping")
        else:
            print("\n[products] Table not found, skipping")
        
        # Add tags column to gallery_items table if it exists and doesn't have the column
        if 'gallery_items' in tables:
            cursor.execute("PRAGMA table_info(gallery_items)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'tags' not in columns:
                print("\n[gallery_items] Adding 'tags' column...")
                cursor.execute("ALTER TABLE gallery_items ADD COLUMN tags TEXT")
                migrations_performed.append("Added 'tags' column to gallery_items table")
                print("✓ Successfully added 'tags' column to gallery_items table")
            else:
                print("\n[gallery_items] 'tags' column already exists, skipping")
        else:
            print("\n[gallery_items] Table not found, skipping")
        
        # Commit changes
        conn.commit()
        
        # Display summary
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        
        if migrations_performed:
            print("✓ Migration completed successfully!")
            print("\nChanges made:")
            for i, change in enumerate(migrations_performed, 1):
                print(f"  {i}. {change}")
        else:
            print("✓ Database already up to date - no changes needed")
        
        print("\nThe following features are now available:")
        print("  • Tag system for gallery items")
        print("  • Tag system for shop products")
        print("  • Drag-and-drop image uploads in admin panel")
        print("  • Shop management in admin panel")
        print("="*60)
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"\n✗ Database error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("DATABASE MIGRATION SCRIPT")
    print("Adding tags support for Gallery Items and Products")
    print("="*60)
    print()
    
    success = migrate_database()
    
    if success:
        print("\n✓ You can now restart your Flask application to use the new features!")
        sys.exit(0)
    else:
        print("\n✗ Migration failed. Please check the errors above.")
        sys.exit(1)
