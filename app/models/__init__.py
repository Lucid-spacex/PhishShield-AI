"""
SQLAlchemy models for PhishShield AI.
"""

from .user import User
from .scan_record import ScanRecord
from .ml_features import ML_Features

__all__ = ['User', 'ScanRecord', 'ML_Features']
