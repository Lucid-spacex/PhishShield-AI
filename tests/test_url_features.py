"""
Unit tests for URL feature extraction module.
Tests cover legitimate URLs, suspicious URLs, IP-based URLs, and edge cases.
"""

import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from features.url_features import extract_features, calculate_entropy, is_ip_address, count_subdomains


class TestExtractFeatures:
    """Test the main extract_features function."""
    
    def test_legitimate_url(self):
        """Test extraction from a clearly legitimate URL."""
        url = "https://www.google.com/search?q=test"
        features = extract_features(url)
        
        assert features['url_length'] == len(url)
        assert features['has_https'] == 1
        assert features['has_ip_address'] == 0
        assert features['dot_count'] >= 2
        assert features['domain_entropy'] > 0
        assert isinstance(features['subdomain_count'], int)
        assert isinstance(features['special_char_count'], int)
        assert isinstance(features['redirect_count'], int)
    
    def test_suspicious_url(self):
        """Test extraction from a suspicious/obfuscated URL."""
        url = "http://phishing-site.com@evil.com/login.php?redirect=//another.site"
        features = extract_features(url)
        
        assert features['url_length'] == len(url)
        assert features['has_https'] == 0  # HTTP instead of HTTPS
        assert features['has_ip_address'] == 0
        assert features['special_char_count'] > 0  # Should have @, /, ?, etc.
        assert features['redirect_count'] > 0  # Has redirect indicators
    
    def test_ip_address_url(self):
        """Test extraction from an IP-based URL."""
        url = "http://192.168.1.1/admin/login"
        features = extract_features(url)
        
        assert features['url_length'] == len(url)
        assert features['has_ip_address'] == 1
        assert features['has_https'] == 0
        assert features['dot_count'] >= 3  # IP address has dots
    
    def test_empty_string(self):
        """Test extraction from an empty string."""
        url = ""
        features = extract_features(url)
        
        assert features['url_length'] == 0
        assert features['domain_entropy'] == 0
        assert features['has_https'] == 0
        assert features['has_ip_address'] == 0
        assert features['dot_count'] == 0
        assert features['subdomain_count'] == 0
        assert features['special_char_count'] == 0
        assert features['redirect_count'] == 0
    
    def test_malformed_url(self):
        """Test extraction from a malformed URL."""
        url = "not-a-valid-url"
        features = extract_features(url)
        
        # Should return default values for malformed URLs
        assert features['url_length'] == len(url)
        assert features['has_https'] == 0
        assert features['has_ip_address'] == 0
        assert isinstance(features['dot_count'], int)
    
    def test_missing_scheme(self):
        """Test extraction from URL without scheme."""
        url = "www.example.com/page"
        features = extract_features(url)
        
        # Should handle missing scheme gracefully
        assert features['url_length'] == len(url)
        assert features['has_https'] == 0
        assert features['has_ip_address'] == 0
    
    def test_subdomain_rich_url(self):
        """Test extraction from URL with many subdomains."""
        url = "https://a.b.c.d.e.f.example.com/path"
        features = extract_features(url)
        
        assert features['subdomain_count'] >= 5
        assert features['dot_count'] >= 7
    
    def test_special_characters(self):
        """Test extraction from URL with many special characters."""
        url = "https://example.com/path-with_underscores@and-dashes?query=value&another=123"
        features = extract_features(url)
        
        assert features['special_char_count'] > 0


class TestCalculateEntropy:
    """Test the entropy calculation function."""
    
    def test_high_entropy(self):
        """Test entropy calculation for high-entropy string."""
        # Random characters should have high entropy
        text = "x7k9@m2p#4"
        entropy = calculate_entropy(text)
        assert entropy > 2.0  # Should be relatively high
    
    def test_low_entropy(self):
        """Test entropy calculation for low-entropy string."""
        # Repeated characters should have low entropy
        text = "aaaaaaaaaa"
        entropy = calculate_entropy(text)
        assert entropy == 0.0  # Should be zero for identical characters
    
    def test_normal_entropy(self):
        """Test entropy calculation for normal text."""
        text = "example.com"
        entropy = calculate_entropy(text)
        assert 0 < entropy < 4.0  # Should be moderate
    
    def test_empty_string(self):
        """Test entropy calculation for empty string."""
        entropy = calculate_entropy("")
        assert entropy == 0.0


class TestIsIPAddress:
    """Test the IP address detection function."""
    
    def test_ipv4_address(self):
        """Test detection of IPv4 address."""
        assert is_ip_address("192.168.1.1") == True
        assert is_ip_address("10.0.0.1") == True
        assert is_ip_address("127.0.0.1") == True
    
    def test_ipv4_with_port(self):
        """Test detection of IPv4 address with port."""
        assert is_ip_address("192.168.1.1:8080") == True
        assert is_ip_address("127.0.0.1:443") == True
    
    def test_invalid_ipv4(self):
        """Test rejection of invalid IPv4 addresses."""
        assert is_ip_address("256.168.1.1") == False  # Octet > 255
        assert is_ip_address("192.168.1") == False  # Missing octet
        assert is_ip_address("192.168.1.1.1") == False  # Too many octets
    
    def test_domain_name(self):
        """Test that domain names are not detected as IP addresses."""
        assert is_ip_address("example.com") == False
        assert is_ip_address("www.google.com") == False
        assert is_ip_address("sub.domain.co.uk") == False
    
    def test_ipv6_address(self):
        """Test detection of IPv6 address."""
        # Test compressed IPv6
        assert is_ip_address("::1") == True
        # Test full IPv6 with multiple colons
        assert is_ip_address("2001:db8::1") == True
        # Test IPv6 with multiple sections
        assert is_ip_address("fe80::1ff:fe23:4567:890a") == True
    
    def test_empty_string(self):
        """Test with empty string."""
        assert is_ip_address("") == False
        assert is_ip_address(None) == False


class TestCountSubdomains:
    """Test the subdomain counting function."""
    
    def test_no_subdomain(self):
        """Test counting with no subdomains."""
        assert count_subdomains("example.com") == 0
        # google.co.uk is a ccTLD, so it's considered as having no subdomains with our logic
        assert count_subdomains("google.co.uk") == 0
    
    def test_single_subdomain(self):
        """Test counting with single subdomain."""
        assert count_subdomains("www.example.com") == 0  # www is not counted
        assert count_subdomains("mail.example.com") == 1
        assert count_subdomains("blog.google.com") == 1
    
    def test_multiple_subdomains(self):
        """Test counting with multiple subdomains."""
        assert count_subdomains("a.b.example.com") == 2
        assert count_subdomains("x.y.z.example.com") == 3
    
    def test_with_port(self):
        """Test counting with port number."""
        assert count_subdomains("example.com:8080") == 0
        assert count_subdomains("mail.example.com:443") == 1
    
    def test_empty_string(self):
        """Test with empty string."""
        assert count_subdomains("") == 0
        assert count_subdomains(None) == 0


class TestFeatureExtractionIntegration:
    """Integration tests for the complete feature extraction process."""
    
    def test_diverse_url_set(self):
        """Test feature extraction on a diverse set of URLs."""
        test_urls = [
            "https://www.google.com",
            "http://192.168.1.1/login",
            "https://sub.domain.example.com/path",
            "http://phishing-site.com@evil.com",
            "https://legitimate-bank.com/secure/login",
            "ftp://files.example.com/download",
            "https://localhost:8080/admin",
        ]
        
        for url in test_urls:
            features = extract_features(url)
            
            # Verify all features are present
            expected_keys = [
                'url_length', 'domain_entropy', 'has_https', 'has_ip_address',
                'dot_count', 'subdomain_count', 'special_char_count', 'redirect_count'
            ]
            assert all(key in features for key in expected_keys)
            
            # Verify all values are numeric
            for value in features.values():
                assert isinstance(value, (int, float))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
