#!/usr/bin/env python3
"""
Manual GitHub + Cognito Test
Test the Cognito user creation with a mock GitHub user
"""
import requests
import json
import sys
import os

# Add the backend path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_cognito_user_creation():
    print("🧪 Testing Cognito User Creation Directly...")
    
    # Set environment variables for GitHub OAuth
    os.environ['GITHUB_CLIENT_ID'] = 'Ov23li4xEOeDgSAMz2rg'
    os.environ['GITHUB_CLIENT_SECRET'] = '65006527de2a3974af1a804b97fd6bcaac62b732'
    
    try:
        # Import the Cognito provider directly
        from src.auth.providers.cognito import CognitoAuthProvider
        
        print("✅ Cognito provider imported successfully")
        
        # Initialize Cognito provider
        cognito_provider = CognitoAuthProvider()
        print(f"✅ Cognito provider initialized")
        print(f"   User Pool ID: {cognito_provider.user_pool_id}")
        print(f"   Region: {cognito_provider.region}")
        
        # Test creating a mock GitHub user
        mock_email = "test-github-user@example.com"
        mock_username = mock_email  # Use email as username for Cognito
        
        print(f"\n🧪 Testing user creation for: {mock_email}")
        print(f"   Using username: {mock_username}")
        
        # Check if user already exists
        existing_users = cognito_provider.cognito_client.list_users(
            UserPoolId=cognito_provider.user_pool_id,
            Filter=f'email = "{mock_email}"'
        )
        
        if existing_users['Users']:
            print(f"✅ User already exists: {existing_users['Users'][0]['Username']}")
            print("   Skipping creation test")
        else:
            print("👤 Creating test user...")
            
            # Basic user attributes
            user_attributes = [
                {'Name': 'email', 'Value': mock_email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'name', 'Value': 'Test GitHub User'}
            ]
            
            # Create user in Cognito
            response = cognito_provider.cognito_client.admin_create_user(
                UserPoolId=cognito_provider.user_pool_id,
                Username=mock_username,
                UserAttributes=user_attributes,
                MessageAction='SUPPRESS'  # Don't send welcome email
            )
            
            print(f"✅ User created successfully: {response['User']['Username']}")
            
            # Set user as confirmed
            cognito_provider.cognito_client.admin_confirm_sign_up(
                UserPoolId=cognito_provider.user_pool_id,
                Username=mock_username
            )
            
            print("✅ User confirmed successfully")
            print(f"🎉 Test user {mock_username} created in Cognito!")
            
            # Clean up test user
            try:
                cognito_provider.cognito_client.admin_delete_user(
                    UserPoolId=cognito_provider.user_pool_id,
                    Username=mock_username
                )
                print("🧹 Test user cleaned up")
            except Exception as cleanup_error:
                print(f"⚠️ Cleanup warning: {cleanup_error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Cognito user creation: {e}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

def test_direct_github_callback():
    print("\n🔗 Testing GitHub OAuth callback endpoint...")
    
    try:
        # Test the callback endpoint directly
        callback_url = "http://localhost:8000/auth/github/callback"
        
        # Try calling without parameters (should return error)
        response = requests.get(callback_url, allow_redirects=False)
        print(f"✅ Callback endpoint accessible: {response.status_code}")
        
        if response.status_code == 307:  # Redirect
            location = response.headers.get('location', '')
            if 'error=missing_parameters' in location:
                print("✅ Callback correctly handles missing parameters")
            else:
                print(f"🤔 Unexpected redirect: {location}")
        
    except Exception as e:
        print(f"❌ Error testing callback: {e}")

if __name__ == "__main__":
    print("🚀 Manual GitHub + Cognito Integration Test")
    print("=" * 60)
    
    # Test 1: Direct Cognito user creation
    cognito_success = test_cognito_user_creation()
    
    # Test 2: GitHub callback endpoint
    test_direct_github_callback()
    
    print("\n" + "=" * 60)
    if cognito_success:
        print("✅ Cognito integration is working correctly!")
        print("   The issue might be:")
        print("   1. GitHub callback not triggering the Cognito creation")
        print("   2. Logs not showing up due to startup monitoring")
        print("   3. Frontend not actually calling the GitHub OAuth")
    else:
        print("❌ Cognito integration has issues that need to be fixed")
    
    print("\n📋 To debug further:")
    print("1. Try GitHub login and check AWS Cognito Console")
    print("2. Look for any browser console errors")
    print("3. Check browser network tab during login")
