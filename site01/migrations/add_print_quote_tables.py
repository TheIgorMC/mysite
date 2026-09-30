#!/usr/bin/env python3
"""
Migration: Add 3D print quote calculator tables
Creates print_materials, print_settings, and print_quote_requests tables.
"""

import sqlite3
import os
import sys

db_path = os.environ.get('DATABASE_URL', 'sqlite:////app/data/orion.db')
db_path = db_path.replace('sqlite:///', '')

print(f"Running migration: add_print_quote_tables")
print(f"Database: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='print_materials'")
    if not cursor.fetchone():
        print("Creating print_materials table...")
        cursor.execute("""
            CREATE TABLE print_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(128) NOT NULL,
                density_g_cm3 REAL NOT NULL,
                price_per_kg REAL NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ print_materials table created")
    else:
        print("✓ print_materials table already exists")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='print_settings'")
    if not cursor.fetchone():
        print("Creating print_settings table...")
        cursor.execute("""
            CREATE TABLE print_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                infill_percent REAL DEFAULT 20.0,
                setup_fee REAL DEFAULT 0.0,
                minimum_price REAL DEFAULT 5.0,
                max_build_x_mm REAL DEFAULT 220.0,
                max_build_y_mm REAL DEFAULT 220.0,
                max_build_z_mm REAL DEFAULT 250.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ print_settings table created")
        print("Seeding default print_settings row...")
        cursor.execute("INSERT INTO print_settings (infill_percent, setup_fee, minimum_price, max_build_x_mm, max_build_y_mm, max_build_z_mm) VALUES (20.0, 0.0, 5.0, 220.0, 220.0, 250.0)")
        print("✓ Default settings row inserted")
    else:
        print("✓ print_settings table already exists")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='print_quote_requests'")
    if not cursor.fetchone():
        print("Creating print_quote_requests table...")
        cursor.execute("""
            CREATE TABLE print_quote_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                material_id INTEGER,
                project_name VARCHAR(256),
                notes TEXT,
                quantity INTEGER DEFAULT 1,
                original_filename VARCHAR(256),
                stored_filename VARCHAR(256),
                volume_cm3 REAL,
                bbox_x_mm REAL,
                bbox_y_mm REAL,
                bbox_z_mm REAL,
                fits_build_volume BOOLEAN,
                weight_g REAL,
                estimated_price REAL,
                status VARCHAR(32) DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (material_id) REFERENCES print_materials(id)
            )
        """)
        print("✓ print_quote_requests table created")

        print("Creating index on print_quote_requests.user_id...")
        cursor.execute("CREATE INDEX idx_print_quote_requests_user_id ON print_quote_requests(user_id)")
        print("✓ Index created")
    else:
        print("✓ print_quote_requests table already exists")

    conn.commit()
    print("Migration completed successfully!")

except Exception as e:
    print(f"Error during migration: {e}")
    sys.exit(1)
finally:
    conn.close()
