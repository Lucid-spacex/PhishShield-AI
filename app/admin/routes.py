"""
Admin routes for PhishShield AI.
Handles system administration functions: Monitor System Activity, View All Scan Records, Manage User Accounts.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc
from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.models.user import User
from app.models.scan_record import ScanRecord
from app.utils import admin_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/scans', methods=['GET'])
@jwt_required()
@admin_required
def get_all_scans():
    """
    Get paginated list of all scan records across all users (Admin only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        minimum: 1
        description: Page number
      - in: query
        name: per_page
        type: integer
        default: 20
        minimum: 1
        maximum: 100
        description: Number of items per page
    responses:
      200:
        description: All scan records retrieved successfully
        schema:
          type: object
          properties:
            scans:
              type: array
              items:
                type: object
                properties:
                  scan_id:
                    type: integer
                    example: 1
                  user_id:
                    type: integer
                    example: 1
                  username:
                    type: string
                    example: johndoe
                  email:
                    type: string
                    example: john@example.com
                  url_scanned:
                    type: string
                    example: https://www.google.com
                  risk_score:
                    type: number
                    format: float
                    example: 0.95
                  result:
                    type: string
                    enum: [phishing, legitimate]
                    example: legitimate
                  scan_time:
                    type: string
                    format: date-time
                    example: 2024-01-01T00:00:00
            total:
              type: integer
              description: Total number of scans
              example: 100
            pages:
              type: integer
              description: Total number of pages
              example: 5
            current_page:
              type: integer
              description: Current page number
              example: 1
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
      403:
        description: Admin access required
        schema:
          type: object
          properties:
            error:
              type: string
              example: Admin access required
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Failed to get all scans
    """
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Validate pagination
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        # Query all scans with user information
        pagination = db.session.query(
            ScanRecord, User
        ).join(
            User, ScanRecord.user_id == User.user_id
        ).order_by(
            desc(ScanRecord.scan_time)
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        scans = []
        for scan, user in pagination.items:
            scan_dict = scan.to_dict(include_features=False)
            scan_dict['username'] = user.username
            scan_dict['email'] = user.email
            scans.append(scan_dict)
        
        return jsonify({
            'scans': scans,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get all scans', 'message': str(e)}), 500


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_all_users():
    """
    Get paginated list of all registered users (Admin only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: query
        name: page
        type: integer
        default: 1
        minimum: 1
        description: Page number
      - in: query
        name: per_page
        type: integer
        default: 20
        minimum: 1
        maximum: 100
        description: Number of items per page
    responses:
      200:
        description: All users retrieved successfully
        schema:
          type: object
          properties:
            users:
              type: array
              items:
                type: object
                properties:
                  user_id:
                    type: integer
                    example: 1
                  username:
                    type: string
                    example: johndoe
                  email:
                    type: string
                    example: john@example.com
                  role:
                    type: string
                    enum: [user, admin]
                    example: user
                  created_at:
                    type: string
                    format: date-time
                    example: 2024-01-01T00:00:00
                  total_scans:
                    type: integer
                    description: Total number of scans by this user
                    example: 15
            total:
              type: integer
              description: Total number of users
              example: 50
            pages:
              type: integer
              description: Total number of pages
              example: 3
            current_page:
              type: integer
              description: Current page number
              example: 1
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
      403:
        description: Admin access required
        schema:
          type: object
          properties:
            error:
              type: string
              example: Admin access required
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Failed to get all users
    """
    try:
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Validate pagination
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        # Query users with scan count
        subquery = db.session.query(
            ScanRecord.user_id,
            func.count(ScanRecord.scan_id).label('scan_count')
        ).group_by(ScanRecord.user_id).subquery()
        
        pagination = db.session.query(
            User, func.coalesce(subquery.c.scan_count, 0).label('total_scans')
        ).outerjoin(
            subquery, User.user_id == subquery.c.user_id
        ).order_by(
            desc(User.created_at)
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        users = []
        for user, scan_count in pagination.items:
            user_dict = user.to_dict()
            user_dict['total_scans'] = scan_count
            users.append(user_dict)
        
        return jsonify({
            'users': users,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get all users', 'message': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """
    Delete a user account (Admin only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: User ID to delete
    responses:
      200:
        description: User deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: User deleted successfully
            deleted_scans:
              type: integer
              description: Number of scan records deleted (cascade)
              example: 15
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
      403:
        description: Admin access required
        schema:
          type: object
          properties:
            error:
              type: string
              example: Admin access required
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: User not found
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Failed to delete user
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Prevent admin from deleting themselves
        if current_user_id == user_id:
            return jsonify({'error': 'Cannot delete your own account'}), 400
        
        # Get user
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Count scan records to be deleted
        scan_count = ScanRecord.query.filter_by(user_id=user_id).count()
        
        # Delete user (cascade will delete scan records and ML features)
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User deleted successfully',
            'deleted_scans': scan_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user', 'message': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['PATCH'])
@jwt_required()
@admin_required
def update_user(user_id):
    """
    Update a user account (Admin only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
        description: User ID to update
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            role:
              type: string
              enum: [user, admin]
              description: User role
              example: admin
            is_active:
              type: boolean
              description: Account active status
              example: true
    responses:
      200:
        description: User updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: User updated successfully
            user:
              type: object
              properties:
                user_id:
                  type: integer
                  example: 1
                username:
                  type: string
                  example: johndoe
                email:
                  type: string
                  example: john@example.com
                role:
                  type: string
                  example: admin
                created_at:
                  type: string
                  format: date-time
                  example: 2024-01-01T00:00:00
      400:
        description: Invalid request
        schema:
          type: object
          properties:
            error:
              type: string
              example: Invalid role value
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
      403:
        description: Admin access required
        schema:
          type: object
          properties:
            error:
              type: string
              example: Admin access required
      404:
        description: User not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: User not found
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Failed to update user
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Prevent admin from demoting themselves
        if current_user_id == user_id:
            return jsonify({'error': 'Cannot modify your own account'}), 400
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Get user
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Update role if provided
        if 'role' in data:
            if data['role'] not in ['user', 'admin']:
                return jsonify({'error': 'Invalid role value'}), 400
            user.role = data['role']
        
        # Note: is_active functionality could be added in future
        # For now, we focus on role management
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update user', 'message': str(e)}), 500


@admin_bp.route('/activity', methods=['GET'])
@jwt_required()
@admin_required
def get_system_activity():
    """
    Get system-wide activity statistics (Admin only)
    ---
    tags:
      - Admin
    security:
      - Bearer: []
    responses:
      200:
        description: System activity statistics retrieved successfully
        schema:
          type: object
          properties:
            total_users:
              type: integer
              description: Total number of registered users
              example: 50
            total_scans:
              type: integer
              description: Total number of scans performed
              example: 1000
            scans_last_24h:
              type: integer
              description: Number of scans in the last 24 hours
              example: 45
            scans_last_7d:
              type: integer
              description: Number of scans in the last 7 days
              example: 230
            phishing_count:
              type: integer
              description: Total phishing URLs detected
              example: 150
            legitimate_count:
              type: integer
              description: Total legitimate URLs detected
              example: 850
            phishing_ratio:
              type: number
              format: float
              description: Percentage of phishing URLs
              example: 15.0
            most_active_users:
              type: array
              items:
                type: object
              description: Top 5 most active users
              example:
                - user_id: 1
                  username: johndoe
                  scan_count: 50
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
      403:
        description: Admin access required
        schema:
          type: object
          properties:
            error:
              type: string
              example: Admin access required
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Failed to get system activity
    """
    try:
        # Total users
        total_users = User.query.count()
        
        # Total scans
        total_scans = ScanRecord.query.count()
        
        # Scans in last 24 hours
        day_ago = datetime.now(timezone.utc) - timedelta(days=1)
        scans_last_24h = ScanRecord.query.filter(ScanRecord.scan_time >= day_ago).count()
        
        # Scans in last 7 days
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        scans_last_7d = ScanRecord.query.filter(ScanRecord.scan_time >= week_ago).count()
        
        # Phishing vs legitimate counts
        phishing_count = ScanRecord.query.filter_by(result='phishing').count()
        legitimate_count = ScanRecord.query.filter_by(result='legitimate').count()
        
        # Phishing ratio
        phishing_ratio = 0.0
        if total_scans > 0:
            phishing_ratio = (phishing_count / total_scans) * 100
        
        # Most active users (top 5)
        most_active_users = db.session.query(
            User.user_id,
            User.username,
            func.count(ScanRecord.scan_id).label('scan_count')
        ).join(
            ScanRecord, User.user_id == ScanRecord.user_id
        ).group_by(
            User.user_id, User.username
        ).order_by(
            desc('scan_count')
        ).limit(5).all()
        
        most_active_users_list = [
            {
                'user_id': user_id,
                'username': username,
                'scan_count': scan_count
            }
            for user_id, username, scan_count in most_active_users
        ]
        
        return jsonify({
            'total_users': total_users,
            'total_scans': total_scans,
            'scans_last_24h': scans_last_24h,
            'scans_last_7d': scans_last_7d,
            'phishing_count': phishing_count,
            'legitimate_count': legitimate_count,
            'phishing_ratio': round(phishing_ratio, 2),
            'most_active_users': most_active_users_list
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get system activity', 'message': str(e)}), 500