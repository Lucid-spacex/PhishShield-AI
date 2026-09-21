"""
Test the exact URL that's showing "Unknown" in the frontend
"""

import requests
import json

BASE_URL = "https://phishshield-ai-pari.onrender.com"

def test_google_url():
    """Test scanning google.com with the exact URL from the frontend"""
    print("Testing exact URL from frontend: https://www.google.com/")
    
    # First, login to get a token
    print("\n1. Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "testuser", "password": "testpassword123"},
        timeout=30
    )
    
    if login_response.status_code == 401:
        print("User doesn't exist, registering...")
        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json={"username": "testuser", "email": "test@example.com", "password": "testpassword123"},
            timeout=30
        )
        print(f"Register status: {register_response.status_code}")
        if register_response.status_code == 201:
            login_response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"username": "testuser", "password": "testpassword123"},
                timeout=30
            )
    
    if login_response.status_code != 200:
        print(f"Login failed: {login_response.text}")
        return
    
    token = login_response.json().get('access_token')
    print(f"Got token: {token[:20]}...")
    
    # Test the exact URL from the frontend
    print("\n2. Scanning https://www.google.com/")
    headers = {"Authorization": f"Bearer {token}"}
    scan_response = requests.post(
        f"{BASE_URL}/api/scan/",
        json={"url": "https://www.google.com/"},
        headers=headers,
        timeout=30
    )
    
    print(f"Scan status: {scan_response.status_code}")
    print(f"Raw response headers: {dict(scan_response.headers)}")
    print(f"\nRaw response JSON:")
    print(json.dumps(scan_response.json(), indent=2))
    
    # Check for the specific fields the frontend is displaying
    if scan_response.status_code == 201:
        data = scan_response.json()
        print(f"\n3. Analyzing response fields:")
        print(f"   label: '{data.get('label')}'")
        print(f"   confidence_score: {data.get('confidence_score')}")
        print(f"   risk_indicators: {data.get('risk_indicators')}")
        print(f"   scan_id: {data.get('scan_id')}")
        
        # Check if this matches the "Unknown" pattern
        if data.get('label') == 'Unknown':
            print("\n[!] FOUND THE ISSUE: Backend is returning 'Unknown' label!")
        elif data.get('label') == 'legitimate':
            print("\n[OK] Backend is correctly returning 'legitimate'")
            print("   The issue is in the FRONTEND processing this response")
    
    # Also test the scan history to see what's stored
    print("\n4. Checking scan history...")
    history_response = requests.get(
        f"{BASE_URL}/api/scan/history",
        headers=headers,
        timeout=30
    )
    
    if history_response.status_code == 200:
        history_data = history_response.json()
        scans = history_data.get('scans', [])
        print(f"Total scans in history: {len(scans)}")
        
        # Find the most recent google.com scan
        for scan in scans[:3]:
            if 'google.com' in scan.get('url_scanned', ''):
                print(f"\nRecent google.com scan:")
                print(f"   URL: {scan.get('url_scanned')}")
                print(f"   Result: {scan.get('result')}")
                print(f"   Risk score: {scan.get('risk_score')}")
                print(f"   Risk indicators: {scan.get('risk_indicators')}")

if __name__ == "__main__":
    test_google_url()