#!/usr/bin/env python3
"""
Migration: Add product variants support
Adds variant_config column to products table and creates product_variants table
"""

import sqlite3
import os
import sys

# Get the database path
db_path = os.environ.get('DATABASE_URL', 'sqlite:////app/data/orion.db')
db_path = db_path.replace('sqlite:///', '')

print(f"Running migration: add_product_variants")
print(f"Database: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if variant_config column already exists
    cursor.execute("PRAGMA table_info(products)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'variant_config' not in columns:
        print("Adding variant_config column to products table...")
        cursor.execute("ALTER TABLE products ADD COLUMN variant_config TEXT")
        print("✓ variant_config column added")
    else:
        print("✓ variant_config column already exists")
    
    # Check if product_variants table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_variants'")
    if not cursor.fetchone():
        print("Creating product_variants table...")
        cursor.execute("""
            CREATE TABLE product_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                attributes TEXT NOT NULL,
                price_modifier REAL DEFAULT 0.0,
                sku VARCHAR(128),
                stock_quantity INTEGER,
                in_stock BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)
        print("✓ product_variants table created")
        
        print("Creating index on product_variants.product_id...")
        cursor.execute("CREATE INDEX idx_product_variants_product_id ON product_variants(product_id)")
        print("✓ Index created")
    else:
        print("✓ product_variants table already exists")
    
    conn.commit()
    print("Migration completed successfully!")
    
except Exception as e:
    print(f"Error during migration: {e}")
    sys.exit(1)
finally:
    conn.close()
