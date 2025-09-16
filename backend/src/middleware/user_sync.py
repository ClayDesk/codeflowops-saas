"""
User Sync Middleware - Automatically sync Cognito users to database
Ensures that authenticated users always have corresponding database records
"""

import logging
from typing import Optional
from datetime import datetime
import uuid
import hashlib

from ..utils.database import get_db_context
from ..models.enhanced_models import User
from ..auth.providers.cognito import AuthResult

logger = logging.getLogger(__name__)

class UserSyncMiddleware:
    """Middleware to automatically sync Cognito users with database"""
    
    @staticmethod
    async def ensure_user_exists(auth_result: AuthResult) -> Optional[User]:
        """
        Ensure that a Cognito-authenticated user has a corresponding database record.
        Creates the user record if it doesn't exist.
        
        Args:
            auth_result: The authentication result from Cognito
            
        Returns:
            User: The database user record (existing or newly created)
        """
        if not auth_result.success or not auth_result.email:
            logger.warning("Cannot sync user: invalid auth result")
            return None
            
        try:
            # Use direct SQLite connection instead of get_db_context
            import sqlite3
            import os
            
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'codeflowops.db')
            
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Check if user already exists
                cursor.execute("SELECT user_id, email FROM users WHERE email = ?", (auth_result.email,))
                result = cursor.fetchone()
                
                if result:
                    logger.debug(f"User {auth_result.email} already exists in database")
                    return {
                        "user_id": result[0],
                        "email": result[1],
                        "exists": True
                    }
                
                # Create new user record from Cognito data using SQLite
                logger.info(f"Creating database record for Cognito user: {auth_result.email}")
                
                user_id = auth_result.user_id or str(uuid.uuid4())
                username = auth_result.username or auth_result.email.split('@')[0]
                full_name = auth_result.full_name or _extract_name_from_email(auth_result.email)
                now = datetime.utcnow().isoformat()
                
                cursor.execute("""
                    INSERT INTO users (
                        user_id, email, username, full_name, hashed_password,
                        role, organization, is_active, created_at, updated_at, last_login
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    auth_result.email,
                    username,
                    full_name,
                    _generate_cognito_placeholder_hash(),
                    'user',
                    None,
                    True,
                    now,
                    now,
                    None
                ))
                
                conn.commit()
                
                logger.info(f"✅ Successfully created database user record for {auth_result.email}")
                logger.info(f"   User ID: {user_id}")
                logger.info(f"   Email: {auth_result.email}")
                logger.info(f"   Username: {username}")
                
                return {
                    "user_id": user_id,
                    "email": auth_result.email,
                    "username": username,
                    "exists": True
                }
                
        except Exception as e:
            logger.error(f"❌ Failed to sync user {auth_result.email} to database: {str(e)}")
            # Don't raise exception - let authentication continue even if sync fails
            return None
    
    @staticmethod
    async def sync_user_on_login(auth_result: AuthResult) -> AuthResult:
        """
        Middleware function to sync user during login process.
        Updates auth_result with database user information.
        
        Args:
            auth_result: Original auth result from Cognito
            
        Returns:
            AuthResult: Updated auth result with database sync confirmation
        """
        if not auth_result.success:
            return auth_result
            
        try:
            # Ensure user exists in database
            db_user = await UserSyncMiddleware.ensure_user_exists(auth_result)
            
            if db_user:
                # Update auth result with confirmed database user info
                auth_result.metadata = auth_result.metadata or {}
                auth_result.metadata.update({
                    'database_synced': True,
                    'database_user_id': db_user.user_id,
                    'sync_timestamp': datetime.utcnow().isoformat()
                })
                
                logger.info(f"✅ User {auth_result.email} successfully synced with database")
            else:
                # Sync failed but don't block authentication
                auth_result.metadata = auth_result.metadata or {}
                auth_result.metadata.update({
                    'database_synced': False,
                    'sync_error': 'Failed to create database record',
                    'sync_timestamp': datetime.utcnow().isoformat()
                })
                
                logger.warning(f"⚠️ User {auth_result.email} authenticated but database sync failed")
            
            return auth_result
            
        except Exception as e:
            logger.error(f"❌ User sync middleware error for {auth_result.email}: {str(e)}")
            # Don't block authentication - just log the error
            auth_result.metadata = auth_result.metadata or {}
            auth_result.metadata['sync_error'] = str(e)
            return auth_result


def _extract_name_from_email(email: str) -> str:
    """Extract a reasonable name from email address"""
    try:
        local_part = email.split('@')[0]
        # Handle common patterns like firstname.lastname or firstname_lastname
        if '.' in local_part:
            parts = local_part.split('.')
            return ' '.join(part.capitalize() for part in parts)
        elif '_' in local_part:
            parts = local_part.split('_')
            return ' '.join(part.capitalize() for part in parts)
        else:
            return local_part.capitalize()
    except:
        return "User"


def _generate_cognito_placeholder_hash() -> str:
    """Generate a placeholder password hash for Cognito users"""
    return hashlib.sha256("COGNITO_AUTH_USER_PLACEHOLDER".encode()).hexdigest()