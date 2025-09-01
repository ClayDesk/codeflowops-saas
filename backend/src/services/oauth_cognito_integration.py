"""
OAuth to Cognito Integration Service
Handles OAuth authentication and stores user credentials in AWS Cognito
"""

import boto3
import json
import uuid
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError
from ..auth.providers.cognito_oauth import CognitoOAuthProvider
from ..auth.providers.oauth import OAuthProvider
from ..auth.providers.base import AuthResult
from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class OAuthCognitoIntegration:
    """Service to integrate OAuth providers with AWS Cognito"""
    
    def __init__(self):
        self.cognito_oauth_provider = CognitoOAuthProvider()
        self.oauth_providers = {
            'github': OAuthProvider('github'),
            'google': OAuthProvider('google')
        }
        
    async def authenticate_with_oauth_and_store_in_cognito(
        self, 
        provider: str, 
        code: str, 
        redirect_uri: str
    ) -> AuthResult:
        """
        Authenticate with OAuth provider and store/update user in Cognito
        """
        try:
            # Step 1: Authenticate with OAuth provider
            oauth_provider = self.oauth_providers.get(provider)
            if not oauth_provider:
                return AuthResult(
                    success=False,
                    error_message=f"OAuth provider '{provider}' not supported"
                )
            
            oauth_result = await oauth_provider.authenticate_with_code(code, redirect_uri)
            if not oauth_result.success:
                return oauth_result
            
            # Step 2: Check if user exists in Cognito
            existing_username = await self.cognito_oauth_provider.find_user_by_oauth_id(
                provider, oauth_result.user_id, oauth_result.email
            )
            
            if existing_username:
                # Step 3a: User exists - update and authenticate
                logger.info(f"Existing {provider} user found in Cognito: {oauth_result.email}")
                return await self.cognito_oauth_provider.update_oauth_user(
                    existing_username, provider, oauth_result
                )
            else:
                # Step 3b: New user - create in Cognito
                logger.info(f"Creating new Cognito user for {provider} OAuth: {oauth_result.email}")
                return await self.cognito_oauth_provider.create_oauth_user(oauth_result, provider)
                
        except Exception as e:
            logger.error(f"OAuth Cognito integration error: {str(e)}")
            return AuthResult(
                success=False,
                error_message=f"Authentication integration failed: {str(e)}"
            )
    
    async def link_oauth_to_existing_user(
        self, 
        cognito_username: str, 
        provider: str, 
        oauth_result: AuthResult
    ) -> bool:
        """Link OAuth account to existing Cognito user"""
        try:
            result = await self.cognito_oauth_provider.update_oauth_user(
                cognito_username, provider, oauth_result
            )
            return result.success
        except Exception as e:
            logger.error(f"Error linking OAuth to existing user: {str(e)}")
            return False
    
    async def get_oauth_authorization_url(self, provider: str, redirect_uri: str, state: str) -> str:
        """Get OAuth authorization URL for the specified provider"""
        oauth_provider = self.oauth_providers.get(provider)
        if not oauth_provider:
            raise ValueError(f"OAuth provider '{provider}' not supported")
        
        config = oauth_provider.config
        
        if provider == 'github':
            return (f"{config['authorize_url']}?"
                   f"client_id={config['client_id']}&"
                   f"redirect_uri={redirect_uri}&"
                   f"scope={config['scope']}&"
                   f"state={state}")
        elif provider == 'google':
            return (f"{config['authorize_url']}?"
                   f"client_id={config['client_id']}&"
                   f"redirect_uri={redirect_uri}&"
                   f"scope={config['scope']}&"
                   f"response_type=code&"
                   f"state={state}")
        
        raise ValueError(f"Authorization URL generation not implemented for {provider}")


# Singleton instance
oauth_cognito_service = OAuthCognitoIntegration()
