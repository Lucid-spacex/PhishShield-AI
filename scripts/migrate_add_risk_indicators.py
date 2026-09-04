"""
Migration script to add risk_indicators field to scan_records table.
This script adds the risk_indicators column to existing databases without data loss.
"""

import sys
import os
import sqlite3

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db


def migrate_add_risk_indicators():
    """Add risk_indicators field to scan_records table if it doesn't exist."""
    
    app = create_app('development')
    
    with app.app_context():
        # Get database path from config
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
        else:
            db_path = db_uri.replace('sqlite://', '')
        
        print(f"Database path: {db_path}")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            print(f"Database file does not exist at {db_path}")
            print("Creating database with new schema...")
            db.create_all()
            print("Database created with risk_indicators field included.")
            return
        
        # Create all tables first if they don't exist
        db.create_all()
        print("Database tables created/verified.")
        
        # Connect to database directly to check/add column
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if risk_indicators column exists
        cursor.execute("PRAGMA table_info(scan_records)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'risk_indicators' in columns:
            print("risk_indicators column already exists in scan_records table.")
            conn.close()
            return
        
        print("Adding risk_indicators column to scan_records table...")
        
        # Add risk_indicators column (TEXT for JSON storage)
        cursor.execute("ALTER TABLE scan_records ADD COLUMN risk_indicators TEXT")
        
        conn.commit()
        conn.close()
        
        print("risk_indicators column added successfully.")


if __name__ == '__main__':
    migrate_add_risk_indicators()