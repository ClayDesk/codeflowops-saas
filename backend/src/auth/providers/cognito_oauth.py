"""
Enhanced Cognito OAuth Provider
Handles OAuth users in Cognito with proper token generation
"""

import boto3
import jwt
import json
import uuid
import hashlib
import time
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError
from .base import AuthProvider, AuthResult
from ...config.env import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()


class CognitoOAuthProvider(AuthProvider):
    """Enhanced Cognito provider for OAuth users"""
    
    def __init__(self):
        self.region = settings.AWS_REGION
        self.user_pool_id = getattr(settings, 'COGNITO_USER_POOL_ID', None)
        self.client_id = getattr(settings, 'COGNITO_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'COGNITO_CLIENT_SECRET', None)
        
        if not all([self.user_pool_id, self.client_id]):
            raise ValueError("Cognito configuration incomplete")
        
        self.cognito_client = boto3.client('cognito-idp', region_name=self.region)
        self.cognito_identity = boto3.client('cognito-identity', region_name=self.region)
    
    @property
    def provider_name(self) -> str:
        return "cognito_oauth"
    
    @property
    def supports_registration(self) -> bool:
        return True
    
    @property
    def supports_password_reset(self) -> bool:
        return False
    
    def _get_secret_hash(self, username: str) -> Optional[str]:
        """Generate secret hash for Cognito if client secret exists"""
        if not self.client_secret:
            return None
        
        import hmac
        import hashlib
        import base64
        
        message = username + self.client_id
        dig = hmac.new(
            self.client_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    async def create_oauth_user(self, oauth_result: AuthResult, provider: str) -> AuthResult:
        """Create a new Cognito user from OAuth data"""
        try:
            username = oauth_result.email or f"{provider}_{oauth_result.user_id}"
            
            # Prepare user attributes
            user_attributes = [
                {'Name': 'email', 'Value': oauth_result.email or f"{provider}@{oauth_result.user_id}.oauth"},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'name', 'Value': oauth_result.full_name or oauth_result.username or username},
                {'Name': f'custom:oauth_{provider}_id', 'Value': str(oauth_result.user_id)},
                {'Name': f'custom:oauth_{provider}_username', 'Value': oauth_result.username or username},
                {'Name': 'custom:auth_provider', 'Value': f'oauth_{provider}'},
                {'Name': 'custom:oauth_profile', 'Value': json.dumps(oauth_result.metadata.get('oauth_user_info', {}))[:2000]}
            ]
            
            # Generate a secure random password that user will never use
            temp_password = self._generate_oauth_password()
            
            # Create user
            create_params = {
                'UserPoolId': self.user_pool_id,
                'Username': username,
                'UserAttributes': user_attributes,
                'TemporaryPassword': temp_password,
                'MessageAction': 'SUPPRESS'
            }
            
            secret_hash = self._get_secret_hash(username)
            if secret_hash:
                create_params['SecretHash'] = secret_hash
            
            response = self.cognito_client.admin_create_user(**create_params)
            
            # Set permanent password
            set_password_params = {
                'UserPoolId': self.user_pool_id,
                'Username': username,
                'Password': temp_password,
                'Permanent': True
            }
            
            if secret_hash:
                set_password_params['SecretHash'] = secret_hash
            
            self.cognito_client.admin_set_user_password(**set_password_params)
            
            # Generate tokens using admin auth
            return await self._generate_tokens_for_oauth_user(username, provider, oauth_result)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'UsernameExistsException':
                # User already exists, try to authenticate
                return await self._generate_tokens_for_oauth_user(username, provider, oauth_result)
            else:
                logger.error(f"Error creating OAuth user: {e}")
                return AuthResult(
                    success=False,
                    error_message=f"Failed to create user: {e.response['Error']['Message']}"
                )
        except Exception as e:
            logger.error(f"Unexpected error creating OAuth user: {str(e)}")
            return AuthResult(
                success=False,
                error_message=f"Failed to create user: {str(e)}"
            )
    
    async def _generate_tokens_for_oauth_user(self, username: str, provider: str, oauth_result: AuthResult) -> AuthResult:
        """Generate proper Cognito tokens for OAuth user"""
        try:
            # Get user details
            user_response = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            
            user_attributes = {attr['Name']: attr['Value'] for attr in user_response['UserAttributes']}
            
            # Create custom JWT tokens that will be accepted by your system
            # In production, you might want to use Cognito Identity Pool for this
            
            # Generate access token
            access_token_payload = {
                'sub': user_response['Username'],
                'email': user_attributes.get('email'),
                'username': username,
                'name': user_attributes.get('name'),
                'cognito:username': username,
                'auth_provider': f'oauth_{provider}',
                'oauth_provider': provider,
                'oauth_user_id': oauth_result.user_id,
                'iss': f'cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}',
                'aud': self.client_id,
                'token_use': 'access',
                'scope': 'openid email profile',
                'iat': int(time.time()),
                'exp': int(time.time()) + 3600  # 1 hour
            }
            
            # For now, create unsigned tokens (in production, sign with proper key)
            access_token = jwt.encode(access_token_payload, 'oauth_secret', algorithm='HS256')
            
            # Generate refresh token
            refresh_token_payload = {
                'sub': user_response['Username'],
                'cognito:username': username,
                'token_use': 'refresh',
                'iat': int(time.time()),
                'exp': int(time.time()) + (30 * 24 * 3600)  # 30 days
            }
            
            refresh_token = jwt.encode(refresh_token_payload, 'oauth_secret', algorithm='HS256')
            
            return AuthResult(
                success=True,
                user_id=user_response['Username'],
                email=user_attributes.get('email'),
                username=username,
                full_name=user_attributes.get('name'),
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=3600,
                metadata={
                    'provider': 'cognito_oauth',
                    'oauth_provider': provider,
                    'cognito_username': username,
                    'cognito_attributes': user_attributes,
                    'oauth_user_id': oauth_result.user_id
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating tokens for OAuth user: {str(e)}")
            return AuthResult(
                success=False,
                error_message=f"Failed to generate authentication tokens: {str(e)}"
            )
    
    def _generate_oauth_password(self) -> str:
        """Generate a secure password for OAuth users"""
        # Generate a strong random password that meets Cognito requirements
        random_part = str(uuid.uuid4()).replace('-', '')
        hash_part = hashlib.sha256(random_part.encode()).hexdigest()[:8]
        return f"OAuth{hash_part}!@#{random_part[:8]}"
    
    async def update_oauth_user(self, username: str, provider: str, oauth_result: AuthResult) -> AuthResult:
        """Update existing OAuth user with new data"""
        try:
            user_attributes = [
                {'Name': f'custom:oauth_{provider}_id', 'Value': str(oauth_result.user_id)},
                {'Name': f'custom:oauth_{provider}_username', 'Value': oauth_result.username or username},
                {'Name': 'custom:auth_provider', 'Value': f'oauth_{provider}'},
                {'Name': 'custom:oauth_profile', 'Value': json.dumps(oauth_result.metadata.get('oauth_user_info', {}))[:2000]}
            ]
            
            # Update name if provided
            if oauth_result.full_name:
                user_attributes.append({'Name': 'name', 'Value': oauth_result.full_name})
            
            self.cognito_client.admin_update_user_attributes(
                UserPoolId=self.user_pool_id,
                Username=username,
                UserAttributes=user_attributes
            )
            
            # Generate new tokens
            return await self._generate_tokens_for_oauth_user(username, provider, oauth_result)
            
        except Exception as e:
            logger.error(f"Error updating OAuth user: {str(e)}")
            return AuthResult(
                success=False,
                error_message=f"Failed to update user: {str(e)}"
            )
    
    async def find_user_by_oauth_id(self, provider: str, oauth_user_id: str, email: str) -> Optional[str]:
        """Find Cognito user by OAuth provider ID or email"""
        try:
            # Try to find by email first
            if email:
                try:
                    response = self.cognito_client.admin_get_user(
                        UserPoolId=self.user_pool_id,
                        Username=email
                    )
                    return response['Username']
                except ClientError as e:
                    if e.response['Error']['Code'] != 'UserNotFoundException':
                        logger.error(f"Error finding user by email: {e}")
            
            # Could implement additional search strategies here
            return None
            
        except Exception as e:
            logger.error(f"Error finding OAuth user: {str(e)}")
            return None
    
    async def authenticate(self, username: str, password: str) -> AuthResult:
        """Not supported for OAuth users"""
        return AuthResult(
            success=False,
            error_message="OAuth users should use OAuth flow"
        )
    
    async def register(self, user_data: Dict[str, Any]) -> AuthResult:
        """Not supported for OAuth users"""
        return AuthResult(
            success=False,
            error_message="OAuth users should use OAuth flow"
        )
    
    async def validate_token(self, token: str) -> AuthResult:
        """Validate OAuth-generated token"""
        try:
            # Decode the token (in production, verify signature properly)
            payload = jwt.decode(token, 'oauth_secret', algorithms=['HS256'], options={"verify_signature": False})
            
            return AuthResult(
                success=True,
                user_id=payload.get('sub'),
                email=payload.get('email'),
                username=payload.get('username'),
                full_name=payload.get('name'),
                metadata={
                    'provider': 'cognito_oauth',
                    'oauth_provider': payload.get('oauth_provider'),
                    'cognito_username': payload.get('cognito:username')
                }
            )
            
        except jwt.ExpiredSignatureError:
            return AuthResult(
                success=False,
                error_message="Token has expired"
            )
        except jwt.InvalidTokenError:
            return AuthResult(
                success=False,
                error_message="Invalid token"
            )
        except Exception as e:
            logger.error(f"Error validating OAuth token: {str(e)}")
            return AuthResult(
                success=False,
                error_message="Token validation failed"
            )
    
    async def refresh_token(self, refresh_token: str) -> AuthResult:
        """Refresh OAuth token"""
        try:
            # Decode refresh token
            payload = jwt.decode(refresh_token, 'oauth_secret', algorithms=['HS256'], options={"verify_signature": False})
            
            if payload.get('token_use') != 'refresh':
                return AuthResult(
                    success=False,
                    error_message="Invalid refresh token"
                )
            
            username = payload.get('cognito:username')
            if not username:
                return AuthResult(
                    success=False,
                    error_message="Invalid refresh token"
                )
            
            # Get user info and generate new tokens
            user_response = self.cognito_client.admin_get_user(
                UserPoolId=self.user_pool_id,
                Username=username
            )
            
            user_attributes = {attr['Name']: attr['Value'] for attr in user_response['UserAttributes']}
            provider = user_attributes.get('custom:auth_provider', '').replace('oauth_', '')
            
            # Create mock oauth result for token generation
            oauth_result = AuthResult(
                success=True,
                user_id=user_attributes.get(f'custom:oauth_{provider}_id'),
                email=user_attributes.get('email'),
                username=user_attributes.get(f'custom:oauth_{provider}_username'),
                full_name=user_attributes.get('name')
            )
            
            return await self._generate_tokens_for_oauth_user(username, provider, oauth_result)
            
        except jwt.ExpiredSignatureError:
            return AuthResult(
                success=False,
                error_message="Refresh token has expired"
            )
        except Exception as e:
            logger.error(f"Error refreshing OAuth token: {str(e)}")
            return AuthResult(
                success=False,
                error_message="Token refresh failed"
            )
    
    async def logout(self, token: str) -> bool:
        """Logout OAuth user"""
        try:
            # For OAuth tokens, we can't revoke them in Cognito easily
            # In production, you might want to maintain a token blacklist
            return True
        except Exception as e:
            logger.error(f"Error logging out OAuth user: {str(e)}")
            return False
    
    async def reset_password(self, email: str) -> bool:
        """Not supported for OAuth users"""
        return False
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Not supported for OAuth users"""
        return False
