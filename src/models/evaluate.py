"""
Model evaluation script for PhishShield AI.
Evaluates trained models and selects the best performer based on F1 score.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
import joblib
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    confusion_matrix, classification_report
)
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_test_data(test_data_path: Path) -> dict:
    """
    Load the test data saved during training.
    
    Args:
        test_data_path: Path to the test data pickle file
        
    Returns:
        Dictionary containing X_test, y_test, and feature_names
    """
    logger.info(f"Loading test data from {test_data_path}")
    
    test_data = joblib.load(test_data_path)
    
    logger.info(f"Test features shape: {test_data['X_test'].shape}")
    logger.info(f"Test labels shape: {test_data['y_test'].shape}")
    logger.info(f"Test label distribution:\n{test_data['y_test'].value_counts()}")
    
    return test_data


def load_model(model_path: Path, model_name: str):
    """
    Load a trained model from disk.
    
    Args:
        model_path: Path to the model file
        model_name: Name of the model (for logging)
        
    Returns:
        Loaded model object
    """
    logger.info(f"Loading {model_name} from {model_path}")
    model = joblib.load(model_path)
    return model


def evaluate_model(model, X_test: pd.DataFrame, y_test: pd.Series, model_name: str) -> dict:
    """
    Evaluate a model on the test set.
    
    Args:
        model: Trained model object
        X_test: Test features
        y_test: Test labels
        model_name: Name of the model
        
    Returns:
        Dictionary of evaluation metrics
    """
    logger.info(f"Evaluating {model_name}...")
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    # Calculate confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    
    # Generate classification report
    report = classification_report(y_test, y_pred, output_dict=True)
    
    metrics = {
        'model_name': model_name,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'confusion_matrix': cm.tolist(),
        'classification_report': report
    }
    
    logger.info(f"{model_name} Results:")
    logger.info(f"  Accuracy:  {accuracy:.4f}")
    logger.info(f"  Precision: {precision:.4f}")
    logger.info(f"  Recall:    {recall:.4f}")
    logger.info(f"  F1 Score:  {f1:.4f}")
    logger.info(f"  Confusion Matrix:\n{cm}")
    
    return metrics


def compare_models(metrics_list: list) -> pd.DataFrame:
    """
    Compare evaluation metrics across all models.
    
    Args:
        metrics_list: List of metric dictionaries from evaluate_model
        
    Returns:
        DataFrame with comparison table
    """
    logger.info("Comparing model performance...")
    
    # Create comparison table
    comparison_data = []
    for metrics in metrics_list:
        comparison_data.append({
            'Model': metrics['model_name'],
            'Accuracy': metrics['accuracy'],
            'Precision': metrics['precision'],
            'Recall': metrics['recall'],
            'F1 Score': metrics['f1_score']
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    comparison_df = comparison_df.sort_values('F1 Score', ascending=False)
    
    logger.info("\nModel Comparison:")
    logger.info("=" * 80)
    logger.info(comparison_df.to_string(index=False))
    logger.info("=" * 80)
    
    return comparison_df


def select_best_model(metrics_list: list) -> tuple:
    """
    Select the best model based on F1 score.
    
    F1 score is chosen because it balances precision and recall, which is important
    for phishing detection where both false positives and false negatives have costs.
    
    Args:
        metrics_list: List of metric dictionaries from evaluate_model
        
    Returns:
        Tuple of (best_model_name, best_metrics)
    """
    logger.info("Selecting best model based on F1 score...")
    
    # Sort by F1 score
    sorted_metrics = sorted(metrics_list, key=lambda x: x['f1_score'], reverse=True)
    
    best_model_name = sorted_metrics[0]['model_name']
    best_metrics = sorted_metrics[0]
    
    logger.info(f"Best model: {best_model_name}")
    logger.info(f"Best F1 Score: {best_metrics['f1_score']:.4f}")
    
    return best_model_name, best_metrics


def save_evaluation_report(metrics_list: list, comparison_df: pd.DataFrame, 
                          best_model_name: str, output_dir: Path) -> Path:
    """
    Save evaluation report to file.
    
    Args:
        metrics_list: List of metric dictionaries
        comparison_df: Comparison DataFrame
        best_model_name: Name of the best model
        output_dir: Directory to save the report
        
    Returns:
        Path to the saved report
    """
    ensure_dir(output_dir)
    
    # Create comprehensive report
    report = {
        'best_model': best_model_name,
        'model_comparison': comparison_df.to_dict('records'),
        'detailed_metrics': {}
    }
    
    for metrics in metrics_list:
        report['detailed_metrics'][metrics['model_name']] = {
            'accuracy': metrics['accuracy'],
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1_score': metrics['f1_score'],
            'confusion_matrix': metrics['confusion_matrix'],
            'classification_report': metrics['classification_report']
        }
    
    # Save as JSON
    json_path = output_dir / "evaluation_report.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Save as Markdown for human readability
    md_path = output_dir / "evaluation_report.md"
    with open(md_path, 'w') as f:
        f.write("# PhishShield AI - Model Evaluation Report\n\n")
        f.write(f"**Best Model:** {best_model_name}\n\n")
        f.write("## Model Comparison\n\n")
        f.write("| Model | Accuracy | Precision | Recall | F1 Score |\n")
        f.write("|-------|----------|-----------|--------|----------|\n")
        for _, row in comparison_df.iterrows():
            f.write(f"| {row['Model']} | {row['Accuracy']:.4f} | {row['Precision']:.4f} | {row['Recall']:.4f} | {row['F1 Score']:.4f} |\n")
        f.write("\n## Detailed Metrics\n\n")
        
        for metrics in metrics_list:
            f.write(f"### {metrics['model_name']}\n\n")
            f.write(f"- **Accuracy:** {metrics['accuracy']:.4f}\n")
            f.write(f"- **Precision:** {metrics['precision']:.4f}\n")
            f.write(f"- **Recall:** {metrics['recall']:.4f}\n")
            f.write(f"- **F1 Score:** {metrics['f1_score']:.4f}\n\n")
            f.write("**Confusion Matrix:**\n")
            f.write("```\n")
            f.write(str(np.array(metrics['confusion_matrix'])))
            f.write("\n```\n\n")
            f.write("**Classification Report:**\n")
            f.write("```\n")
            f.write(classification_report_to_string(metrics['classification_report']))
            f.write("\n```\n\n")
    
    logger.info(f"Evaluation report saved to {json_path}")
    logger.info(f"Evaluation report saved to {md_path}")
    
    return json_path


def classification_report_to_string(report: dict) -> str:
    """Convert classification report dict to string format."""
    lines = []
    for class_name, metrics in report.items():
        if isinstance(metrics, dict):
            lines.append(f"{class_name}:")
            for metric_name, value in metrics.items():
                lines.append(f"  {metric_name}: {value:.4f}")
    return "\n".join(lines)


def ensure_dir(directory: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def main():
    """Main function to evaluate all models."""
    # Set up paths
    project_root = Path(__file__).parent.parent.parent
    models_dir = project_root / "models"
    
    test_data_path = models_dir / "test_data.pkl"
    
    logger.info("Starting model evaluation...")
    logger.info(f"Project root: {project_root}")
    
    # Load test data
    try:
        test_data = load_test_data(test_data_path)
    except Exception as e:
        logger.error(f"Error loading test data: {e}")
        logger.error("Please run train.py first to generate test_data.pkl")
        return
    
    X_test = test_data['X_test']
    y_test = test_data['y_test']
    
    # Load and evaluate models
    models_to_evaluate = [
        ('logistic_regression', models_dir / 'logistic_regression_model.pkl'),
        ('random_forest', models_dir / 'random_forest_model.pkl'),
        ('xgboost', models_dir / 'xgboost_model.pkl')
    ]
    
    metrics_list = []
    
    for model_name, model_path in models_to_evaluate:
        if model_path.exists():
            try:
                model = load_model(model_path, model_name)
                metrics = evaluate_model(model, X_test, y_test, model_name)
                metrics_list.append(metrics)
            except Exception as e:
                logger.error(f"Error evaluating {model_name}: {e}")
        else:
            logger.warning(f"Model file not found: {model_path}")
    
    if not metrics_list:
        logger.error("No models were successfully evaluated")
        return
    
    # Compare models
    comparison_df = compare_models(metrics_list)
    
    # Select best model
    best_model_name, best_metrics = select_best_model(metrics_list)
    
    # Save evaluation report
    save_evaluation_report(metrics_list, comparison_df, best_model_name, models_dir)
    
    logger.info("Model evaluation complete!")
    logger.info(f"Best model: {best_model_name} with F1 score: {best_metrics['f1_score']:.4f}")


if __name__ == "__main__":
    main()
