"""
Startup script to run database migrations before the app starts.
This should be called before the main application starts in production.
"""

import sys
import os
from flask_migrate import upgrade

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

def run_migrations():
    """Run database migrations and health checks."""
    app = create_app()
    
    with app.app_context():
        # Run migrations
        try:
            print("Running database migrations...")
            upgrade()
            print("Database migrations completed successfully")
        except Exception as e:
            print(f"Database migration failed: {e}")
            # Don't fail startup if migration fails, but log it clearly
            print("Warning: Application starting without completed migrations")
        
        # Health check for database tables
        try:
            inspector = db.inspect(db.engine)
            expected_tables = ['users', 'scan_records', 'ml_features']
            existing_tables = inspector.get_table_names()
            
            missing_tables = [table for table in expected_tables if table not in existing_tables]
            if missing_tables:
                print(f"ERROR: Missing database tables: {missing_tables}")
                print("Database schema is incomplete. API may not function correctly.")
                return False
            else:
                print("All expected database tables are present")
                return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False

if __name__ == '__main__':
    success = run_migrations()
    sys.exit(0 if success else 1)