#!/usr/bin/env python3
"""
Test GitHub OAuth + Cognito Integration
Test if GitHub users are being created in Cognito
"""
import requests
import json

def test_github_cognito():
    print("🧪 Testing GitHub OAuth + Cognito Integration...")
    
    # Test Cognito connection
    try:
        response = requests.get('http://localhost:8000/auth/github/test-cognito')
        if response.status_code == 200:
            data = response.json()
            print("✅ Cognito Connection Status:")
            print(f"   Status: {data.get('status')}")
            print(f"   User Pool: {data.get('user_pool_name')}")
            print(f"   User Pool ID: {data.get('user_pool_id')}")
            print(f"   Region: {data.get('region')}")
        else:
            print("❌ Cognito connection failed")
            print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error testing Cognito: {e}")
        return False
    
    # Test GitHub OAuth health
    try:
        response = requests.get('http://localhost:8000/auth/github/health')
        if response.status_code == 200:
            data = response.json()
            print("✅ GitHub OAuth Status:")
            print(f"   Status: {data.get('status')}")
            print(f"   GitHub configured: {data.get('github_client_configured')}")
            print(f"   Cognito available: {data.get('cognito_available')}")
        else:
            print("❌ GitHub OAuth health check failed")
    except Exception as e:
        print(f"❌ Error testing GitHub OAuth: {e}")
    
    print("\n📋 Next Steps:")
    print("1. Go to http://localhost:3000/login")
    print("2. Click 'Continue with GitHub'")
    print("3. Complete GitHub OAuth")
    print("4. Check AWS Cognito Console for new user")
    print("5. If no user appears, check backend logs for errors")
    
    print("\n🔍 Debugging Tips:")
    print("- Check AWS Cognito Console: https://console.aws.amazon.com/cognito/")
    print("- Look for user pool: User pool - ieiszw")
    print("- Check if user appears after GitHub login")
    print("- If errors occur, they'll be logged in the backend terminal")

if __name__ == "__main__":
    test_github_cognito()
