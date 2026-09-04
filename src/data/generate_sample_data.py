"""
Generate sample URL data for testing the PhishShield AI pipeline.
This creates a synthetic dataset for development and testing purposes.
"""

import pandas as pd
from pathlib import Path
import logging
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_sample_urls(num_samples: int = 1000) -> pd.DataFrame:
    """
    Generate sample URLs with labels for testing.
    
    Args:
        num_samples: Number of sample URLs to generate
        
    Returns:
        DataFrame with 'url' and 'label' columns
    """
    logger.info(f"Generating {num_samples} sample URLs...")
    
    # Sample legitimate URLs
    legitimate_urls = [
        "https://www.google.com/search?q=test",
        "https://github.com/user/repository",
        "https://stackoverflow.com/questions/12345",
        "https://www.amazon.com/product/dp/12345",
        "https://www.facebook.com/profile",
        "https://twitter.com/user/status/123",
        "https://www.linkedin.com/in/user",
        "https://www.reddit.com/r/subreddit",
        "https://www.wikipedia.org/wiki/topic",
        "https://www.youtube.com/watch?v=123",
        "https://mail.google.com/mail/u/0/#inbox",
        "https://docs.google.com/document/d/123",
        "https://drive.google.com/file/d/123",
        "https://www.instagram.com/p/123/",
        "https://www.netflix.com/watch/123",
    ]
    
    # Sample phishing URLs (obfuscated, suspicious patterns)
    phishing_urls = [
        "http://192.168.1.1/login.php",
        "http://verify-account.com@evil.com/login",
        "https://secure-login.fakebank.com/verify",
        "http://free-netflix.com/account/login",
        "https://apple-id.icloud.verify.com/signin",
        "http://paypal-secure.com/api/login",
        "https://account-recovery.microsoft.com/verify",
        "http://bit.ly/malicious-link-redirect",
        "https://sub.sub.sub.phishing-site.com/login",
        "http://secure-login-gmail.com/verify-account",
        "https://amazon-verify-account.com/signin",
        "http://facebook-security.com/account/recovery",
        "https://twitter-verification.com/login",
        "http://bank-secure-login.com/online-banking",
        "https://apple-support-id.com/verify",
    ]
    
    # Generate variations
    urls = []
    labels = []
    
    for i in range(num_samples):
        if i % 2 == 0:  # Legitimate
            base_url = random.choice(legitimate_urls)
            # Add some variations
            if random.random() > 0.5:
                base_url = base_url + f"?param={random.randint(1000, 9999)}"
            urls.append(base_url)
            labels.append(0)
        else:  # Phishing
            base_url = random.choice(phishing_urls)
            # Add some variations
            if random.random() > 0.5:
                subdomain = f"sub{random.randint(1, 9)}."
                base_url = base_url.replace("://", f"://{subdomain}")
            urls.append(base_url)
            labels.append(1)
    
    # Create DataFrame
    df = pd.DataFrame({
        'url': urls,
        'label': labels
    })
    
    logger.info(f"Generated {len(df)} sample URLs")
    logger.info(f"Label distribution:\n{df['label'].value_counts()}")
    
    return df


def main():
    """Generate and save sample data."""
    # Set up paths
    project_root = Path(__file__).parent.parent.parent
    raw_data_dir = project_root / "data" / "raw"
    
    ensure_dir(raw_data_dir)
    
    # Generate sample data
    sample_df = generate_sample_urls(num_samples=2000)
    
    # Save as Kaggle-style dataset
    output_path = raw_data_dir / "kaggle_phishing_dataset.csv"
    sample_df.to_csv(output_path, index=False)
    
    logger.info(f"Sample data saved to {output_path}")
    logger.info("This can be used as the Kaggle dataset for testing the pipeline")


def ensure_dir(directory: Path) -> None:
    """Ensure directory exists, create if it doesn't."""
    directory.mkdir(parents=True, exist_ok=True)


if __name__ == "__main__":
    main()
