"""
Migration: Add designators field to ELEC_board_components table
Date: 2025-11-19
Description: Adds a 'designators' TEXT field to store comma-separated component designators
"""

import mysql.connector
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

def run_migration():
    """Add designators column to ELEC_board_components"""
    
    conn = mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )
    
    cursor = conn.cursor()
    
    try:
        print("Starting migration: add_designators_to_board_components")
        
        # Check if column already exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'ELEC_board_components' 
            AND COLUMN_NAME = 'designators'
        """, (Config.DB_NAME,))
        
        exists = cursor.fetchone()[0]
        
        if exists:
            print("✓ Column 'designators' already exists in ELEC_board_components")
        else:
            # Add designators column
            print("Adding 'designators' column to ELEC_board_components...")
            cursor.execute("""
                ALTER TABLE ELEC_board_components 
                ADD COLUMN designators TEXT NULL 
                COMMENT 'Comma-separated list of component designators (e.g., R1,R2,R3)'
            """)
            conn.commit()
            print("✓ Added 'designators' column to ELEC_board_components")
        
        print("Migration completed successfully!")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
