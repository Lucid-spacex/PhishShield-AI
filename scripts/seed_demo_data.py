"""
Seed script for PhishShield AI demo data.
Creates a test user and sample scan records for testing the API.
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Add the parent directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.scan_record import ScanRecord
from app.models.ml_features import ML_Features

def seed_demo_data():
    """Seed the database with demo data for testing."""
    
    app = create_app('development')
    
    with app.app_context():
        # Get database path and delete it to ensure clean schema
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            db_path = db_uri.replace('sqlite:///', '')
        else:
            db_path = db_uri.replace('sqlite://', '')
        
        # Delete existing database to ensure clean schema with role field
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(f"Deleted existing database: {db_path}")
            except Exception as e:
                print(f"Warning: Could not delete database file: {e}")
        
        # Drop all tables and recreate with new schema
        db.drop_all()
        db.create_all()
        print("Database created with new schema including role field.")
        
        print("Seeding demo data...")
        
        # Create demo user
        demo_user = User(
            username='demouser',
            email='demo@phishshield.ai',
            role='user'
        )
        demo_user.set_password('DemoPassword123!')
        db.session.add(demo_user)
        db.session.flush()
        
        print(f"Created demo user: {demo_user.username} (ID: {demo_user.user_id})")
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@phishshield.ai',
            role='admin'
        )
        admin_user.set_password('AdminPassword123!')
        db.session.add(admin_user)
        db.session.flush()
        
        print(f"Created admin user: {admin_user.username} (ID: {admin_user.user_id})")
        
        # Sample legitimate URLs
        legitimate_urls = [
            {
                'url': 'https://www.google.com',
                'risk_score': 0.95,
                'result': 'legitimate',
                'features': {
                    'url_length': 22,
                    'domain_entropy': 2.5,
                    'has_https': 1,
                    'has_ip_address': 0,
                    'dot_count': 2,
                    'subdomain_count': 1,
                    'special_char_count': 0,
                    'redirect_count': 0
                }
            },
            {
                'url': 'https://github.com',
                'risk_score': 0.92,
                'result': 'legitimate',
                'features': {
                    'url_length': 18,
                    'domain_entropy': 2.8,
                    'has_https': 1,
                    'has_ip_address': 0,
                    'dot_count': 1,
                    'subdomain_count': 0,
                    'special_char_count': 0,
                    'redirect_count': 0
                }
            },
            {
                'url': 'https://www.amazon.com',
                'risk_score': 0.94,
                'result': 'legitimate',
                'features': {
                    'url_length': 22,
                    'domain_entropy': 2.6,
                    'has_https': 1,
                    'has_ip_address': 0,
                    'dot_count': 2,
                    'subdomain_count': 1,
                    'special_char_count': 0,
                    'redirect_count': 0
                }
            },
            {
                'url': 'https://stackoverflow.com',
                'risk_score': 0.91,
                'result': 'legitimate',
                'features': {
                    'url_length': 26,
                    'domain_entropy': 3.1,
                    'has_https': 1,
                    'has_ip_address': 0,
                    'dot_count': 1,
                    'subdomain_count': 0,
                    'special_char_count': 0,
                    'redirect_count': 0
                }
            },
            {
                'url': 'https://www.linkedin.com',
                'risk_score': 0.93,
                'result': 'legitimate',
                'features': {
                    'url_length': 24,
                    'domain_entropy': 2.9,
                    'has_https': 1,
                    'has_ip_address': 0,
                    'dot_count': 2,
                    'subdomain_count': 1,
                    'special_char_count': 0,
                    'redirect_count': 0
                }
            }
        ]
        
        # Sample phishing URLs
        phishing_urls = [
            {
                'url': 'http://192.168.1.1/login',
                'risk_score': 0.85,
                'result': 'phishing',
                'features': {
                    'url_length': 24,
                    'domain_entropy': 1.5,
                    'has_https': 0,
                    'has_ip_address': 1,
                    'dot_count': 3,
                    'subdomain_count': 0,
                    'special_char_count': 1,
                    'redirect_count': 0
                }
            },
            {
                'url': 'http://secure-login-verify-account.com',
                'risk_score': 0.88,
                'result': 'phishing',
                'features': {
                    'url_length': 42,
                    'domain_entropy': 4.2,
                    'has_https': 0,
                    'has_ip_address': 0,
                    'dot_count': 1,
                    'subdomain_count': 0,
                    'special_char_count': 4,
                    'redirect_count': 0
                }
            },
            {
                'url': 'http://www.paypal-secure-login.abc.com/update',
                'risk_score': 0.82,
                'result': 'phishing',
                'features': {
                    'url_length': 48,
                    'domain_entropy': 3.8,
                    'has_https': 0,
                    'has_ip_address': 0,
                    'dot_count': 4,
                    'subdomain_count': 2,
                    'special_char_count': 2,
                    'redirect_count': 1
                }
            }
        ]
        
        # Create scan records with timestamps spread over the past week
        base_time = datetime.now(timezone.utc)
        
        for i, url_data in enumerate(legitimate_urls):
            scan_time = base_time - timedelta(days=i)
            scan = ScanRecord(
                user_id=demo_user.user_id,
                url_scanned=url_data['url'],
                risk_score=url_data['risk_score'],
                result=url_data['result'],
                scan_time=scan_time
            )
            db.session.add(scan)
            db.session.commit()  # Commit to get the scan_id
            
            features = ML_Features.from_feature_dict(scan.scan_id, url_data['features'])
            db.session.add(features)
            db.session.commit()  # Commit the features
            print(f"Created legitimate scan: {url_data['url']}")
        
        for i, url_data in enumerate(phishing_urls):
            scan_time = base_time - timedelta(days=i + 2)
            scan = ScanRecord(
                user_id=demo_user.user_id,
                url_scanned=url_data['url'],
                risk_score=url_data['risk_score'],
                result=url_data['result'],
                scan_time=scan_time
            )
            db.session.add(scan)
            db.session.commit()  # Commit to get the scan_id
            
            features = ML_Features.from_feature_dict(scan.scan_id, url_data['features'])
            db.session.add(features)
            db.session.commit()  # Commit the features
            print(f"Created phishing scan: {url_data['url']}")
        
        print("\nDemo data seeded successfully!")
        print(f"Regular User: demouser / DemoPassword123!")
        print(f"Admin User: admin / AdminPassword123!")
        print(f"Total scans created: {len(legitimate_urls) + len(phishing_urls)}")
        print(f"Legitimate: {len(legitimate_urls)}, Phishing: {len(phishing_urls)}")
        print("\nYou can now use these credentials to test the API:")
        print("  POST /api/auth/login")
        print('  {"username": "demouser", "password": "DemoPassword123!"}')
        print('  {"username": "admin", "password": "AdminPassword123!"}')


if __name__ == '__main__':
    seed_demo_data()