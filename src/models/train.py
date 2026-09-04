"""
Model training script for PhishShield AI.
Trains Logistic Regression, Random Forest, and XGBoost models with cross-validation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Set random seed for reproducibility
RANDOM_STATE = 42


def load_data(features_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """
    Load the features dataset and separate features from labels.
    
    Args:
        features_path: Path to the features CSV file
        
    Returns:
        Tuple of (X, y) where X is features and y is labels
    """
    logger.info(f"Loading features from {features_path}")
    
    df = pd.read_csv(features_path)
    logger.info(f"Dataset shape: {df.shape}")
    logger.info(f"Columns: {df.columns.tolist()}")
    
    # Separate features and labels
    X = df.drop('label', axis=1)
    y = df['label']
    
    logger.info(f"Features shape: {X.shape}")
    logger.info(f"Labels shape: {y.shape}")
    logger.info(f"Label distribution:\n{y.value_counts()}")
    
    return X, y


def split_data(X: pd.DataFrame, y: pd.Series, test_size: float = 0.2) -> tuple:
    """
    Split data into train and test sets with stratification.
    
    Args:
        X: Feature matrix
        y: Label vector
        test_size: Proportion of data to use for testing
        
    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    logger.info(f"Splitting data with test_size={test_size}")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=test_size, 
        random_state=RANDOM_STATE,
        stratify=y  # Stratify to maintain label distribution
    )
    
    logger.info(f"Training set shape: {X_train.shape}")
    logger.info(f"Test set shape: {X_test.shape}")
    logger.info(f"Training label distribution:\n{y_train.value_counts()}")
    logger.info(f"Test label distribution:\n{y_test.value_counts()}")
    
    return X_train, X_test, y_train, y_test


def train_logistic_regression(X_train: pd.DataFrame, y_train: pd.Series) -> Pipeline:
    """
    Train a Logistic Regression model with scaling.
    
    Args:
        X_train: Training features
        y_train: Training labels
        
    Returns:
        Trained model pipeline
    """
    logger.info("Training Logistic Regression model...")
    
    # Create pipeline with scaling
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(
            random_state=RANDOM_STATE,
            max_iter=1000,
            class_weight='balanced'  # Handle potential class imbalance
        ))
    ])
    
    # Train with cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=cv, scoring='f1')
    
    logger.info(f"Logistic Regression CV F1 scores: {cv_scores}")
    logger.info(f"Logistic Regression Mean CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Fit on full training set
    pipeline.fit(X_train, y_train)
    
    return pipeline


def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series) -> RandomForestClassifier:
    """
    Train a Random Forest model.
    
    Args:
        X_train: Training features
        y_train: Training labels
        
    Returns:
        Trained Random Forest model
    """
    logger.info("Training Random Forest model...")
    
    # Random Forest doesn't require scaling
    rf = RandomForestClassifier(
        n_estimators=100,
        random_state=RANDOM_STATE,
        class_weight='balanced',  # Handle potential class imbalance
        n_jobs=-1  # Use all available cores
    )
    
    # Train with cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_scores = cross_val_score(rf, X_train, y_train, cv=cv, scoring='f1')
    
    logger.info(f"Random Forest CV F1 scores: {cv_scores}")
    logger.info(f"Random Forest Mean CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Fit on full training set
    rf.fit(X_train, y_train)
    
    return rf


def train_xgboost(X_train: pd.DataFrame, y_train: pd.Series) -> xgb.XGBClassifier:
    """
    Train an XGBoost model.
    
    Args:
        X_train: Training features
        y_train: Training labels
        
    Returns:
        Trained XGBoost model
    """
    logger.info("Training XGBoost model...")
    
    # XGBoost handles feature scaling internally
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=6,
        random_state=RANDOM_STATE,
        eval_metric='logloss',
        scale_pos_weight=1  # Will be adjusted based on class distribution
    )
    
    # Calculate scale_pos_weight for class imbalance
    # This helps handle imbalanced datasets
    class_counts = y_train.value_counts()
    if len(class_counts) == 2:
        scale_pos_weight = class_counts[0] / class_counts[1]
        xgb_model.set_params(scale_pos_weight=scale_pos_weight)
        logger.info(f"Set scale_pos_weight to {scale_pos_weight:.2f} for class imbalance")
    
    # Train with cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_scores = cross_val_score(xgb_model, X_train, y_train, cv=cv, scoring='f1')
    
    logger.info(f"XGBoost CV F1 scores: {cv_scores}")
    logger.info(f"XGBoost Mean CV F1: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
    
    # Fit on full training set
    xgb_model.fit(X_train, y_train)
    
    return xgb_model


def save_model(model, model_name: str, output_dir: Path) -> Path:
    """
    Save a trained model to disk.
    
    Args:
        model: Trained model object
        model_name: Name for the saved model file
        output_dir: Directory to save the model
        
    Returns:
        Path to the saved model file
    """
    ensure_dir(output_dir)
    
    model_path = output_dir / f"{model_name}.pkl"
    joblib.dump(model, model_path)
    
    logger.info(f"Model saved to {model_path}")
    return model_path


def ensure_dir(directory: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def main():
    """Main function to train all models."""
    # Set up paths
    project_root = Path(__file__).parent.parent.parent
    processed_data_dir = project_root / "data" / "processed"
    models_dir = project_root / "models"
    
    features_path = processed_data_dir / "features.csv"
    
    logger.info("Starting model training pipeline...")
    logger.info(f"Project root: {project_root}")
    
    # Load data
    try:
        X, y = load_data(features_path)
    except Exception as e:
        logger.error(f"Error loading features: {e}")
        logger.error("Please run generate_features.py first to create features.csv")
        return
    
    # Split data
    X_train, X_test, y_train, y_test = split_data(X, y)
    
    # Train models
    models = {}
    
    # Logistic Regression
    lr_model = train_logistic_regression(X_train, y_train)
    models['logistic_regression'] = lr_model
    save_model(lr_model, 'logistic_regression_model', models_dir)
    
    # Random Forest
    rf_model = train_random_forest(X_train, y_train)
    models['random_forest'] = rf_model
    save_model(rf_model, 'random_forest_model', models_dir)
    
    # XGBoost
    xgb_model = train_xgboost(X_train, y_train)
    models['xgboost'] = xgb_model
    save_model(xgb_model, 'xgboost_model', models_dir)
    
    # Save test data for evaluation
    test_data_path = models_dir / "test_data.pkl"
    joblib.dump({
        'X_test': X_test,
        'y_test': y_test,
        'feature_names': X.columns.tolist()
    }, test_data_path)
    logger.info(f"Test data saved to {test_data_path}")
    
    logger.info("Model training complete!")
    logger.info("All models saved to models/ directory")
    logger.info("Run evaluate.py to compare model performance")


if __name__ == "__main__":
    main()
