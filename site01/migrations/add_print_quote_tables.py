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

    def add_column_if_missing(table, column_def):
        col_name = column_def.split()[0]
        cursor.execute(f"PRAGMA table_info({table})")
        existing = [c[1] for c in cursor.fetchall()]
        if col_name not in existing:
            print(f"Adding {col_name} to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='print_materials'")
    if not cursor.fetchone():
        print("Creating print_materials table...")
        cursor.execute("""
            CREATE TABLE print_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(128) NOT NULL,
                technology VARCHAR(16) NOT NULL DEFAULT 'fdm',
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
        add_column_if_missing('print_materials', "technology VARCHAR(16) NOT NULL DEFAULT 'fdm'")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='print_settings'")
    if not cursor.fetchone():
        print("Creating print_settings table...")
        cursor.execute("""
            CREATE TABLE print_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                infill_percent REAL DEFAULT 20.0,
                resin_fill_percent REAL DEFAULT 100.0,
                setup_fee REAL DEFAULT 0.0,
                minimum_price REAL DEFAULT 5.0,
                multi_material_fee_per_extra REAL DEFAULT 0.0,
                max_build_x_mm REAL DEFAULT 220.0,
                max_build_y_mm REAL DEFAULT 220.0,
                max_build_z_mm REAL DEFAULT 250.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ print_settings table created")
        print("Seeding default print_settings row...")
        cursor.execute("""
            INSERT INTO print_settings
                (infill_percent, resin_fill_percent, setup_fee, minimum_price, multi_material_fee_per_extra, max_build_x_mm, max_build_y_mm, max_build_z_mm)
            VALUES (20.0, 100.0, 0.0, 5.0, 0.0, 220.0, 220.0, 250.0)
        """)
        print("✓ Default settings row inserted")
    else:
        print("✓ print_settings table already exists")
        add_column_if_missing('print_settings', "resin_fill_percent REAL DEFAULT 100.0")
        add_column_if_missing('print_settings', "multi_material_fee_per_extra REAL DEFAULT 0.0")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='print_printers'")
    printers_table_is_new = not cursor.fetchone()
    if printers_table_is_new:
        print("Creating print_printers table...")
        cursor.execute("""
            CREATE TABLE print_printers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(128) NOT NULL,
                technology VARCHAR(16) NOT NULL DEFAULT 'fdm',
                max_build_x_mm REAL NOT NULL,
                max_build_y_mm REAL NOT NULL,
                max_build_z_mm REAL NOT NULL,
                max_materials INTEGER DEFAULT 1,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ print_printers table created")

        # Seed one printer from the old single global build volume, if this
        # site already ran an earlier version of this migration, so existing
        # setups don't suddenly have zero printers (= everything "doesn't fit").
        cursor.execute("PRAGMA table_info(print_settings)")
        old_settings_cols = [c[1] for c in cursor.fetchall()]
        if 'max_build_x_mm' in old_settings_cols:
            cursor.execute("SELECT max_build_x_mm, max_build_y_mm, max_build_z_mm FROM print_settings LIMIT 1")
            row = cursor.fetchone()
            if row:
                print("Seeding a default printer from the previous global build volume...")
                cursor.execute("""
                    INSERT INTO print_printers (name, technology, max_build_x_mm, max_build_y_mm, max_build_z_mm, max_materials, is_active)
                    VALUES ('Stampante 1', 'fdm', ?, ?, ?, 1, 1)
                """, row)
                print("✓ Default printer inserted — rename it and add the other two in the admin panel")
    else:
        print("✓ print_printers table already exists")

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='print_quote_requests'")
    if not cursor.fetchone():
        print("Creating print_quote_requests table...")
        cursor.execute("""
            CREATE TABLE print_quote_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                material_id INTEGER,
                printer_id INTEGER,
                project_name VARCHAR(256),
                notes TEXT,
                quantity INTEGER DEFAULT 1,
                original_filename VARCHAR(256),
                stored_filename VARCHAR(256),
                file_format VARCHAR(8),
                volume_cm3 REAL,
                bbox_x_mm REAL,
                bbox_y_mm REAL,
                bbox_z_mm REAL,
                fits_build_volume BOOLEAN,
                fit_reason VARCHAR(32),
                weight_g REAL,
                detected_material_count INTEGER DEFAULT 1,
                estimated_price REAL,
                status VARCHAR(32) DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (material_id) REFERENCES print_materials(id),
                FOREIGN KEY (printer_id) REFERENCES print_printers(id)
            )
        """)
        print("✓ print_quote_requests table created")

        print("Creating index on print_quote_requests.user_id...")
        cursor.execute("CREATE INDEX idx_print_quote_requests_user_id ON print_quote_requests(user_id)")
        print("✓ Index created")
    else:
        print("✓ print_quote_requests table already exists")
        add_column_if_missing('print_quote_requests', "file_format VARCHAR(8)")
        add_column_if_missing('print_quote_requests', "detected_material_count INTEGER DEFAULT 1")
        add_column_if_missing('print_quote_requests', "printer_id INTEGER REFERENCES print_printers(id)")
        add_column_if_missing('print_quote_requests', "fit_reason VARCHAR(32)")

    conn.commit()
    print("Migration completed successfully!")

except Exception as e:
    print(f"Error during migration: {e}")
    sys.exit(1)
finally:
    conn.close()
