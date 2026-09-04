"""
Script to generate features from the cleaned URL dataset.
This script loads the cleaned URLs and extracts features for model training.
"""

import pandas as pd
from pathlib import Path
import logging
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from features.url_features import extract_features_batch

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Generate features from cleaned URL dataset."""
    # Set up paths
    project_root = Path(__file__).parent.parent.parent
    processed_data_dir = project_root / "data" / "processed"
    
    # Input and output paths
    input_path = processed_data_dir / "urls_clean.csv"
    output_path = processed_data_dir / "features.csv"
    
    logger.info(f"Loading cleaned URLs from {input_path}")
    
    # Load cleaned dataset
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} URLs from cleaned dataset")
    except Exception as e:
        logger.error(f"Error loading cleaned dataset: {e}")
        logger.error("Please run preprocess.py first to generate urls_clean.csv")
        return
    
    # Extract URLs
    urls = df['url'].tolist()
    labels = df['label'].tolist()
    
    logger.info(f"Extracting features for {len(urls)} URLs...")
    
    # Extract features
    features_df = extract_features_batch(urls)
    
    # Add label column
    features_df['label'] = labels
    
    # Save features
    features_df.to_csv(output_path, index=False)
    
    logger.info(f"Features saved to {output_path}")
    logger.info(f"Features shape: {features_df.shape}")
    logger.info(f"Features columns: {features_df.columns.tolist()}")
    logger.info(f"Label distribution:\n{features_df['label'].value_counts()}")


if __name__ == "__main__":
    main()
