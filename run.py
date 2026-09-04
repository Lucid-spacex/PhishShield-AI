"""
Entry point for running the PhishShield AI Flask application.
"""

import os
from app import create_app

# Create the Flask app
app = create_app()

if __name__ == '__main__':
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
