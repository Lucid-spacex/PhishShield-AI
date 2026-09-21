"""
ML predictor module for PhishShield AI.
Loads the production model package and wraps url_features for inference.
"""

import joblib
import numpy as np
import pandas as pd
import logging
import warnings
from pathlib import Path
from typing import Dict, Tuple
import sys

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from features.url_features import extract_features

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress sklearn warnings about version differences
warnings.filterwarnings('ignore', category=UserWarning, module='sklearn')


class PhishingPredictor:
    """Phishing URL predictor using the trained model."""
    
    def __init__(self, model_path: str):
        """
        Initialize the predictor with the model package.
        
        Args:
            model_path: Path to the production model package (.pkl file)
        """
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.model_type = None
        self._load_model()
    
    def _load_model(self):
        """Load the model package from disk."""
        try:
            logger.info(f"Loading model package from {self.model_path}")
            
            # Load the production package
            package = joblib.load(self.model_path)
            
            # Extract components
            self.model = package['model']
            self.scaler = package.get('artifacts', {}).get('scaler')
            self.feature_names = package['feature_names']
            self.model_type = package['model_type']
            
            logger.info(f"Model loaded successfully: {self.model_type}")
            logger.info(f"Features: {self.feature_names}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def predict(self, url: str) -> Dict:
        """
        Predict if a URL is phishing or legitimate.
        
        Args:
            url: URL string to analyze
            
        Returns:
            Dictionary containing:
                - label: 'phishing' or 'legitimate'
                - confidence_score: Model confidence (0-1)
                - features: Extracted feature values
                - risk_indicators: List of suspicious features
        """
        try:
            # Extract features
            features = extract_features(url)
            
            # Validate feature keys against expected feature names
            self._validate_features(features)
            
            # Prepare feature vector in correct order
            feature_vector = self._prepare_feature_vector(features)
            
            # Apply scaling if available
            if self.scaler is not None:
                # Convert to numpy array and reshape for scaler
                feature_array = np.array(feature_vector).reshape(1, -1)
                feature_vector = self.scaler.transform(feature_array)[0]
            else:
                feature_vector = np.array(feature_vector)
            
            # Get prediction
            prediction = self.model.predict([feature_vector])[0]
            
            # Get confidence score (probability)
            if hasattr(self.model, 'predict_proba'):
                probabilities = self.model.predict_proba([feature_vector])[0]
                confidence = max(probabilities)
            else:
                # For models without predict_proba, use decision function or default
                confidence = 0.9  # Default high confidence
            
            # Convert prediction to label
            label = 'phishing' if prediction == 1 else 'legitimate'
            
            # Generate risk indicators
            risk_indicators = self._generate_risk_indicators(features, label)
            
            logger.info(f"Prediction for {url}: label={label}, confidence={confidence:.4f}")
            
            return {
                'label': label,
                'confidence_score': float(confidence),
                'features': features,
                'risk_indicators': risk_indicators
            }
            
        except Exception as e:
            logger.error(f"Error during prediction for {url}: {e}")
            # Re-raise with more context
            raise ValueError(f"Prediction failed for URL '{url}': {str(e)}")
    
    def _validate_features(self, features: Dict):
        """
        Validate that extracted features match expected feature names.
        
        Args:
            features: Extracted feature dictionary
            
        Raises:
            ValueError: If feature keys don't match expected names
        """
        expected_features = set(self.feature_names)
        actual_features = set(features.keys())
        
        if expected_features != actual_features:
            missing = expected_features - actual_features
            extra = actual_features - expected_features
            
            error_msg = "Feature mismatch detected. "
            if missing:
                error_msg += f"Missing features: {missing}. "
            if extra:
                error_msg += f"Extra features: {extra}. "
            
            logger.error(error_msg)
            logger.error(f"Expected: {expected_features}")
            logger.error(f"Actual: {actual_features}")
            raise ValueError(error_msg)
    
    def _prepare_feature_vector(self, features: Dict) -> list:
        """
        Prepare feature vector in the correct order for the model.
        
        Args:
            features: Feature dictionary
            
        Returns:
            List of feature values in the correct order
        """
        return [features[feature] for feature in self.feature_names]
    
    def _generate_risk_indicators(self, features: Dict, label: str) -> list:
        """
        Generate human-readable risk indicators based on features.
        
        Args:
            features: Extracted feature dictionary
            label: Predicted label
            
        Returns:
            List of risk indicator strings
        """
        indicators = []
        
        if label == 'phishing':
            # High entropy domain
            if features.get('domain_entropy', 0) > 3.0:
                indicators.append("High domain entropy (suspicious randomness)")
            
            # No HTTPS
            if features.get('has_https', 0) == 0:
                indicators.append("Missing HTTPS encryption")
            
            # IP address instead of domain
            if features.get('has_ip_address', 0) == 1:
                indicators.append("Uses IP address instead of domain name")
            
            # Many subdomains
            if features.get('subdomain_count', 0) > 2:
                indicators.append("Unusual number of subdomains")
            
            # Many special characters
            if features.get('special_char_count', 0) > 5:
                indicators.append("Excessive special characters in URL")
            
            # Many dots
            if features.get('dot_count', 0) > 5:
                indicators.append("Unusual number of dots in URL")
            
            # Redirect indicators
            if features.get('redirect_count', 0) > 0:
                indicators.append("Potential redirect patterns detected")
            
            # Very long URL
            if features.get('url_length', 0) > 100:
                indicators.append("Unusually long URL")
            
            # If no specific indicators but still phishing
            if not indicators:
                indicators.append("General phishing pattern detected")
        
        return indicators


# Global predictor instance (loaded at app startup)
_predictor_instance = None


def get_predictor(model_path: str = None) -> PhishingPredictor:
    """
    Get or create the global predictor instance.
    
    Args:
        model_path: Path to model file (only needed on first call)
        
    Returns:
        PhishingPredictor instance
    """
    global _predictor_instance
    
    if _predictor_instance is None:
        if model_path is None:
            raise ValueError("Model path required for first initialization")
        _predictor_instance = PhishingPredictor(model_path)
    
    return _predictor_instance


def initialize_predictor(model_path: str):
    """
    Initialize the global predictor instance.
    
    Args:
        model_path: Path to the model file
    """
    global _predictor_instance
    _predictor_instance = PhishingPredictor(model_path)
    logger.info("Global predictor initialized")
