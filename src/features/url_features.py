"""
URL feature extraction module for PhishShield AI.
This module is designed to be lightweight and reusable in the Flask backend.
"""

import re
import math
from typing import Dict, Optional
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_features(url: str) -> Dict[str, float]:
    """
    Extract features from a single URL for phishing detection.
    
    This function is designed to be lightweight and fast for real-time prediction.
    It extracts structural and lexical features that are indicative of phishing URLs.
    
    Args:
        url: The URL string to analyze
        
    Returns:
        Dictionary of feature names and their values
        
    Features extracted:
        - url_length: Total length of the URL
        - domain_entropy: Shannon entropy of the domain (measures randomness)
        - has_https: Boolean (1 if HTTPS, 0 otherwise)
        - has_ip_address: Boolean (1 if URL uses IP address instead of domain)
        - dot_count: Number of dots in the URL
        - subdomain_count: Number of subdomains
        - special_char_count: Count of special characters (@, -, _, etc.)
        - redirect_count: Number of potential redirects in URL (from // or / patterns)
    """
    features = {}
    
    # Handle empty or invalid URLs
    if not url or not isinstance(url, str):
        logger.warning(f"Invalid URL provided: {url}")
        return {
            'url_length': 0,
            'domain_entropy': 0,
            'has_https': 0,
            'has_ip_address': 0,
            'dot_count': 0,
            'subdomain_count': 0,
            'special_char_count': 0,
            'redirect_count': 0
        }
    
    try:
        # Parse the URL
        parsed = urlparse(url)
        
        # Feature 1: URL length
        features['url_length'] = len(url)
        
        # Feature 2: Domain entropy (Shannon entropy)
        domain = parsed.netloc
        if domain:
            features['domain_entropy'] = calculate_entropy(domain)
        else:
            features['domain_entropy'] = 0
        
        # Feature 3: Has HTTPS
        features['has_https'] = 1 if parsed.scheme == 'https' else 0
        
        # Feature 4: Has IP address (instead of domain name)
        features['has_ip_address'] = 1 if is_ip_address(domain) else 0
        
        # Feature 5: Dot count
        features['dot_count'] = url.count('.')
        
        # Feature 6: Subdomain count
        features['subdomain_count'] = count_subdomains(domain)
        
        # Feature 7: Special character count
        special_chars = ['@', '-', '_', '~', '!', '$', '&', "'", '(', ')', '*', '+', ',', ';', '=', ':']
        features['special_char_count'] = sum(1 for char in url if char in special_chars)
        
        # Feature 8: Redirect count (from URL structure)
        # Count occurrences of // (potential redirects) and path depth
        redirect_indicators = url.count('//') - 1  # Subtract 1 for the scheme://
        path_depth = url.count('/')
        features['redirect_count'] = max(0, redirect_indicators) + max(0, path_depth - 2)
        
    except Exception as e:
        logger.error(f"Error extracting features from URL '{url}': {e}")
        # Return default values on error
        return {
            'url_length': len(url) if url else 0,
            'domain_entropy': 0,
            'has_https': 0,
            'has_ip_address': 0,
            'dot_count': url.count('.') if url else 0,
            'subdomain_count': 0,
            'special_char_count': 0,
            'redirect_count': 0
        }
    
    return features


def calculate_entropy(text: str) -> float:
    """
    Calculate Shannon entropy of a string.
    
    Higher entropy indicates more randomness, which can be a sign of
    obfuscated or generated phishing domains.
    
    Args:
        text: String to calculate entropy for
        
    Returns:
        Shannon entropy value
    """
    if not text:
        return 0.0
    
    # Count character frequencies
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    
    # Calculate entropy
    entropy = 0.0
    text_len = len(text)
    
    for count in freq.values():
        probability = count / text_len
        if probability > 0:
            entropy -= probability * math.log2(probability)
    
    return entropy


def is_ip_address(domain: str) -> bool:
    """
    Check if the domain is an IP address instead of a domain name.
    
    Phishing sites often use IP addresses directly to avoid domain-based filtering.
    
    Args:
        domain: Domain string to check
        
    Returns:
        True if the domain appears to be an IP address
    """
    if not domain:
        return False
    
    # Check for IPv6 first (before port removal, since IPv6 uses colons)
    ipv6_pattern = r'^[0-9a-fA-F:]+$'
    if re.match(ipv6_pattern, domain) and ':' in domain:
        # Additional check: ensure it looks like an IPv6 address
        # IPv6 addresses typically have multiple colons or compressed sections (::)
        if domain.count(':') >= 2:
            return True
        # Handle special case of compressed addresses like ::1 or 1::
        if '::' in domain:
            return True
    
    # Remove port if present (for IPv4)
    domain = domain.split(':')[0]
    
    # IPv4 pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ipv4_pattern, domain):
        # Validate each octet is 0-255
        octets = domain.split('.')
        for octet in octets:
            try:
                if int(octet) > 255:
                    return False
            except ValueError:
                return False
        return True
    
    return False


def count_subdomains(domain: str) -> int:
    """
    Count the number of subdomains in a domain.
    
    Phishing sites often use many subdomains to obfuscate the true domain.
    
    Args:
        domain: Domain string to analyze
        
    Returns:
        Number of subdomains
    """
    if not domain:
        return 0
    
    # Remove port if present
    domain = domain.split(':')[0]
    
    # Remove 'www.' if present (it's not counted as a subdomain for our purposes)
    domain = domain.replace('www.', '', 1)
    
    # Split by dots and count
    parts = domain.split('.')
    
    # Handle common country-code TLDs (co.uk, com.au, etc.)
    # These have 3 parts for the main domain (example.co.uk)
    common_cc_tlds = ['co.uk', 'com.au', 'co.nz', 'co.jp', 'co.in', 'co.za', 
                      'org.uk', 'net.au', 'gov.uk', 'ac.uk', 'edu.au']
    
    # Check if the last two parts form a common ccTLD
    if len(parts) >= 2:
        potential_cctld = '.'.join(parts[-2:])
        if potential_cctld in common_cc_tlds:
            # For ccTLDs, valid domain has at least 3 parts (example.co.uk)
            if len(parts) <= 3:
                return 0
            return len(parts) - 3
    
    # For regular TLDs, valid domain has at least 2 parts (example.com)
    # Anything beyond that is a subdomain
    if len(parts) <= 2:
        return 0
    
    return len(parts) - 2


def extract_features_batch(urls: list) -> 'pd.DataFrame':
    """
    Extract features from a batch of URLs.
    
    This function is optimized for processing large datasets efficiently.
    
    Args:
        urls: List of URL strings
        
    Returns:
        DataFrame with extracted features
    """
    import pandas as pd
    
    logger.info(f"Extracting features for {len(urls)} URLs...")
    
    features_list = []
    for i, url in enumerate(urls):
        if i % 1000 == 0:
            logger.info(f"Processed {i}/{len(urls)} URLs...")
        
        features = extract_features(url)
        features_list.append(features)
    
    df = pd.DataFrame(features_list)
    logger.info(f"Feature extraction complete. Shape: {df.shape}")
    
    return df


def main():
    """Test the feature extraction functions with example URLs."""
    # Test URLs
    test_urls = [
        "https://www.google.com",
        "http://192.168.1.1/login",
        "https://sub.sub.example.com/path/to/page",
        "http://phishing-site.com@evil.com",
        "https://legitimate-bank.com/secure/login",
    ]
    
    print("Testing feature extraction on sample URLs:")
    print("=" * 80)
    
    for url in test_urls:
        features = extract_features(url)
        print(f"\nURL: {url}")
        print("Features:")
        for feature, value in features.items():
            print(f"  {feature}: {value}")


if __name__ == "__main__":
    main()
