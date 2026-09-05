"""
Entry point for running the PhishShield AI Flask application.
"""

import os
import sys
from app import create_app

# Run database migrations before starting the app
def run_startup_migrations():
    """Run database migrations and health checks before app startup."""
    print("Running database migrations...")
    try:
        from scripts.startup_migrations import run_migrations
        success = run_migrations()
        if not success:
            print("Warning: Database health check failed, but starting app anyway...")
    except Exception as e:
        print(f"Migration script failed: {e}")
        print("Starting app without migrations...")

# Create the Flask app
app = create_app()

if __name__ == '__main__':
    # Run migrations on startup (except in test mode)
    if os.environ.get('FLASK_ENV') != 'testing':
        run_startup_migrations()
    
    # Run the development server
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"\n{'='*50}")
    print(f"PhishShield AI API Server")
    print(f"{'='*50}")
    print(f"Server running at: http://127.0.0.1:{port}")
    print(f"Swagger docs available at: http://127.0.0.1:{port}/api/docs")
    print(f"Health check: http://127.0.0.1:{port}/api/health")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
