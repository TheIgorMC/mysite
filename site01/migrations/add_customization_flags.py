"""
Migration: Add customization flags to products table
Date: 2025-10-27
Description: Adds is_custom_string and is_custom_print boolean flags to enable customizers
"""

import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def run_migration():
    """Add customization flags to products table"""
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'orion_db')
    }
    
    try:
        # Connect to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Adding customization flags to products table...")
        
        # Add is_custom_string column
        cursor.execute("""
            ALTER TABLE products 
            ADD COLUMN is_custom_string BOOLEAN DEFAULT FALSE
            COMMENT 'Enable string customizer for this product'
        """)
        print("✓ Added is_custom_string column")
        
        # Add is_custom_print column
        cursor.execute("""
            ALTER TABLE products 
            ADD COLUMN is_custom_print BOOLEAN DEFAULT FALSE
            COMMENT 'Enable 3D print customizer for this product'
        """)
        print("✓ Added is_custom_print column")
        
        # Commit changes
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
        # Show table structure
        cursor.execute("DESCRIBE products")
        columns = cursor.fetchall()
        print("\nCurrent products table structure:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
        
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def rollback_migration():
    """Remove customization flags from products table"""
    
    # Database configuration
    db_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'orion_db')
    }
    
    try:
        # Connect to database
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        print("Rolling back customization flags from products table...")
        
        # Remove columns
        cursor.execute("ALTER TABLE products DROP COLUMN is_custom_string")
        print("✓ Removed is_custom_string column")
        
        cursor.execute("ALTER TABLE products DROP COLUMN is_custom_print")
        print("✓ Removed is_custom_print column")
        
        # Commit changes
        conn.commit()
        print("\n✅ Rollback completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
        if conn:
            conn.rollback()
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_migration()
    else:
        run_migration()
