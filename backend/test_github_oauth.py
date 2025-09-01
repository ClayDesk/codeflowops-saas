"""
Test script for GitHub OAuth integration
Run this to verify the GitHub OAuth setup is working correctly
"""

import os
import sys
import asyncio

# Add the backend root to the path for imports
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

async def test_github_oauth_setup():
    """Test GitHub OAuth setup and configuration"""
    print("🔍 Testing GitHub OAuth Integration Setup...")
    print("=" * 50)
    
    try:
        # Test 1: Import OAuth Cognito Provider
        print("1. Testing CognitoOAuthProvider import...")
        from src.auth.providers.cognito_oauth import CognitoOAuthProvider
        print("   ✅ CognitoOAuthProvider imported successfully")
        
        # Test 2: Import GitHub OAuth routes
        print("2. Testing GitHub OAuth routes import...")
        from src.api.github_auth_routes import router
        print("   ✅ GitHub OAuth routes imported successfully")
        
        # Test 3: Import OAuth integration service
        print("3. Testing OAuth Cognito integration service...")
        from src.services.oauth_cognito_integration import oauth_cognito_service
        print("   ✅ OAuth Cognito integration service imported successfully")
        
        # Test 4: Check environment configuration
        print("4. Testing environment configuration...")
        from src.config.env import get_settings
        settings = get_settings()
        
        # Check GitHub OAuth settings
        github_client_id = getattr(settings, 'GITHUB_CLIENT_ID', None)
        github_client_secret = getattr(settings, 'GITHUB_CLIENT_SECRET', None)
        
        if github_client_id:
            print(f"   ✅ GITHUB_CLIENT_ID configured: {github_client_id[:10]}...")
        else:
            print("   ⚠️  GITHUB_CLIENT_ID not configured")
            
        if github_client_secret:
            print(f"   ✅ GITHUB_CLIENT_SECRET configured: {github_client_secret[:10]}...")
        else:
            print("   ⚠️  GITHUB_CLIENT_SECRET not configured")
        
        # Check Cognito settings
        cognito_user_pool_id = getattr(settings, 'COGNITO_USER_POOL_ID', None)
        cognito_client_id = getattr(settings, 'COGNITO_CLIENT_ID', None)
        aws_region = getattr(settings, 'AWS_REGION', None)
        
        if cognito_user_pool_id:
            print(f"   ✅ COGNITO_USER_POOL_ID configured: {cognito_user_pool_id}")
        else:
            print("   ⚠️  COGNITO_USER_POOL_ID not configured")
            
        if cognito_client_id:
            print(f"   ✅ COGNITO_CLIENT_ID configured: {cognito_client_id}")
        else:
            print("   ⚠️  COGNITO_CLIENT_ID not configured")
            
        if aws_region:
            print(f"   ✅ AWS_REGION configured: {aws_region}")
        else:
            print("   ⚠️  AWS_REGION not configured")
        
        # Test 5: OAuth provider configuration
        print("5. Testing OAuth provider configuration...")
        try:
            from src.auth.providers.oauth import OAuthProvider
            github_oauth = OAuthProvider("github")
            config = github_oauth.config
            
            if config.get('client_id'):
                print("   ✅ GitHub OAuth provider configured")
                print(f"      - Authorize URL: {config.get('authorize_url')}")
                print(f"      - Token URL: {config.get('token_url')}")
                print(f"      - User URL: {config.get('user_url')}")
                print(f"      - Scope: {config.get('scope')}")
            else:
                print("   ⚠️  GitHub OAuth provider not properly configured")
                
        except Exception as e:
            print(f"   ❌ Error testing OAuth provider: {e}")
        
        # Test 6: Authorization URL generation
        print("6. Testing authorization URL generation...")
        try:
            auth_url = await oauth_cognito_service.get_oauth_authorization_url(
                provider="github",
                redirect_uri="https://api.codeflowops.com/api/v1/auth/github",
                state="test-state-123"
            )
            print("   ✅ Authorization URL generated successfully")
            print(f"      URL: {auth_url[:100]}...")
        except Exception as e:
            print(f"   ❌ Error generating authorization URL: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 GitHub OAuth Integration Test Complete!")
        print("\nNext steps:")
        print("1. Ensure all environment variables are set in production")
        print("2. Configure Cognito User Pool custom attributes")
        print("3. Test the complete OAuth flow with frontend")
        print("4. Verify GitHub OAuth app configuration")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_github_oauth_setup())
