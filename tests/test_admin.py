"""
Tests for Admin endpoints.
Tests admin functionality and access control.
"""

import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.scan_record import ScanRecord
from app.models.ml_features import ML_Features
from datetime import datetime, timezone


@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_app('testing')
    app.config['TESTING'] = True
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def init_db(app):
    """Initialize the database with test data."""
    with app.app_context():
        db.create_all()
        
        # Create regular user
        regular_user = User(
            username='regularuser',
            email='regular@example.com',
            role='user'
        )
        regular_user.set_password('RegularPassword123!')
        db.session.add(regular_user)
        db.session.commit()
        
        # Create admin user
        admin_user = User(
            username='adminuser',
            email='admin@example.com',
            role='admin'
        )
        admin_user.set_password('AdminPassword123!')
        db.session.add(admin_user)
        db.session.commit()
        
        # Create some scan records for regular user
        scan1 = ScanRecord(
            user_id=regular_user.user_id,
            url_scanned='https://www.google.com',
            risk_score=0.95,
            result='legitimate',
            scan_time=datetime.now(timezone.utc)
        )
        db.session.add(scan1)
        db.session.commit()
        
        features1 = ML_Features.from_feature_dict(scan1.scan_id, {
            'url_length': 22,
            'domain_entropy': 2.5,
            'has_https': 1,
            'has_ip_address': 0,
            'dot_count': 2,
            'subdomain_count': 1,
            'special_char_count': 0,
            'redirect_count': 0
        })
        db.session.add(features1)
        db.session.commit()
        
        # Create scan for admin user
        scan2 = ScanRecord(
            user_id=admin_user.user_id,
            url_scanned='https://www.microsoft.com',
            risk_score=0.96,
            result='legitimate',
            scan_time=datetime.now(timezone.utc)
        )
        db.session.add(scan2)
        db.session.commit()
        
        features2 = ML_Features.from_feature_dict(scan2.scan_id, {
            'url_length': 25,
            'domain_entropy': 2.7,
            'has_https': 1,
            'has_ip_address': 0,
            'dot_count': 2,
            'subdomain_count': 1,
            'special_char_count': 0,
            'redirect_count': 0
        })
        db.session.add(features2)
        db.session.commit()
        
        yield regular_user, admin_user
        
        # Cleanup
        db.session.remove()
        db.drop_all()


def get_auth_token(client, username, password):
    """Helper function to get auth token."""
    response = client.post('/api/auth/login', json={
        'username': username,
        'password': password
    })
    data = response.get_json()
    return data.get('access_token')


# Tests for GET /api/admin/scans
def test_get_all_scans_as_admin(client, init_db):
    """Test that admin can view all scans."""
    regular_user, admin_user = init_db
    
    # Login as admin
    admin_token = get_auth_token(client, 'adminuser', 'AdminPassword123!')
    
    # Get all scans
    response = client.get('/api/admin/scans', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'scans' in data
    assert len(data['scans']) == 2  # Both users' scans
    assert data['total'] == 2


def test_get_all_scans_as_regular_user(client, init_db):
    """Test that regular user gets 403 when trying to view all scans."""
    regular_user, admin_user = init_db
    
    # Login as regular user
    regular_token = get_auth_token(client, 'regularuser', 'RegularPassword123!')
    
    # Try to get all scans
    response = client.get('/api/admin/scans', headers={
        'Authorization': f'Bearer {regular_token}'
    })
    
    assert response.status_code == 403
    data = response.get_json()
    assert 'error' in data
    assert 'Admin access required' in data['error']


def test_get_all_scans_without_auth(client, init_db):
    """Test that unauthenticated request gets 401."""
    response = client.get('/api/admin/scans')
    assert response.status_code == 401


# Tests for GET /api/admin/users
def test_get_all_users_as_admin(client, init_db):
    """Test that admin can view all users."""
    regular_user, admin_user = init_db
    
    # Login as admin
    admin_token = get_auth_token(client, 'adminuser', 'AdminPassword123!')
    
    # Get all users
    response = client.get('/api/admin/users', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'users' in data
    assert len(data['users']) == 2  # Both users
    assert data['total'] == 2
    
    # Check that password hashes are not included
    for user in data['users']:
        assert 'password_hash' not in user
        assert 'role' in user


def test_get_all_users_as_regular_user(client, init_db):
    """Test that regular user gets 403 when trying to view all users."""
    regular_user, admin_user = init_db
    
    # Login as regular user
    regular_token = get_auth_token(client, 'regularuser', 'RegularPassword123!')
    
    # Try to get all users
    response = client.get('/api/admin/users', headers={
        'Authorization': f'Bearer {regular_token}'
    })
    
    assert response.status_code == 403
    data = response.get_json()
    assert 'error' in data
    assert 'Admin access required' in data['error']


# Tests for DELETE /api/admin/users/{user_id}
def test_delete_user_as_admin(client, init_db):
    """Test that admin can delete a user."""
    regular_user, admin_user = init_db
    
    # Login as admin
    admin_token = get_auth_token(client, 'adminuser', 'AdminPassword123!')
    
    # Delete regular user
    response = client.delete(f'/api/admin/users/{regular_user.user_id}', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'deleted_scans' in data
    assert data['deleted_scans'] == 1  # Regular user had 1 scan


def test_delete_user_as_regular_user(client, init_db):
    """Test that regular user gets 403 when trying to delete a user."""
    regular_user, admin_user = init_db
    
    # Login as regular user
    regular_token = get_auth_token(client, 'regularuser', 'RegularPassword123!')
    
    # Try to delete admin user
    response = client.delete(f'/api/admin/users/{admin_user.user_id}', headers={
        'Authorization': f'Bearer {regular_token}'
    })
    
    assert response.status_code == 403
    data = response.get_json()
    assert 'error' in data
    assert 'Admin access required' in data['error']


def test_delete_self_as_admin(client, init_db):
    """Test that admin cannot delete their own account."""
    regular_user, admin_user = init_db
    
    # Login as admin
    admin_token = get_auth_token(client, 'adminuser', 'AdminPassword123!')
    
    # Try to delete self
    response = client.delete(f'/api/admin/users/{admin_user.user_id}', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Cannot delete your own account' in data['error']


# Tests for PATCH /api/admin/users/{user_id}
def test_update_user_role_as_admin(client, init_db):
    """Test that admin can update user role."""
    regular_user, admin_user = init_db
    
    # Login as admin
    admin_token = get_auth_token(client, 'adminuser', 'AdminPassword123!')
    
    # Promote regular user to admin
    response = client.patch(f'/api/admin/users/{regular_user.user_id}', 
        json={'role': 'admin'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data
    assert 'user' in data
    assert data['user']['role'] == 'admin'


def test_update_user_role_as_regular_user(client, init_db):
    """Test that regular user gets 403 when trying to update user role."""
    regular_user, admin_user = init_db
    
    # Login as regular user
    regular_token = get_auth_token(client, 'regularuser', 'RegularPassword123!')
    
    # Try to update admin user role
    response = client.patch(f'/api/admin/users/{admin_user.user_id}',
        json={'role': 'user'},
        headers={'Authorization': f'Bearer {regular_token}'}
    )
    
    assert response.status_code == 403
    data = response.get_json()
    assert 'error' in data
    assert 'Admin access required' in data['error']


def test_update_user_role_invalid_value(client, init_db):
    """Test that invalid role value returns 400."""
    regular_user, admin_user = init_db
    
    # Login as admin
    admin_token = get_auth_token(client, 'adminuser', 'AdminPassword123!')
    
    # Try to set invalid role
    response = client.patch(f'/api/admin/users/{regular_user.user_id}',
        json={'role': 'superadmin'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Invalid role value' in data['error']


def test_update_self_as_admin(client, init_db):
    """Test that admin cannot modify their own account."""
    regular_user, admin_user = init_db
    
    # Login as admin
    admin_token = get_auth_token(client, 'adminuser', 'AdminPassword123!')
    
    # Try to modify self
    response = client.patch(f'/api/admin/users/{admin_user.user_id}',
        json={'role': 'user'},
        headers={'Authorization': f'Bearer {admin_token}'}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'Cannot modify your own account' in data['error']


# Tests for GET /api/admin/activity
def test_get_system_activity_as_admin(client, init_db):
    """Test that admin can view system activity."""
    regular_user, admin_user = init_db
    
    # Login as admin
    admin_token = get_auth_token(client, 'adminuser', 'AdminPassword123!')
    
    # Get system activity
    response = client.get('/api/admin/activity', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'total_users' in data
    assert 'total_scans' in data
    assert 'scans_last_24h' in data
    assert 'scans_last_7d' in data
    assert 'phishing_count' in data
    assert 'legitimate_count' in data
    assert 'phishing_ratio' in data
    assert 'most_active_users' in data
    
    assert data['total_users'] == 2
    assert data['total_scans'] == 2


def test_get_system_activity_as_regular_user(client, init_db):
    """Test that regular user gets 403 when trying to view system activity."""
    regular_user, admin_user = init_db
    
    # Login as regular user
    regular_token = get_auth_token(client, 'regularuser', 'RegularPassword123!')
    
    # Try to get system activity
    response = client.get('/api/admin/activity', headers={
        'Authorization': f'Bearer {regular_token}'
    })
    
    assert response.status_code == 403
    data = response.get_json()
    assert 'error' in data
    assert 'Admin access required' in data['error']


# Test pagination
def test_admin_scans_pagination(client, init_db):
    """Test pagination on admin scans endpoint."""
    regular_user, admin_user = init_db
    
    # Login as admin
    admin_token = get_auth_token(client, 'adminuser', 'AdminPassword123!')
    
    # Test with per_page=1
    response = client.get('/api/admin/scans?per_page=1&page=1', headers={
        'Authorization': f'Bearer {admin_token}'
    })
    
    assert response.status_code == 200
    data = response.get_json()
    assert len(data['scans']) == 1
    assert data['total'] == 2
    assert data['pages'] == 2
    assert data['current_page'] == 1