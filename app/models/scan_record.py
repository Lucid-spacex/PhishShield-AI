"""
ScanRecord model for storing URL scan results.
"""

from datetime import datetime
import json
from app.extensions import db


class ScanRecord(db.Model):
    """Model for storing URL scan results."""
    
    __tablename__ = 'scan_records'
    
    scan_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, index=True)
    url_scanned = db.Column(db.Text, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)  # Model's confidence score
    result = db.Column(db.String(20), nullable=False)  # 'legitimate' or 'phishing'
    risk_indicators = db.Column(db.Text)  # JSON string of risk indicators
    scan_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # One-to-one relationship with ML_Features
    ml_features = db.relationship('ML_Features', backref='scan_record', uselist=False, cascade='all, delete-orphan')
    
    def to_dict(self, include_features=False):
        """Convert scan record to dictionary."""
        data = {
            'scan_id': self.scan_id,
            'user_id': self.user_id,
            'url_scanned': self.url_scanned,
            'risk_score': self.risk_score,
            'result': self.result,
            'scan_time': self.scan_time.isoformat() if self.scan_time else None
        }
        
        # Parse risk indicators from JSON if available
        if self.risk_indicators:
            try:
                data['risk_indicators'] = json.loads(self.risk_indicators)
            except:
                data['risk_indicators'] = []
        else:
            data['risk_indicators'] = []
        
        if include_features and self.ml_features:
            data['features'] = self.ml_features.to_dict()
        
        return data
    
    def __repr__(self):
        return f'<ScanRecord {self.scan_id}: {self.result}>'
