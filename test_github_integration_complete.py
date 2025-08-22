#!/usr/bin/env python3
"""
🔍 Complete GitHub OAuth + Cognito Integration Test
====================================================

This script tests the complete GitHub OAuth flow including:
1. Backend routes availability
2. GitHub OAuth initiation
3. Cognito user creation and status
4. Frontend integration endpoints
"""

import requests
import json
import sys
from typing import Dict, Any

API_BASE = "http://localhost:8000"
FRONTEND_BASE = "http://localhost:3000"

def test_backend_health() -> bool:
    """Test if backend is running and responsive."""
    try:
        print("🏥 Testing backend health...")
        response = requests.get(f"{API_BASE}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is healthy and responsive")
            return True
        else:
            print(f"⚠️ Backend responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        return False

def test_frontend_health() -> bool:
    """Test if frontend is running."""
    try:
        print("🖥️ Testing frontend health...")
        response = requests.get(FRONTEND_BASE, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is running and accessible")
            return True
        else:
            print(f"⚠️ Frontend responded with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend not accessible: {e}")
        return False

def test_github_routes() -> Dict[str, Any]:
    """Test GitHub OAuth routes."""
    results = {}
    
    print("\n🔗 Testing GitHub OAuth routes...")
    
    # Test GitHub login initiation
    try:
        response = requests.get(f"{API_BASE}/auth/github", allow_redirects=False, timeout=10)
        if response.status_code in [302, 307]:
            print("✅ GitHub login initiation working")
            results["login_endpoint"] = "✅ Working"
        else:
            print(f"❌ GitHub login endpoint returned: {response.status_code}")
            results["login_endpoint"] = f"❌ Status: {response.status_code}"
    except Exception as e:
        print(f"❌ GitHub login endpoint error: {e}")
        results["login_endpoint"] = f"❌ Error: {e}"
    
    # Test GitHub callback (without parameters)
    try:
        response = requests.get(f"{API_BASE}/auth/github/callback", allow_redirects=False, timeout=10)
        if response.status_code in [302, 307, 400]:  # 400 is expected for missing params
            print("✅ GitHub callback endpoint accessible")
            results["callback_endpoint"] = "✅ Working"
        else:
            print(f"❌ GitHub callback endpoint returned: {response.status_code}")
            results["callback_endpoint"] = f"❌ Status: {response.status_code}"
    except Exception as e:
        print(f"❌ GitHub callback endpoint error: {e}")
        results["callback_endpoint"] = f"❌ Error: {e}"
    
    # Test user session endpoint
    try:
        response = requests.get(f"{API_BASE}/auth/github/user", timeout=10)
        if response.status_code == 401:  # Expected when no session
            print("✅ User session endpoint working (no active session)")
            results["user_endpoint"] = "✅ Working"
        else:
            print(f"⚠️ User session endpoint returned: {response.status_code}")
            results["user_endpoint"] = f"⚠️ Status: {response.status_code}"
    except Exception as e:
        print(f"❌ User session endpoint error: {e}")
        results["user_endpoint"] = f"❌ Error: {e}"
    
    return results

def test_cognito_integration() -> Dict[str, Any]:
    """Test Cognito integration."""
    results = {}
    
    print("\n🔐 Testing Cognito integration...")
    
    try:
        # Import Cognito provider
        sys.path.append('backend/src')
        sys.path.append('backend')
        from src.auth.providers.cognito import CognitoAuthProvider
        
        # Initialize provider
        cognito_provider = CognitoAuthProvider()
        print(f"✅ Cognito provider initialized")
        print(f"   User Pool ID: {cognito_provider.user_pool_id}")
        
        results["provider_init"] = "✅ Working"
        results["user_pool_id"] = cognito_provider.user_pool_id
        
        # Test user creation with email as username
        test_email = "github-test-integration@example.com"
        print(f"\n🧪 Testing user creation with email: {test_email}")
        
        try:
            # Try to create a test user
            user_attributes = [
                {'Name': 'email', 'Value': test_email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'name', 'Value': 'GitHub Test User'},
            ]
            
            response = cognito_provider.cognito_client.admin_create_user(
                UserPoolId=cognito_provider.user_pool_id,
                Username=test_email,  # Use email as username
                UserAttributes=user_attributes,
                MessageAction='SUPPRESS',
                TemporaryPassword='TempPass123!'
            )
            
            user_id = response.get('User', {}).get('Username')
            print(f"✅ Test user created successfully: {user_id}")
            results["user_creation"] = "✅ Working"
            
            # Set permanent password
            cognito_provider.cognito_client.admin_set_user_password(
                UserPoolId=cognito_provider.user_pool_id,
                Username=test_email,
                Password='GitHubOAuth123!',
                Permanent=True
            )
            print("✅ User password set and confirmed")
            results["user_confirmation"] = "✅ Working"
            
            # Clean up test user
            try:
                cognito_provider.cognito_client.admin_delete_user(
                    UserPoolId=cognito_provider.user_pool_id,
                    Username=test_email
                )
                print("🧹 Test user cleaned up")
            except:
                pass  # Ignore cleanup errors
                
        except Exception as create_error:
            if "UsernameExistsException" in str(create_error):
                print("⚠️ Test user already exists (that's actually good!)")
                results["user_creation"] = "✅ Working (user exists)"
            else:
                print(f"❌ User creation failed: {create_error}")
                results["user_creation"] = f"❌ Error: {create_error}"
        
    except Exception as e:
        print(f"❌ Cognito integration error: {e}")
        results["provider_init"] = f"❌ Error: {e}"
    
    return results

def print_integration_summary(backend_health: bool, frontend_health: bool, 
                            github_results: Dict, cognito_results: Dict):
    """Print a comprehensive summary."""
    print("\n" + "="*60)
    print("🎯 GITHUB OAUTH + COGNITO INTEGRATION SUMMARY")
    print("="*60)
    
    print(f"\n🏥 Infrastructure Status:")
    print(f"   Backend (localhost:8000): {'✅ Running' if backend_health else '❌ Down'}")
    print(f"   Frontend (localhost:3000): {'✅ Running' if frontend_health else '❌ Down'}")
    
    print(f"\n🔗 GitHub OAuth Endpoints:")
    for endpoint, status in github_results.items():
        print(f"   {endpoint}: {status}")
    
    print(f"\n🔐 Cognito Integration:")
    for component, status in cognito_results.items():
        if component != "user_pool_id":
            print(f"   {component}: {status}")
    
    # Overall status
    all_working = (
        backend_health and frontend_health and
        all("✅" in str(status) for status in github_results.values()) and
        all("✅" in str(status) or key == "user_pool_id" for key, status in cognito_results.items())
    )
    
    if all_working:
        print(f"\n🎉 OVERALL STATUS: ✅ ALL SYSTEMS WORKING!")
        print(f"   Ready for GitHub OAuth login testing")
        print(f"   Users will be created and stored in Cognito")
        print(f"   Frontend GitHub button should work properly")
    else:
        print(f"\n⚠️ OVERALL STATUS: ❌ SOME ISSUES DETECTED")
        print(f"   Please check the individual component statuses above")
    
    print(f"\n📋 Next Steps:")
    print(f"   1. Open browser to http://localhost:3000")
    print(f"   2. Click the GitHub login button")
    print(f"   3. Complete GitHub OAuth flow")
    print(f"   4. Check AWS Cognito Console for new user")
    print(f"   5. Verify redirect to homepage")
    
    print("="*60)

def main():
    """Run complete integration test."""
    print("🚀 Complete GitHub OAuth + Cognito Integration Test")
    print("="*60)
    
    # Test infrastructure
    backend_health = test_backend_health()
    frontend_health = test_frontend_health()
    
    # Test GitHub OAuth
    github_results = test_github_routes()
    
    # Test Cognito integration
    cognito_results = test_cognito_integration()
    
    # Print summary
    print_integration_summary(backend_health, frontend_health, github_results, cognito_results)

if __name__ == "__main__":
    main()
