#!/usr/bin/env python3
"""
Simple test to verify backend API endpoints are working
"""
import requests
import json

def test_backend_endpoints():
    """Test the backend API endpoints"""

    print("🔍 Testing Backend API Endpoints")
    print("=" * 50)

    # Test URLs
    base_urls = [
        "https://api.codeflowops.com",
        "http://codeflowops.us-east-1.elasticbeanstalk.com"
    ]

    endpoints = [
        "/api/health",
        "/api/v1/auth/health",
        "/api/v1/auth/me",
        "/api/v1/payments/subscription/user"
    ]

    headers = {
        'Origin': 'https://www.codeflowops.com',
        'Content-Type': 'application/json'
    }

    for base_url in base_urls:
        print(f"\n🌐 Testing: {base_url}")
        print("-" * 40)

        for endpoint in endpoints:
            url = f"{base_url}{endpoint}"
            try:
                print(f"Testing {endpoint}...")

                # Test OPTIONS (CORS preflight)
                options_response = requests.options(url, headers=headers, timeout=10)
                print(f"  OPTIONS: {options_response.status_code}")

                # Test GET request with Bearer token
                headers_with_auth = headers.copy()
                headers_with_auth['Authorization'] = 'Bearer demo-token'

                response = requests.get(url, headers=headers_with_auth, timeout=10)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"  ✅ GET: {response.status_code} - {data.get('status', 'OK')}")
                    except json.JSONDecodeError:
                        print(f"  ❌ GET: {response.status_code} - Invalid JSON")
                        print(f"      Response: {response.text[:100]}...")
                else:
                    print(f"  ❌ GET: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"  ❌ ERROR: {str(e)}")

if __name__ == "__main__":
    test_backend_endpoints()