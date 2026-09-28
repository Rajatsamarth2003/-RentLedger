import os
import sqlite3

from config import DATABASE_PATH, DATABASE_FOLDER


def get_db():
    os.makedirs(DATABASE_FOLDER, exist_ok=True)

    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()

    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS families (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            default_rent REAL NOT NULL DEFAULT 0,
            move_in_date TEXT NOT NULL,
            move_out_date TEXT,
            status TEXT NOT NULL DEFAULT 'Active'
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            family_id INTEGER NOT NULL,
            month TEXT NOT NULL,

            previous_reading REAL NOT NULL DEFAULT 0,
            current_reading REAL NOT NULL DEFAULT 0,

            calculated_units REAL NOT NULL DEFAULT 0,
            entered_units REAL NOT NULL DEFAULT 0,

            electricity_rate REAL NOT NULL,
            rent REAL NOT NULL DEFAULT 0,

            electricity_bill REAL NOT NULL DEFAULT 0,
            total_amount REAL NOT NULL DEFAULT 0,

            meter_image TEXT,
            ocr_reading REAL,
            ocr_confidence REAL,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (family_id) REFERENCES families(id)
        )
    """)

    # Keep the original local admin account available for existing installs.
    # New users can register through /signup.
    default_admin_hash = (
        "pbkdf2:sha256:600000$01a00a9e592ebd93dbe9a8f863f20939"
        "$0351ff4bc3be05041e767bdd15bb07255cd841410c534efdfb8ae669727ee6df"
    )
    db.execute(
        "INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
        ("admin", default_admin_hash)
    )

    db.commit()
    db.close()
