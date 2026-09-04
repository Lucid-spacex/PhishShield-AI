"""
Migration script to add role field to users table.
This script adds the role column to existing databases without data loss.
"""

import sys
import os
import sqlite3

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User


def migrate_add_role():
    """Add role field to users table if it doesn't exist."""
    
    app = create_app('development')
    
    with app.app_context():
        # Get database path from config
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
        else:
            db_path = db_uri.replace('sqlite://', '')
        
        print(f"Database path: {db_path}")
        
        # Create all tables first if they don't exist
        db.create_all()
        print("Database tables created/verified.")
        
        # Check if database file exists
        if not os.path.exists(db_path):
            print(f"Database file does not exist at {db_path}")
            print("Creating database with new schema...")
            db.create_all()
            print("Database created with role field included.")
            return
        
        # Connect to database directly to check/add column
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if role column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'role' in columns:
            print("Role column already exists in users table.")
            conn.close()
            return
        
        print("Adding role column to users table...")
        
        # Add role column with default value 'user'
        cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL")
        
        conn.commit()
        conn.close()
        
        print("Role column added successfully.")
        
        # Update existing users to have 'user' role
        users = User.query.all()
        for user in users:
            if not hasattr(user, 'role') or user.role is None:
                user.role = 'user'
        
        db.session.commit()
        print(f"Updated {len(users)} existing users with 'user' role.")


if __name__ == '__main__':
    migrate_add_role()