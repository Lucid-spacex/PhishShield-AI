"""
Flask application factory for PhishShield AI.
"""

from flask import Flask
from flask import jsonify
from app.config import get_config
from app.extensions import db, migrate, jwt, cors, swagger
from app.models import User, ScanRecord, ML_Features


def create_app(config_name=None):
    """Create and configure the Flask application."""
    
    # Get configuration
    config = get_config(config_name)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    
    # Initialize Swagger for API documentation
    # Skip Swagger initialization in testing mode
    if not app.config['TESTING']:
        # Set Swagger configuration in app config
        app.config['SWAGGER'] = {
            "headers": [],
            "specs": [
                {
                    "endpoint": 'apispec',
                    "route": '/api/docs.json',
                    "rule_filter": lambda rule: True,
                    "model_filter": lambda tag: True,
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/api/docs"
        }
        
        app.config['SWAGGER_TEMPLATE'] = {
            "swagger": "2.0",
            "info": {
                "title": "PhishShield AI API",
                "description": "Machine learning-powered phishing detection API",
                "version": "1.0.0",
                "contact": {
                    "name": "PhishShield AI Team"
                }
            },
            "securityDefinitions": {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "JWT authorization header using the Bearer scheme. Example: 'Bearer {token}'"
                }
            }
        }
        
        try:
            swagger.init_app(app)
            app.logger.info("Swagger documentation initialized at /api/docs")
        except Exception as e:
            app.logger.warning(f"Swagger initialization failed: {e}")
            app.logger.info("Continuing without Swagger documentation")
    else:
        app.logger.info("Swagger documentation disabled in testing mode")
    
    # Initialize ML predictor (skip for testing)
    from app.ml.predictor import PhishingPredictor
    if app.config['MODEL_PATH']:
        try:
            app.predictor = PhishingPredictor(app.config['MODEL_PATH'])
        except Exception as e:
            app.logger.error(f"Failed to initialize ML predictor: {e}")
            app.predictor = None
    else:
        app.predictor = None
        app.logger.info("ML predictor skipped (testing mode)")
    
    # Register blueprints
    from app.auth.routes import auth_bp
    from app.scan.routes import scan_bp
    from app.analytics.routes import analytics_bp
    from app.admin.routes import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(scan_bp, url_prefix='/api/scan')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request', 'message': str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': str(error)}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': str(error)}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found', 'message': str(error)}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'service': 'PhishShield AI API'})
    
    # API health endpoint with version info
    @app.route('/api/health')
    def api_health():
        """
        API Health Check
        ---
        tags:
          - Health
        responses:
          200:
            description: API is healthy and running
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: healthy
                service:
                  type: string
                  example: PhishShield AI API
                version:
                  type: string
                  example: 1.0.0
                model:
                  type: string
                  example: logistic_regression
        """
        model_info = "unknown"
        if hasattr(app, 'predictor') and app.predictor:
            model_info = app.predictor.model_type if hasattr(app.predictor, 'model_type') else "loaded"
        
        return jsonify({
            'status': 'healthy',
            'service': 'PhishShield AI API',
            'version': '1.0.0',
            'model': model_info
        })
    
    return app
