"""
Preprocessing script for PhishShield AI.
Cleans and merges downloaded datasets into a unified format.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def ensure_dir(directory: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


def load_uci_dataset(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Load and process the UCI Phishing Websites Dataset.
    
    The UCI dataset has 30 pre-extracted features plus a label.
    We need to extract the URL information if available, or work with what we have.
    
    Args:
        file_path: Path to the UCI dataset CSV file
        
    Returns:
        DataFrame with standardized columns, or None if loading fails
    """
    logger.info(f"Loading UCI dataset from {file_path}")
    
    try:
        # UCI dataset typically has feature columns, not raw URLs
        # We'll load it and see what columns are available
        df = pd.read_csv(file_path)
        
        logger.info(f"UCI dataset shape: {df.shape}")
        logger.info(f"UCI dataset columns: {df.columns.tolist()}")
        
        # The UCI dataset structure varies, but typically has:
        # - 30 feature columns
        # - A 'Result' column (1 = phishing, -1 = legitimate, or 0/1)
        
        # Try to identify the label column
        label_col = None
        for col in df.columns:
            if col.lower() in ['result', 'label', 'class', 'target']:
                label_col = col
                break
        
        if label_col is None:
            logger.warning("Could not identify label column in UCI dataset")
            return None
        
        # Standardize labels to 0 (legitimate) and 1 (phishing)
        df['label'] = df[label_col].apply(lambda x: 1 if x == 1 or x == -1 else 0)
        
        # Check if there's a URL column
        url_col = None
        for col in df.columns:
            if col.lower() in ['url', 'address', 'domain']:
                url_col = col
                break
        
        if url_col:
            df = df.rename(columns={url_col: 'url'})
        else:
            # If no URL column, we can't use this dataset for feature extraction
            # We'll create placeholder URLs based on the features
            logger.warning("No URL column found in UCI dataset")
            logger.info("UCI dataset may not be suitable for URL-based feature extraction")
            return None
        
        # Keep only url and label columns
        df = df[['url', 'label']].copy()
        
        logger.info(f"Processed UCI dataset shape: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading UCI dataset: {e}")
        return None


def load_kaggle_dataset(file_path: Path) -> Optional[pd.DataFrame]:
    """
    Load and process a Kaggle phishing URL dataset.
    
    Kaggle datasets vary in structure. We'll try to detect common patterns.
    
    Args:
        file_path: Path to the Kaggle dataset CSV file
        
    Returns:
        DataFrame with standardized columns, or None if loading fails
    """
    logger.info(f"Loading Kaggle dataset from {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        
        logger.info(f"Kaggle dataset shape: {df.shape}")
        logger.info(f"Kaggle dataset columns: {df.columns.tolist()}")
        
        # Try to identify URL and label columns
        url_col = None
        label_col = None
        
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in ['url', 'link', 'website', 'address']:
                url_col = col
            elif col_lower in ['label', 'class', 'target', 'result', 'status']:
                label_col = col
        
        if url_col is None:
            logger.error("Could not identify URL column in Kaggle dataset")
            return None
        
        if label_col is None:
            logger.error("Could not identify label column in Kaggle dataset")
            return None
        
        # Standardize column names
        df = df.rename(columns={url_col: 'url', label_col: 'label'})
        
        # Standardize labels to 0 (legitimate) and 1 (phishing)
        # Handle various label encodings
        def standardize_label(label):
            if pd.isna(label):
                return np.nan
            label_str = str(label).lower()
            if label_str in ['1', 'phishing', 'bad', 'malicious', 'yes', 'true']:
                return 1
            elif label_str in ['0', 'legitimate', 'good', 'safe', 'no', 'false']:
                return 0
            else:
                # Try to convert to int
                try:
                    return int(label)
                except:
                    return np.nan
        
        df['label'] = df['label'].apply(standardize_label)
        
        # Keep only url and label columns
        df = df[['url', 'label']].copy()
        
        logger.info(f"Processed Kaggle dataset shape: {df.shape}")
        return df
        
    except Exception as e:
        logger.error(f"Error loading Kaggle dataset: {e}")
        return None


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean the dataset by removing duplicates, handling nulls, and malformed rows.
    
    Args:
        df: Input DataFrame with 'url' and 'label' columns
        
    Returns:
        Cleaned DataFrame
    """
    logger.info("Cleaning dataset...")
    
    initial_rows = len(df)
    
    # Remove rows with null values
    df = df.dropna(subset=['url', 'label'])
    logger.info(f"Removed {initial_rows - len(df)} rows with null values")
    
    # Remove duplicate URLs
    df = df.drop_duplicates(subset=['url'])
    logger.info(f"Removed duplicates, remaining rows: {len(df)}")
    
    # Remove malformed URLs (empty strings, too short, etc.)
    df = df[df['url'].str.len() > 5]  # Minimum reasonable URL length
    logger.info(f"Removed malformed URLs, remaining rows: {len(df)}")
    
    # Ensure label is integer
    df['label'] = df['label'].astype(int)
    
    # Remove any rows with invalid labels (not 0 or 1)
    df = df[df['label'].isin([0, 1])]
    logger.info(f"Removed invalid labels, remaining rows: {len(df)}")
    
    logger.info(f"Final cleaned dataset shape: {df.shape}")
    logger.info(f"Label distribution:\n{df['label'].value_counts()}")
    
    return df


def merge_datasets(datasets: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple datasets into one unified dataset.
    
    Args:
        datasets: List of DataFrames to merge
        
    Returns:
        Merged DataFrame
    """
    logger.info(f"Merging {len(datasets)} datasets...")
    
    if not datasets:
        raise ValueError("No datasets to merge")
    
    # Concatenate all datasets
    merged_df = pd.concat(datasets, ignore_index=True)
    
    # Remove any duplicates that may have appeared after merging
    merged_df = merged_df.drop_duplicates(subset=['url'])
    
    logger.info(f"Merged dataset shape: {merged_df.shape}")
    logger.info(f"Merged label distribution:\n{merged_df['label'].value_counts()}")
    
    return merged_df


def main():
    """Main function to preprocess all datasets."""
    # Set up paths
    project_root = Path(__file__).parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    processed_data_dir = project_root / "data" / "processed"
    
    ensure_dir(processed_data_dir)
    
    logger.info(f"Raw data directory: {raw_data_dir}")
    logger.info(f"Processed data directory: {processed_data_dir}")
    
    # Load available datasets
    datasets = []
    
    # Try to load UCI dataset
    uci_path = raw_data_dir / "uci_phishing_dataset.csv"
    if uci_path.exists():
        uci_df = load_uci_dataset(uci_path)
        if uci_df is not None:
            datasets.append(uci_df)
    else:
        logger.warning(f"UCI dataset not found at {uci_path}")
    
    # Try to load Kaggle dataset
    kaggle_path = raw_data_dir / "kaggle_phishing_dataset.csv"
    if kaggle_path.exists():
        kaggle_df = load_kaggle_dataset(kaggle_path)
        if kaggle_df is not None:
            datasets.append(kaggle_df)
    else:
        logger.warning(f"Kaggle dataset not found at {kaggle_path}")
    
    if not datasets:
        logger.error("No valid datasets found in data/raw/")
        logger.error("Please download datasets first using download_data.py")
        return
    
    # Merge datasets
    merged_df = merge_datasets(datasets)
    
    # Clean the merged dataset
    cleaned_df = clean_dataset(merged_df)
    
    # Save cleaned dataset
    output_path = processed_data_dir / "urls_clean.csv"
    cleaned_df.to_csv(output_path, index=False)
    
    logger.info(f"Cleaned dataset saved to {output_path}")
    logger.info(f"Final dataset shape: {cleaned_df.shape}")
    logger.info(f"Final label distribution:\n{cleaned_df['label'].value_counts()}")


if __name__ == "__main__":
    main()
