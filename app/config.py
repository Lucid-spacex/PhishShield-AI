"""
Configuration settings for PhishShield AI Flask application.
Environment-based configuration for development and production.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration."""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours in seconds
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    JWT_IDENTITY_CLAIM = 'sub'
    
    # Database settings
    # Support both Postgres (Neon) and SQLite for local development
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    if DATABASE_URL:
        # Use Postgres (Neon) - typically from production environment
        # Ensure SSL mode is set for Neon compatibility
        if 'sslmode' not in DATABASE_URL:
            if '?' in DATABASE_URL:
                SQLALCHEMY_DATABASE_URI = DATABASE_URL + '&sslmode=require'
            else:
                SQLALCHEMY_DATABASE_URI = DATABASE_URL + '?sslmode=require'
        else:
            SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Fallback to SQLite for local development
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'phishshield.db')
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Connection pool configuration for Neon Postgres
    # Neon recommends smaller pool sizes for serverless
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 5,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_recycle': 3600,  # Recycle connections after 1 hour
        'pool_pre_ping': True,  # Verify connections before using
    }
    
    # Model settings
    MODEL_PATH = os.environ.get('MODEL_PATH') or 'models/phishshield_model.pkl'
    
    # CORS settings
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Security settings
    BCRYPT_LOG_ROUNDS = 13
    
    # Pagination
    ITEMS_PER_PAGE = 20


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Override these in production with proper environment variables
    # SECRET_KEY = os.environ.get('SECRET_KEY')
    # JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = 3600  # 1 hour for tests
    MODEL_PATH = None  # Don't load actual model in tests
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config(env_name=None):
    """Get configuration based on environment name."""
    if env_name is None:
        env_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(env_name, DevelopmentConfig)
