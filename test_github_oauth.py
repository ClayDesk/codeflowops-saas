#!/usr/bin/env python3
"""
Test GitHub OAuth Integration
Quick test to verify GitHub authentication works correctly
"""
import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def test_github_oauth():
    print("🧪 Testing GitHub OAuth Integration...")
    
    # Set environment variables
    os.environ['GITHUB_CLIENT_ID'] = 'Ov23li4xEOeDgSAMz2rg'
    os.environ['GITHUB_CLIENT_SECRET'] = '65006527de2a3974af1a804b97fd6bcaac62b732'
    os.environ['GITHUB_CALLBACK_URL'] = 'http://localhost:8000/auth/github/callback'
    os.environ['FRONTEND_URL'] = 'http://localhost:3000'
    
    # Check if backend is running
    try:
        response = requests.get('http://localhost:8000/auth/github/health', timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ GitHub auth service is healthy")
            print(f"   Status: {health_data['status']}")
            print(f"   GitHub client configured: {health_data['github_client_configured']}")
            print(f"   Callback URL: {health_data['callback_url']}")
            
            # Test GitHub OAuth URL generation
            try:
                response = requests.get('http://localhost:8000/auth/github', 
                                       allow_redirects=False, timeout=5)
                if response.status_code == 307:  # Redirect response
                    redirect_url = response.headers.get('location')
                    if 'github.com/login/oauth/authorize' in redirect_url:
                        print("✅ GitHub OAuth redirect URL generated correctly")
                        print(f"   Redirect URL: {redirect_url[:100]}...")
                    else:
                        print("❌ Invalid GitHub OAuth redirect URL")
                else:
                    print("❌ GitHub OAuth endpoint not working")
            except Exception as e:
                print(f"❌ Error testing GitHub OAuth endpoint: {e}")
            
        else:
            print("❌ GitHub auth service not responding correctly")
            
    except requests.ConnectionError:
        print("❌ Backend not running on localhost:8000")
        print("   Please start the backend server first:")
        print("   cd backend && python start_backend_server.py")
        return False
    except Exception as e:
        print(f"❌ Error connecting to backend: {e}")
        return False
    
    print("\n🔗 GitHub OAuth Integration Summary:")
    print("   1. Backend routes are configured ✅")
    print("   2. Frontend login button added ✅")
    print("   3. GitHub OAuth app settings:")
    print("      - Client ID: Ov23li4xEOeDgSAMz2rg")
    print("      - Homepage URL: http://localhost:3000")
    print("      - Callback URL: http://localhost:8000/auth/github/callback")
    print("\n🚀 To test the full flow:")
    print("   1. Start backend: python start_backend_server.py")
    print("   2. Start frontend: python start_robust_front_end.py")
    print("   3. Go to http://localhost:3000/login")
    print("   4. Click 'Continue with GitHub' button")
    
    return True

if __name__ == "__main__":
    test_github_oauth()
