"""
Final model serialization script for PhishShield AI.
Selects the best model and saves it as the production model with all necessary artifacts.
"""

import json
import joblib
from pathlib import Path
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_evaluation_report(report_path: Path) -> dict:
    """
    Load the evaluation report to determine the best model.
    
    Args:
        report_path: Path to the evaluation report JSON file
        
    Returns:
        Dictionary containing evaluation results
    """
    logger.info(f"Loading evaluation report from {report_path}")
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    best_model_name = report['best_model']
    logger.info(f"Best model identified: {best_model_name}")
    
    return report, best_model_name


def load_model_and_artifacts(model_path: Path, model_name: str) -> tuple:
    """
    Load the best model and any preprocessing artifacts.
    
    Args:
        model_path: Path to the model file
        model_name: Name of the model
        
    Returns:
        Tuple of (model, artifacts_dict)
    """
    logger.info(f"Loading best model from {model_path}")
    
    model = joblib.load(model_path)
    
    # Extract preprocessing artifacts if present (e.g., from sklearn Pipeline)
    artifacts = {}
    
    if hasattr(model, 'named_steps'):
        # This is a Pipeline, extract the scaler
        if 'scaler' in model.named_steps:
            artifacts['scaler'] = model.named_steps['scaler']
            logger.info("Extracted scaler from pipeline")
    
    logger.info(f"Model and artifacts loaded successfully")
    
    return model, artifacts


def save_production_model(model: str, artifacts: dict, feature_names: list, 
                          best_model_name: str, output_dir: Path) -> Path:
    """
    Save the production model with all necessary components for inference.
    
    Args:
        model: Trained model object
        artifacts: Dictionary of preprocessing artifacts
        feature_names: List of feature names for validation
        best_model_name: Name of the best model (for metadata)
        output_dir: Directory to save the production model
        
    Returns:
        Path to the saved production model
    """
    ensure_dir(output_dir)
    
    # Create production package
    production_package = {
        'model': model,
        'artifacts': artifacts,
        'feature_names': feature_names,
        'model_type': best_model_name,
        'metadata': {
            'model_name': best_model_name,
            'description': 'PhishShield AI phishing detection model',
            'version': '1.0',
            'features': feature_names
        }
    }
    
    # Save production model
    production_path = output_dir / "phishshield_model.pkl"
    joblib.dump(production_package, production_path)
    
    logger.info(f"Production model saved to {production_path}")
    logger.info(f"Package includes: model, artifacts, feature names, and metadata")
    
    return production_path


def load_test_data(test_data_path: Path) -> dict:
    """
    Load test data to get feature names.
    
    Args:
        test_data_path: Path to test data pickle file
        
    Returns:
        Dictionary containing test data
    """
    logger.info(f"Loading test data from {test_data_path}")
    test_data = joblib.load(test_data_path)
    return test_data


def ensure_dir(directory: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def main():
    """Main function to finalize the production model."""
    # Set up paths
    project_root = Path(__file__).parent.parent.parent
    models_dir = project_root / "models"
    
    evaluation_report_path = models_dir / "evaluation_report.json"
    test_data_path = models_dir / "test_data.pkl"
    
    logger.info("Starting production model finalization...")
    logger.info(f"Project root: {project_root}")
    
    # Load evaluation report
    try:
        report, best_model_name = load_evaluation_report(evaluation_report_path)
    except Exception as e:
        logger.error(f"Error loading evaluation report: {e}")
        logger.error("Please run evaluate.py first to generate evaluation_report.json")
        return
    
    # Load test data to get feature names
    try:
        test_data = load_test_data(test_data_path)
        feature_names = test_data['feature_names']
        logger.info(f"Feature names: {feature_names}")
    except Exception as e:
        logger.error(f"Error loading test data: {e}")
        return
    
    # Determine model file path
    model_filename = f"{best_model_name}_model.pkl"
    model_path = models_dir / model_filename
    
    if not model_path.exists():
        logger.error(f"Best model file not found: {model_path}")
        return
    
    # Load best model and artifacts
    try:
        model, artifacts = load_model_and_artifacts(model_path, best_model_name)
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return
    
    # Save production model
    try:
        production_path = save_production_model(
            model, artifacts, feature_names, best_model_name, models_dir
        )
    except Exception as e:
        logger.error(f"Error saving production model: {e}")
        return
    
    logger.info("=" * 80)
    logger.info("PRODUCTION MODEL FINALIZATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Best model: {best_model_name}")
    logger.info(f"Production model saved to: {production_path}")
    logger.info(f"Number of features: {len(feature_names)}")
    logger.info(f"Features: {feature_names}")
    logger.info("=" * 80)
    logger.info("The production model is ready for deployment in the Flask backend.")
    logger.info("It includes the model, preprocessing artifacts, and feature metadata.")


if __name__ == "__main__":
    main()
