"""
Analytics routes for PhishShield AI.
Provides dashboard data and statistics for Chart.js visualization.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, extract
from app.extensions import db
from app.models.scan_record import ScanRecord
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """
    Get summary statistics for the current user
    ---
    tags:
      - Analytics
    security:
      - Bearer: []
    responses:
      200:
        description: Summary statistics retrieved successfully
        schema:
          type: object
          properties:
            total_scans:
              type: integer
              description: Total number of scans performed
              example: 100
            phishing_count:
              type: integer
              description: Number of phishing URLs detected
              example: 25
            legitimate_count:
              type: integer
              description: Number of legitimate URLs
              example: 75
            protection_rate:
              type: number
              format: float
              description: Percentage of phishing detected
              example: 25.0
            recent_scans:
              type: integer
              description: Number of scans in the last 7 days
              example: 10
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Failed to get summary
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Total scans
        total_scans = ScanRecord.query.filter_by(user_id=current_user_id).count()
        
        # Phishing vs legitimate counts
        phishing_count = ScanRecord.query.filter_by(
            user_id=current_user_id,
            result='phishing'
        ).count()
        
        legitimate_count = ScanRecord.query.filter_by(
            user_id=current_user_id,
            result='legitimate'
        ).count()
        
        # Protection rate (phishing detected / total scans)
        protection_rate = 0.0
        if total_scans > 0:
            protection_rate = (phishing_count / total_scans) * 100
        
        # Recent scans (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_scans = ScanRecord.query.filter(
            ScanRecord.user_id == current_user_id,
            ScanRecord.scan_time >= week_ago
        ).count()
        
        return jsonify({
            'total_scans': total_scans,
            'phishing_count': phishing_count,
            'legitimate_count': legitimate_count,
            'protection_rate': round(protection_rate, 2),
            'recent_scans': recent_scans
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get summary', 'message': str(e)}), 500


@analytics_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    """
    Get scan trends over time for time-series chart
    ---
    tags:
      - Analytics
    security:
      - Bearer: []
    parameters:
      - in: query
        name: period
        type: string
        enum: [daily, weekly]
        default: daily
        description: Time period for grouping
      - in: query
        name: days
        type: integer
        default: 30
        minimum: 1
        maximum: 365
        description: Number of days to include
    responses:
      200:
        description: Trends data retrieved successfully
        schema:
          type: object
          properties:
            dates:
              type: array
              items:
                type: string
                format: date
              description: Array of date strings
              example: ["2024-01-01", "2024-01-02"]
            phishing_counts:
              type: array
              items:
                type: integer
              description: Array of phishing counts per date
              example: [5, 3]
            legitimate_counts:
              type: array
              items:
                type: integer
              description: Array of legitimate counts per date
              example: [20, 15]
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Failed to get trends
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get query parameters
        period = request.args.get('period', 'daily')
        days = request.args.get('days', 30, type=int)
        
        # Validate parameters
        if period not in ['daily', 'weekly']:
            period = 'daily'
        if days < 1 or days > 365:
            days = 30
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        if period == 'daily':
            # Group by day
            trends = db.session.query(
                func.date(ScanRecord.scan_time).label('date'),
                ScanRecord.result,
                func.count(ScanRecord.scan_id).label('count')
            ).filter(
                ScanRecord.user_id == current_user_id,
                ScanRecord.scan_time >= start_date
            ).group_by(
                func.date(ScanRecord.scan_time),
                ScanRecord.result
            ).order_by(func.date(ScanRecord.scan_time)).all()
            
            # Format results for Chart.js
            date_counts = {}
            for date, result, count in trends:
                # SQLite's func.date() returns a string, so use it directly
                date_str = str(date) if not isinstance(date, str) else date
                if date_str not in date_counts:
                    date_counts[date_str] = {'phishing': 0, 'legitimate': 0}
                date_counts[date_str][result] = count
            
            # Fill in missing dates
            dates = []
            phishing_counts = []
            legitimate_counts = []
            
            current_date = start_date.date()
            while current_date <= end_date.date():
                date_str = current_date.isoformat()
                dates.append(date_str)
                
                if date_str in date_counts:
                    phishing_counts.append(date_counts[date_str]['phishing'])
                    legitimate_counts.append(date_counts[date_str]['legitimate'])
                else:
                    phishing_counts.append(0)
                    legitimate_counts.append(0)
                
                current_date += timedelta(days=1)
        
        else:  # weekly
            # For SQLite, we'll group by week manually
            scans = ScanRecord.query.filter(
                ScanRecord.user_id == current_user_id,
                ScanRecord.scan_time >= start_date
            ).all()
            
            # Group by week
            week_counts = {}
            for scan in scans:
                # Get week start (Monday)
                week_start = scan.scan_time - timedelta(days=scan.scan_time.weekday())
                week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
                week_str = week_start.isoformat()
                
                if week_str not in week_counts:
                    week_counts[week_str] = {'phishing': 0, 'legitimate': 0}
                week_counts[week_str][scan.result] += 1
            
            dates = sorted(week_counts.keys())
            phishing_counts = [week_counts[date]['phishing'] for date in dates]
            legitimate_counts = [week_counts[date]['legitimate'] for date in dates]
        
        return jsonify({
            'dates': dates,
            'phishing_counts': phishing_counts,
            'legitimate_counts': legitimate_counts
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get trends', 'message': str(e)}), 500


@analytics_bp.route('/risk-distribution', methods=['GET'])
@jwt_required()
def get_risk_distribution():
    """
    Get distribution of risk scores for visualization
    ---
    tags:
      - Analytics
    security:
      - Bearer: []
    responses:
      200:
        description: Risk distribution retrieved successfully
        schema:
          type: object
          properties:
            low_risk:
              type: integer
              description: Number of scans with risk score 0.0-0.3
              example: 50
            medium_risk:
              type: integer
              description: Number of scans with risk score 0.3-0.7
              example: 30
            high_risk:
              type: integer
              description: Number of scans with risk score 0.7-1.0
              example: 20
      401:
        description: Unauthorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Unauthorized
      500:
        description: Server error
        schema:
          type: object
          properties:
            error:
              type: string
              example: Failed to get risk distribution
    """
    try:
        current_user_id = int(get_jwt_identity())
        
        # Get all risk scores
        scans = ScanRecord.query.filter_by(user_id=current_user_id).all()
        
        low_risk = 0  # 0.0 - 0.3
        medium_risk = 0  # 0.3 - 0.7
        high_risk = 0  # 0.7 - 1.0
        
        for scan in scans:
            score = scan.risk_score
            if score < 0.3:
                low_risk += 1
            elif score < 0.7:
                medium_risk += 1
            else:
                high_risk += 1
        
        return jsonify({
            'low_risk': low_risk,
            'medium_risk': medium_risk,
            'high_risk': high_risk
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get risk distribution', 'message': str(e)}), 500
