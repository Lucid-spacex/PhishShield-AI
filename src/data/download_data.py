"""
Data acquisition script for PhishShield AI.
Downloads UCI Phishing Websites Dataset and Kaggle phishing URL datasets.
"""

import os
import requests
import zipfile
import pandas as pd
from pathlib import Path
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def ensure_dir(directory: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def download_uci_dataset(output_dir: Path) -> Optional[Path]:
    """
    Download the UCI Phishing Websites Dataset.
    
    The UCI dataset contains 11,055 URLs with 30 features and labels.
    Source: https://archive.ics.uci.edu/ml/datasets/Phishing+Websites
    
    Args:
        output_dir: Directory to save the downloaded dataset
        
    Returns:
        Path to the downloaded file, or None if download fails
    """
    logger.info("Downloading UCI Phishing Websites Dataset...")
    
    # UCI dataset URL (arXiv version which is more reliable)
    uci_url = "https://archive.ics.uci.edu/ml/machine-learning-databases/00327/Phishing%20Websites%20DataSet.csv"
    
    try:
        response = requests.get(uci_url, timeout=30)
        response.raise_for_status()
        
        output_path = output_dir / "uci_phishing_dataset.csv"
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"UCI dataset downloaded successfully to {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to download UCI dataset: {e}")
        logger.info("Manual download instructions:")
        logger.info("1. Visit: https://archive.ics.uci.edu/ml/datasets/Phishing+Websites")
        logger.info("2. Download the dataset file")
        logger.info("3. Save it as 'uci_phishing_dataset.csv' in data/raw/")
        return None


def download_kaggle_dataset(output_dir: Path) -> Optional[Path]:
    """
    Download a Kaggle phishing URL dataset using Kaggle API.
    
    Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables.
    
    Args:
        output_dir: Directory to save the downloaded dataset
        
    Returns:
        Path to the downloaded file, or None if download fails
    """
    logger.info("Attempting to download Kaggle phishing URL dataset...")
    
    # Check for Kaggle credentials
    kaggle_username = os.environ.get('KAGGLE_USERNAME')
    kaggle_key = os.environ.get('KAGGLE_KEY')
    
    if not kaggle_username or not kaggle_key:
        logger.warning("Kaggle credentials not found in environment variables.")
        logger.info("Manual download instructions:")
        logger.info("1. Visit: https://www.kaggle.com/datasets")
        logger.info("2. Search for 'phishing url dataset'")
        logger.info("3. Download a dataset with URLs and labels")
        logger.info("4. Save it as 'kaggle_phishing_dataset.csv' in data/raw/")
        logger.info("Note: Ensure the dataset has 'url' and 'label' columns")
        return None
    
    try:
        from kaggle.api import KaggleApi
        
        # Authenticate with Kaggle
        os.environ['KAGGLE_USERNAME'] = kaggle_username
        os.environ['KAGGLE_KEY'] = kaggle_key
        
        api = KaggleApi()
        api.authenticate()
        
        # Download a popular phishing URL dataset
        # Using the "Phishing Site URLs" dataset or similar
        dataset_name = "taruntiwarihp/phishing-site-urls"
        
        logger.info(f"Downloading dataset: {dataset_name}")
        api.dataset_download_files(dataset_name, path=str(output_dir), unzip=True)
        
        # Find the downloaded CSV file
        csv_files = list(output_dir.glob("*.csv"))
        if csv_files:
            output_path = output_dir / "kaggle_phishing_dataset.csv"
            # Rename the first CSV file found
            csv_files[0].rename(output_path)
            logger.info(f"Kaggle dataset downloaded successfully to {output_path}")
            return output_path
        else:
            logger.warning("No CSV file found in downloaded Kaggle dataset")
            return None
            
    except ImportError:
        logger.warning("Kaggle library not installed. Install with: pip install kaggle")
        return None
    except Exception as e:
        logger.error(f"Failed to download Kaggle dataset: {e}")
        logger.info("Manual download instructions:")
        logger.info("1. Visit: https://www.kaggle.com/datasets")
        logger.info("2. Search for 'phishing url dataset'")
        logger.info("3. Download a dataset with URLs and labels")
        logger.info("4. Save it as 'kaggle_phishing_dataset.csv' in data/raw/")
        return None


def main():
    """Main function to download all datasets."""
    # Set up paths
    project_root = Path(__file__).parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    
    ensure_dir(raw_data_dir)
    
    logger.info(f"Data will be saved to: {raw_data_dir}")
    
    # Download UCI dataset
    uci_path = download_uci_dataset(raw_data_dir)
    
    # Download Kaggle dataset (optional)
    kaggle_path = download_kaggle_dataset(raw_data_dir)
    
    # Summary
    logger.info("\n" + "="*50)
    logger.info("Download Summary:")
    logger.info("="*50)
    
    if uci_path:
        logger.info(f"✓ UCI dataset: {uci_path}")
    else:
        logger.info("✗ UCI dataset: Download failed - follow manual instructions")
    
    if kaggle_path:
        logger.info(f"✓ Kaggle dataset: {kaggle_path}")
    else:
        logger.info("✗ Kaggle dataset: Download failed - follow manual instructions")
    
    logger.info("="*50)
    
    if not uci_path and not kaggle_path:
        logger.warning("No datasets were downloaded successfully.")
        logger.warning("Please download datasets manually and place them in data/raw/")
    else:
        logger.info("At least one dataset was downloaded successfully.")


if __name__ == "__main__":
    main()
