"""
Utility functions and decorators for PhishShield AI.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from app.models.user import User
from app.extensions import db


def admin_required(f):
    """
    Decorator to require admin role for endpoint access.
    
    Usage:
        @admin_required
        @jwt_required()
        def protected_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = db.session.get(User, current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    
    return decorated_function