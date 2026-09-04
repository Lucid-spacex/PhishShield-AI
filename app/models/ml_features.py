"""
ML_Features model for storing extracted URL features.
This table's columns mirror the output of url_features.extract_features().
"""

from app.extensions import db


class ML_Features(db.Model):
    """Model for storing ML features extracted from URLs."""
    
    __tablename__ = 'ml_features'
    
    feature_id = db.Column(db.Integer, primary_key=True)
    scan_id = db.Column(db.Integer, db.ForeignKey('scan_records.scan_id'), nullable=False, unique=True, index=True)
    
    # Features from url_features.extract_features()
    url_length = db.Column(db.Integer, nullable=False)
    domain_entropy = db.Column(db.Float, nullable=False)
    has_https = db.Column(db.Integer, nullable=False)  # Stored as 0/1 for SQLite compatibility
    has_ip_address = db.Column(db.Integer, nullable=False)  # Stored as 0/1
    dot_count = db.Column(db.Integer, nullable=False)
    subdomain_count = db.Column(db.Integer, nullable=False)
    special_char_count = db.Column(db.Integer, nullable=False)
    redirect_count = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        """Convert features to dictionary."""
        return {
            'feature_id': self.feature_id,
            'scan_id': self.scan_id,
            'url_length': self.url_length,
            'domain_entropy': self.domain_entropy,
            'has_https': bool(self.has_https),
            'has_ip_address': bool(self.has_ip_address),
            'dot_count': self.dot_count,
            'subdomain_count': self.subdomain_count,
            'special_char_count': self.special_char_count,
            'redirect_count': self.redirect_count
        }
    
    @classmethod
    def from_feature_dict(cls, scan_id, feature_dict):
        """Create ML_Features instance from feature dictionary."""
        return cls(
            scan_id=scan_id,
            url_length=feature_dict.get('url_length', 0),
            domain_entropy=feature_dict.get('domain_entropy', 0.0),
            has_https=int(feature_dict.get('has_https', 0)),
            has_ip_address=int(feature_dict.get('has_ip_address', 0)),
            dot_count=feature_dict.get('dot_count', 0),
            subdomain_count=feature_dict.get('subdomain_count', 0),
            special_char_count=feature_dict.get('special_char_count', 0),
            redirect_count=feature_dict.get('redirect_count', 0)
        )
    
    def __repr__(self):
        return f'<ML_Features {self.feature_id} for scan {self.scan_id}>'
