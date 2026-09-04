"""
Unit tests for analytics routes.
"""

import pytest
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.scan_record import ScanRecord
from app.models.ml_features import ML_Features
from unittest.mock import Mock


@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_app('testing')
    app.config['TESTING'] = True
    
    # The app will have predictor=None in testing mode
    # Scan routes will return mock responses
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Create authenticated user and return headers."""
    response = client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'testpassword123'
    })
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def sample_scans(client, auth_headers, app):
    """Create sample scan records for testing."""
    with app.app_context():
        # Get user from database (using username from registration)
        user = User.query.filter_by(username='testuser').first()
        user_id = user.user_id
        
        # Create legitimate scans directly in database
        for i in range(5):
            scan = ScanRecord(
                user_id=user_id,
                url_scanned=f'https://legitimate{i}.com',
                risk_score=0.95,
                result='legitimate'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 20,
                'domain_entropy': 2.5,
                'has_https': 1,
                'has_ip_address': 0,
                'dot_count': 2,
                'subdomain_count': 0,
                'special_char_count': 0,
                'redirect_count': 0
            })
            db.session.add(features)
        
        # Create phishing scans
        for i in range(3):
            scan = ScanRecord(
                user_id=user_id,
                url_scanned=f'http://phishing{i}.com',
                risk_score=0.85,
                result='phishing'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 50,
                'domain_entropy': 4.5,
                'has_https': 0,
                'has_ip_address': 1,
                'dot_count': 5,
                'subdomain_count': 3,
                'special_char_count': 8,
                'redirect_count': 2
            })
            db.session.add(features)
        
        db.session.commit()


def test_get_summary(client, auth_headers, app):
    """Test getting summary statistics."""
    with app.app_context():
        # Get user from database (using username from registration)
        user = User.query.filter_by(username='testuser').first()
        user_id = user.user_id
        
        # Create sample scans directly in database
        for i in range(5):
            scan = ScanRecord(
                user_id=user_id,
                url_scanned=f'https://legitimate{i}.com',
                risk_score=0.95,
                result='legitimate'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 20,
                'domain_entropy': 2.5,
                'has_https': 1,
                'has_ip_address': 0,
                'dot_count': 2,
                'subdomain_count': 0,
                'special_char_count': 0,
                'redirect_count': 0
            })
            db.session.add(features)
        
        for i in range(3):
            scan = ScanRecord(
                user_id=user_id,
                url_scanned=f'http://phishing{i}.com',
                risk_score=0.85,
                result='phishing'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 50,
                'domain_entropy': 4.5,
                'has_https': 0,
                'has_ip_address': 1,
                'dot_count': 5,
                'subdomain_count': 3,
                'special_char_count': 8,
                'redirect_count': 2
            })
            db.session.add(features)
        
        db.session.commit()
    
    response = client.get('/api/analytics/summary', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json
    assert 'total_scans' in data
    assert 'phishing_count' in data
    assert 'legitimate_count' in data
    assert 'protection_rate' in data
    assert 'recent_scans' in data
    
    # Verify counts match our sample data
    assert data['total_scans'] == 8  # 5 legitimate + 3 phishing
    assert data['phishing_count'] == 3
    assert data['legitimate_count'] == 5


def test_get_summary_without_auth(client):
    """Test getting summary without authentication."""
    response = client.get('/api/analytics/summary')
    
    assert response.status_code == 401


def test_get_summary_empty_history(client, auth_headers):
    """Test getting summary with no scan history."""
    response = client.get('/api/analytics/summary', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json
    assert data['total_scans'] == 0
    assert data['phishing_count'] == 0
    assert data['legitimate_count'] == 0
    assert data['protection_rate'] == 0.0


def test_get_trends_daily(client, auth_headers, app):
    """Test getting daily trends."""
    with app.app_context():
        # Get user from database (using username from registration)
        user = User.query.filter_by(username='testuser').first()
        user_id = user.user_id
        
        # Create sample scans
        scan = ScanRecord(
            user_id=user_id,
            url_scanned='https://example.com',
            risk_score=0.95,
            result='legitimate'
        )
        db.session.add(scan)
        db.session.flush()
        
        features = ML_Features.from_feature_dict(scan.scan_id, {
            'url_length': 20,
            'domain_entropy': 2.5,
            'has_https': 1,
            'has_ip_address': 0,
            'dot_count': 2,
            'subdomain_count': 0,
            'special_char_count': 0,
            'redirect_count': 0
        })
        db.session.add(features)
        db.session.commit()
    
    response = client.get('/api/analytics/trends?period=daily&days=7', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json
    assert 'dates' in data
    assert 'phishing_counts' in data
    assert 'legitimate_counts' in data
    
    # Verify arrays have same length
    assert len(data['dates']) == len(data['phishing_counts'])
    assert len(data['dates']) == len(data['legitimate_counts'])
    
    # Verify we have data for the requested period (7 days range includes both endpoints)
    assert len(data['dates']) == 8  # 7 days range includes start and end dates


def test_get_trends_weekly(client, auth_headers, app):
    """Test getting weekly trends."""
    with app.app_context():
        # Get user from database (using username from registration)
        user = User.query.filter_by(username='testuser').first()
        user_id = user.user_id
        
        # Create sample scan
        scan = ScanRecord(
            user_id=user_id,
            url_scanned='https://example.com',
            risk_score=0.95,
            result='legitimate'
        )
        db.session.add(scan)
        db.session.flush()
        
        features = ML_Features.from_feature_dict(scan.scan_id, {
            'url_length': 20,
            'domain_entropy': 2.5,
            'has_https': 1,
            'has_ip_address': 0,
            'dot_count': 2,
            'subdomain_count': 0,
            'special_char_count': 0,
            'redirect_count': 0
        })
        db.session.add(features)
        db.session.commit()
    
    response = client.get('/api/analytics/trends?period=weekly&days=30', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json
    assert 'dates' in data
    assert 'phishing_counts' in data
    assert 'legitimate_counts' in data


def test_get_trends_without_auth(client):
    """Test getting trends without authentication."""
    response = client.get('/api/analytics/trends')
    
    assert response.status_code == 401


def test_get_trends_invalid_period(client, auth_headers):
    """Test getting trends with invalid period (should default to daily)."""
    response = client.get('/api/analytics/trends?period=invalid', headers=auth_headers)
    
    assert response.status_code == 200
    # Should default to daily and not error


def test_get_trends_invalid_days(client, auth_headers):
    """Test getting trends with invalid days parameter."""
    response = client.get('/api/analytics/trends?days=500', headers=auth_headers)
    
    assert response.status_code == 200
    # Should default to max 365 days


def test_get_risk_distribution(client, auth_headers, app):
    """Test getting risk score distribution."""
    with app.app_context():
        # Get user from database (using username from registration)
        user = User.query.filter_by(username='testuser').first()
        user_id = user.user_id
        
        # Create sample scans with different risk scores
        # Low risk
        for i in range(3):
            scan = ScanRecord(
                user_id=user_id,
                url_scanned=f'https://low{i}.com',
                risk_score=0.2,
                result='legitimate'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 20,
                'domain_entropy': 2.5,
                'has_https': 1,
                'has_ip_address': 0,
                'dot_count': 2,
                'subdomain_count': 0,
                'special_char_count': 0,
                'redirect_count': 0
            })
            db.session.add(features)
        
        # Medium risk
        for i in range(3):
            scan = ScanRecord(
                user_id=user_id,
                url_scanned=f'https://medium{i}.com',
                risk_score=0.5,
                result='legitimate'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 20,
                'domain_entropy': 2.5,
                'has_https': 1,
                'has_ip_address': 0,
                'dot_count': 2,
                'subdomain_count': 0,
                'special_char_count': 0,
                'redirect_count': 0
            })
            db.session.add(features)
        
        # High risk
        for i in range(2):
            scan = ScanRecord(
                user_id=user_id,
                url_scanned=f'http://high{i}.com',
                risk_score=0.8,
                result='phishing'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 50,
                'domain_entropy': 4.5,
                'has_https': 0,
                'has_ip_address': 1,
                'dot_count': 5,
                'subdomain_count': 3,
                'special_char_count': 8,
                'redirect_count': 2
            })
            db.session.add(features)
        
        db.session.commit()
    
    response = client.get('/api/analytics/risk-distribution', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json
    assert 'low_risk' in data
    assert 'medium_risk' in data
    assert 'high_risk' in data
    
    # Verify total matches scan count
    total = data['low_risk'] + data['medium_risk'] + data['high_risk']
    assert total == 8  # Our sample scans


def test_get_risk_distribution_without_auth(client):
    """Test getting risk distribution without authentication."""
    response = client.get('/api/analytics/risk-distribution')
    
    assert response.status_code == 401


def test_get_risk_distribution_empty(client, auth_headers):
    """Test getting risk distribution with no scans."""
    response = client.get('/api/analytics/risk-distribution', headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json
    assert data['low_risk'] == 0
    assert data['medium_risk'] == 0
    assert data['high_risk'] == 0


def test_user_isolation_analytics(client, auth_headers, app):
    """Test that analytics only show current user's data."""
    with app.app_context():
        # Create first user and scans
        user1 = User(username='user1', email='user1@example.com')
        user1.set_password('password123')
        db.session.add(user1)
        db.session.flush()
        
        for i in range(3):
            scan = ScanRecord(
                user_id=user1.user_id,
                url_scanned=f'https://user1-{i}.com',
                risk_score=0.95,
                result='legitimate'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 20,
                'domain_entropy': 2.5,
                'has_https': 1,
                'has_ip_address': 0,
                'dot_count': 2,
                'subdomain_count': 0,
                'special_char_count': 0,
                'redirect_count': 0
            })
            db.session.add(features)
        
        # Create second user
        user2 = User(username='user2', email='user2@example.com')
        user2.set_password('password123')
        db.session.add(user2)
        db.session.flush()
        
        for i in range(2):
            scan = ScanRecord(
                user_id=user2.user_id,
                url_scanned=f'https://user2-{i}.com',
                risk_score=0.95,
                result='legitimate'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 20,
                'domain_entropy': 2.5,
                'has_https': 1,
                'has_ip_address': 0,
                'dot_count': 2,
                'subdomain_count': 0,
                'special_char_count': 0,
                'redirect_count': 0
            })
            db.session.add(features)
        
        db.session.commit()
        
        # Get user1's summary
        from flask_jwt_extended import create_access_token
        user1_token = create_access_token(identity=str(user1.user_id))
        user1_headers = {'Authorization': f'Bearer {user1_token}'}
        
        response = client.get('/api/analytics/summary', headers=user1_headers)
        user1_summary = response.json
        
        # Get user2's summary
        user2_token = create_access_token(identity=str(user2.user_id))
        user2_headers = {'Authorization': f'Bearer {user2_token}'}
        
        response = client.get('/api/analytics/summary', headers=user2_headers)
        user2_summary = response.json
        
        # Verify counts are different
        assert user1_summary['total_scans'] == 3
        assert user2_summary['total_scans'] == 2


def test_protection_rate_calculation(client, auth_headers, app):
    """Test protection rate calculation."""
    with app.app_context():
        # Get user from database (using username from registration)
        user = User.query.filter_by(username='testuser').first()
        user_id = user.user_id
        
        # Create equal mix of phishing and legitimate directly in database
        for i in range(5):
            # Phishing scans
            scan = ScanRecord(
                user_id=user_id,
                url_scanned=f'http://phishing{i}.com',
                risk_score=0.85,
                result='phishing'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 50,
                'domain_entropy': 4.5,
                'has_https': 0,
                'has_ip_address': 1,
                'dot_count': 5,
                'subdomain_count': 3,
                'special_char_count': 8,
                'redirect_count': 2
            })
            db.session.add(features)
            
            # Legitimate scans
            scan = ScanRecord(
                user_id=user_id,
                url_scanned=f'https://legitimate{i}.com',
                risk_score=0.95,
                result='legitimate'
            )
            db.session.add(scan)
            db.session.flush()
            
            features = ML_Features.from_feature_dict(scan.scan_id, {
                'url_length': 20,
                'domain_entropy': 2.5,
                'has_https': 1,
                'has_ip_address': 0,
                'dot_count': 2,
                'subdomain_count': 0,
                'special_char_count': 0,
                'redirect_count': 0
            })
            db.session.add(features)
        
        db.session.commit()
    
    response = client.get('/api/analytics/summary', headers=auth_headers)
    data = response.json
    
    # Protection rate should be 50% (5 phishing out of 10 total)
    assert data['total_scans'] == 10
    assert data['phishing_count'] == 5
    assert data['protection_rate'] == 50.0
