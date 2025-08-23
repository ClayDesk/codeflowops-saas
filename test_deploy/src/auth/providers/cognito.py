"""
AWS Cognito authentication provider
"""

import boto3
import jwt
import requests
from typing import Dict, Any, Optional
from .base import AuthProvider, AuthResult
from ...config.env import get_settings

settings = get_settings()

class CognitoAuthProvider(AuthProvider):
    """AWS Cognito authentication provider"""
    
    def __init__(self):
        self.region = settings.AWS_REGION
        self.user_pool_id = getattr(settings, 'COGNITO_USER_POOL_ID', None)
        self.client_id = getattr(settings, 'COGNITO_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'COGNITO_CLIENT_SECRET', None)
        
        if not all([self.user_pool_id, self.client_id]):
            raise ValueError("Cognito configuration incomplete")
        
        self.cognito_client = boto3.client('cognito-idp', region_name=self.region)
        self._public_keys = None
    
    @property
    def provider_name(self) -> str:
        return "cognito"
    
    @property
    def supports_registration(self) -> bool:
        return True
    
    @property
    def supports_password_reset(self) -> bool:
        return True
    
    async def _get_public_keys(self) -> Dict[str, Any]:
        """Get Cognito public keys for token validation"""
        if not self._public_keys:
            keys_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
            response = requests.get(keys_url)
            response.raise_for_status()
            self._public_keys = response.json()
        return self._public_keys
    
    def _get_secret_hash(self, username: str) -> Optional[str]:
        """Generate secret hash if client secret is configured"""
        if not self.client_secret:
            return None
        
        import hmac
        import hashlib
        import base64
        
        message = username + self.client_id
        dig = hmac.new(
            str(self.client_secret).encode('utf-8'),
            msg=str(message).encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    async def authenticate(self, username: str, password: str) -> AuthResult:
        """Authenticate user with username/password"""
        try:
            auth_params = {
                'USERNAME': username,
                'PASSWORD': password
            }
            
            secret_hash = self._get_secret_hash(username)
            if secret_hash:
                auth_params['SECRET_HASH'] = secret_hash
            
            # Try ADMIN_NO_SRP_AUTH first (requires admin privileges)
            try:
                response = self.cognito_client.admin_initiate_auth(
                    UserPoolId=self.user_pool_id,
                    ClientId=self.client_id,
                    AuthFlow='ADMIN_NO_SRP_AUTH',
                    AuthParameters=auth_params
                )
            except Exception as admin_error:
                # If ADMIN_NO_SRP_AUTH fails, try alternative approach
                if "Auth flow not enabled" in str(admin_error):
                    return AuthResult(
                        success=False,
                        error_message="Authentication method not configured. Please enable ADMIN_NO_SRP_AUTH flow in AWS Cognito console under App Integration > App clients > Authentication flows."
                    )
                else:
                    raise admin_error
            
            auth_result = response['AuthenticationResult']
            
            # Decode ID token to get user info
            id_token = auth_result['IdToken']
            public_keys = await self._get_public_keys()
            
            # For now, decode without verification (in production, verify signature)
            user_info = jwt.decode(id_token, options={"verify_signature": False})
            
            return AuthResult(
                success=True,
                user_id=user_info.get('sub'),
                email=user_info.get('email'),
                username=user_info.get('cognito:username'),
                full_name=user_info.get('name'),
                access_token=auth_result['AccessToken'],
                refresh_token=auth_result.get('RefreshToken'),
                expires_in=auth_result.get('ExpiresIn', 3600),
                metadata={
                    "provider": "cognito",
                    "id_token": id_token,
                    "token_type": auth_result.get('TokenType', 'Bearer')
                }
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Authentication error: {str(e)}")
            return AuthResult(
                success=False,
                error_message=f"Cognito authentication failed: {str(e)}"
            )
    
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh access token"""
        try:
            response = self.cognito_client.admin_initiate_auth(
                UserPoolId=self.user_pool_id,
                ClientId=self.client_id,
                AuthFlow='REFRESH_TOKEN_AUTH',
                AuthParameters={
                    'REFRESH_TOKEN': refresh_token
                }
            )
            
            auth_result = response['AuthenticationResult']
            
            # Decode ID token to get user info
            id_token = auth_result['IdToken']
            user_info = jwt.decode(id_token, options={"verify_signature": False})
            
            return AuthResult(
                success=True,
                user_id=user_info.get('sub'),
                email=user_info.get('email'),
                username=user_info.get('cognito:username'),
                full_name=user_info.get('name'),
                access_token=auth_result['AccessToken'],
                expires_in=auth_result.get('ExpiresIn', 3600),
                metadata={
                    "provider": "cognito",
                    "id_token": id_token,
                    "token_type": auth_result.get('TokenType', 'Bearer')
                }
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=f"Token refresh failed: {str(e)}"
            )
    
    async def validate_token(self, token: str) -> AuthResult:
        """Validate access token"""
        try:
            # Use Cognito to get user info from access token
            response = self.cognito_client.get_user(AccessToken=token)
            
            user_attributes = {attr['Name']: attr['Value'] for attr in response['UserAttributes']}
            
            return AuthResult(
                success=True,
                user_id=response['Username'],
                email=user_attributes.get('email'),
                username=response['Username'],
                full_name=user_attributes.get('name'),
                metadata={
                    "provider": "cognito",
                    "attributes": user_attributes
                }
            )
            
        except Exception as e:
            return AuthResult(
                success=False,
                error_message=f"Token validation failed: {str(e)}"
            )
    
    async def logout(self, token: str) -> bool:
        """Logout user and invalidate token"""
        try:
            self.cognito_client.global_sign_out(AccessToken=token)
            return True
        except Exception:
            return False
    
    async def register(self, user_data: Dict[str, Any]) -> AuthResult:
        """Register new user"""
        try:
            # Use the actual username field if provided, otherwise fall back to email
            username = user_data.get("username", user_data["email"])
            password = user_data["password"]
            
            user_attributes = [
                {'Name': 'email', 'Value': user_data["email"]},
                {'Name': 'email_verified', 'Value': 'true'}
            ]
            
            if user_data.get("full_name"):
                user_attributes.append({'Name': 'name', 'Value': user_data["full_name"]})
            
            secret_hash = self._get_secret_hash(username)
            params = {
                'UserPoolId': self.user_pool_id,
                'Username': username,
                'TemporaryPassword': password,
                'UserAttributes': user_attributes,
                'MessageAction': 'SUPPRESS'  # Don't send welcome email
            }
            
            if secret_hash:
                params['SecretHash'] = secret_hash
            
            response = self.cognito_client.admin_create_user(**params)
            
            # Set permanent password
            set_password_params = {
                'UserPoolId': self.user_pool_id,
                'Username': username,
                'Password': password,
                'Permanent': True
            }
            
            if secret_hash:
                set_password_params['SecretHash'] = secret_hash
                
            self.cognito_client.admin_set_user_password(**set_password_params)
            
            # Now authenticate to get tokens
            return await self.authenticate(username, password)
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Registration error: {str(e)}")
            return AuthResult(
                success=False,
                error_message=f"Registration failed: {str(e)}"
            )
    
    async def reset_password(self, email: str) -> bool:
        """Initiate password reset"""
        try:
            secret_hash = self._get_secret_hash(email)
            params = {
                'ClientId': self.client_id,
                'Username': email
            }
            
            if secret_hash:
                params['SecretHash'] = secret_hash
            
            self.cognito_client.forgot_password(**params)
            return True
        except Exception:
            return False
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            # This requires the access token, which we don't have here
            # In practice, this would be called with the user's access token
            return False
        except Exception:
            return False
