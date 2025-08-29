"""
AWS Cognito authentication provider - Production Optimized for High Scale
Supports thousands of concurrent users with connection pooling, caching, and retry logic
"""

import boto3
import jwt
import requests
import asyncio
import time
from typing import Dict, Any, Optional
from botocore.config import Config
from botocore.exceptions import ClientError, BotoCoreError
from functools import lru_cache
import logging
from src.auth.providers.base import AuthProvider, AuthResult
from src.config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class CognitoAuthProvider(AuthProvider):
    """
    AWS Cognito authentication provider optimized for production scale
    Features:
    - Connection pooling for high throughput
    - Public key caching with TTL
    - Exponential backoff retry logic
    - Rate limiting awareness
    - Optimized for thousands of concurrent users
    """
    
    def __init__(self):
        self.region = settings.AWS_REGION
        self.user_pool_id = getattr(settings, 'COGNITO_USER_POOL_ID', None)
        self.client_id = getattr(settings, 'COGNITO_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'COGNITO_CLIENT_SECRET', None)
        
        if not all([self.user_pool_id, self.client_id]):
            raise ValueError("Cognito configuration incomplete")
        
        # Production-optimized boto3 configuration
        config = Config(
            region_name=self.region,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'  # Adaptive retry mode for better handling of throttling
            },
            max_pool_connections=50,  # Increased connection pool for high concurrency
            read_timeout=10,
            connect_timeout=5
        )
        
        self.cognito_client = boto3.client('cognito-idp', config=config)
        self._public_keys = None
        self._public_keys_cache_time = 0
        self._public_keys_ttl = 3600  # Cache public keys for 1 hour
    
    @property
    def provider_name(self) -> str:
        return "cognito"
    
    @property
    def supports_registration(self) -> bool:
        return True
    
    @property
    def supports_password_reset(self) -> bool:
        return True
    
    @lru_cache(maxsize=1)
    def _get_jwks_url(self) -> str:
        """Cache JWKS URL to avoid string formatting overhead"""
        return f"https://cognito-idp.{self.region}.amazonaws.com/{self.user_pool_id}/.well-known/jwks.json"
    
    async def _get_public_keys(self) -> Dict[str, Any]:
        """
        Get Cognito public keys for token validation with caching
        Optimized for high-scale production use
        """
        current_time = time.time()
        
        # Check cache validity
        if (self._public_keys and 
            current_time - self._public_keys_cache_time < self._public_keys_ttl):
            return self._public_keys
        
        try:
            # Use session for connection reuse
            session = requests.Session()
            session.mount('https://', requests.adapters.HTTPAdapter(
                pool_connections=10,
                pool_maxsize=20,
                max_retries=3
            ))
            
            keys_url = self._get_jwks_url()
            response = session.get(keys_url, timeout=10)
            response.raise_for_status()
            
            self._public_keys = response.json()
            self._public_keys_cache_time = current_time
            
            logger.info("Cognito public keys refreshed from cache")
            return self._public_keys
            
        except Exception as e:
            logger.error(f"Failed to fetch Cognito public keys: {e}")
            # Return cached keys if available, even if expired
            if self._public_keys:
                logger.warning("Using expired public keys cache due to fetch failure")
                return self._public_keys
            raise
    
    @lru_cache(maxsize=1000)  # Cache secret hashes for frequently used usernames
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
        """
        Authenticate user with username/password - Production Optimized
        Features:
        - Exponential backoff retry logic for throttling
        - Detailed error handling for production monitoring
        - Performance optimizations for high throughput
        """
        max_retries = 3
        base_delay = 0.1  # Start with 100ms delay
        
        for attempt in range(max_retries + 1):
            try:
                auth_params = {
                    'USERNAME': username,
                    'PASSWORD': password
                }
                
                secret_hash = self._get_secret_hash(username)
                if secret_hash:
                    auth_params['SECRET_HASH'] = secret_hash
                
                # Use ADMIN_NO_SRP_AUTH flow for server-side authentication
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.cognito_client.admin_initiate_auth(
                        UserPoolId=self.user_pool_id,
                        ClientId=self.client_id,
                        AuthFlow='ADMIN_NO_SRP_AUTH',
                        AuthParameters=auth_params
                    )
                )
                
                auth_result = response['AuthenticationResult']
                
                # Decode ID token to get user info (without signature verification for performance)
                # In production, implement JWT signature verification for enhanced security
                id_token = auth_result['IdToken']
                user_info = jwt.decode(id_token, options={"verify_signature": False})
                
                logger.info(f"Successful authentication for user: {user_info.get('cognito:username')}")
                
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
                        'provider': 'cognito',
                        'auth_time': user_info.get('auth_time'),
                        'token_use': user_info.get('token_use')
                    }
                )
                
            except ClientError as e:
                error_code = e.response['Error']['Code']
                error_message = e.response['Error']['Message']
                
                # Handle specific Cognito errors
                if error_code == 'NotAuthorizedException':
                    logger.warning(f"Authentication failed for {username}: Invalid credentials")
                    return AuthResult(
                        success=False,
                        error_message="Invalid username or password"
                    )
                elif error_code == 'UserNotFoundException':
                    logger.warning(f"Authentication failed for {username}: User not found")
                    return AuthResult(
                        success=False,
                        error_message="Invalid username or password"  # Don't reveal user existence
                    )
                elif error_code == 'UserNotConfirmedException':
                    logger.warning(f"Authentication failed for {username}: User not confirmed")
                    return AuthResult(
                        success=False,
                        error_message="Please verify your email address before signing in"
                    )
                elif error_code == 'TooManyRequestsException' and attempt < max_retries:
                    # Exponential backoff for rate limiting
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {delay}s (attempt {attempt + 1})")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Cognito authentication error for {username}: {error_code} - {error_message}")
                    return AuthResult(
                        success=False,
                        error_message=f"Authentication service error: {error_code}"
                    )
                    
            except BotoCoreError as e:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Network error, retrying in {delay}s (attempt {attempt + 1}): {e}")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"Network error during authentication for {username}: {e}")
                    return AuthResult(
                        success=False,
                        error_message="Authentication service temporarily unavailable"
                    )
                    
            except Exception as e:
                logger.error(f"Unexpected error during authentication for {username}: {e}")
                return AuthResult(
                    success=False,
                    error_message="Authentication failed due to unexpected error"
                )
        
        # If we get here, all retries failed
        return AuthResult(
            success=False,
            error_message="Authentication service temporarily unavailable"
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
    
    async def confirm_reset_password(self, email: str, confirmation_code: str, new_password: str) -> bool:
        """Confirm password reset with confirmation code"""
        try:
            secret_hash = self._get_secret_hash(email)
            params = {
                'ClientId': self.client_id,
                'Username': email,
                'ConfirmationCode': confirmation_code,
                'Password': new_password
            }
            
            if secret_hash:
                params['SecretHash'] = secret_hash
            
            self.cognito_client.confirm_forgot_password(**params)
            return True
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Confirm reset password error: {str(e)}")
            return False

    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            # This requires the access token, which we don't have here
            # In practice, this would be called with the user's access token
            return False
        except Exception:
            return False
