"""
Authentication utilities for CodeFlowOps
Handles JWT tokens, password hashing, and user management
"""

import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
import bcrypt
import logging
from enum import Enum
import uuid

from ..config.env import get_settings
from ..models.auth_models import User, APIKey, UserRole
from ..database.connection import get_database_connection

logger = logging.getLogger(__name__)
settings = get_settings()

# Security schemes
security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthManager:
    """
    Core authentication manager
    Handles JWT validation and user authorization
    """
    
    @staticmethod
    def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """
        Get current authenticated user from JWT token
        
        Validates JWT token and returns user information.
        """
        try:
            token = credentials.credentials
            payload = verify_token(token)
            
            user_id = payload.get("sub")
            email = payload.get("email")
            role = payload.get("role")
            organization = payload.get("organization")
            
            if not user_id or not email:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            return {
                "user_id": user_id,
                "email": email,
                "role": role,
                "organization": organization
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        except Exception as e:
            logger.error(f"Token validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )
    
    @staticmethod
    def get_current_user_or_api_key(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        api_key: Optional[str] = Depends(api_key_header)
    ) -> Dict[str, Any]:
        """
        Get current user from JWT token or API key
        
        Supports both JWT and API key authentication.
        """
        try:
            # Try API key first
            if api_key:
                return AuthManager._validate_api_key(api_key)
            
            # Fall back to JWT token
            if credentials:
                return AuthManager.get_current_user.__wrapped__(credentials)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )
    
    @staticmethod
    def require_role(required_role: UserRole):
        """
        Require specific user role
        
        Decorator factory for role-based access control.
        """
        def role_checker(current_user: Dict = Depends(AuthManager.get_current_user)):
            user_role = UserRole(current_user.get("role", "user"))
            
            # Admin can access everything
            if user_role == UserRole.ADMIN:
                return current_user
            
            # Check if user has required role
            role_hierarchy = {
                UserRole.VIEWER: 1,
                UserRole.USER: 2,
                UserRole.ADMIN: 3
            }
            
            if role_hierarchy.get(user_role, 0) < role_hierarchy.get(required_role, 999):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required role: {required_role.value}"
                )
            
            return current_user
        
        return role_checker
    
    @staticmethod
    def require_admin(current_user: Dict = Depends(get_current_user)):
        """Require admin role"""
        if current_user.get("role") != UserRole.ADMIN.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user
    
    @staticmethod
    def require_user_or_admin(current_user: Dict = Depends(get_current_user)):
        """Require user role or higher"""
        role = current_user.get("role")
        if role not in [UserRole.USER.value, UserRole.ADMIN.value]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User access required"
            )
        return current_user
    
    @staticmethod
    async def _validate_api_key(api_key: str) -> Dict[str, Any]:
        """
        Validate API key and return user information
        
        Checks API key validity and permissions.
        """
        try:
            user_manager = UserManager()
            key_record = await user_manager.get_api_key_by_value(api_key)
            
            if not key_record:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid API key"
                )
            
            if not key_record.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key is deactivated"
                )
            
            if key_record.expires_at and key_record.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="API key has expired"
                )
            
            # Get user information
            user = await user_manager.get_user_by_id(key_record.user_id)
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is inactive"
                )
            
            # Update last used
            await user_manager.update_api_key_last_used(key_record.key_id)
            
            return {
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role.value,
                "organization": user.organization,
                "auth_method": "api_key",
                "api_key_permissions": key_record.permissions
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key validation failed"
            )


class UserManager:
    """
    User management operations
    Handles user CRUD operations and authentication
    """
    
    def __init__(self):
        self.db = None
    
    async def get_database(self):
        """Get database connection"""
        if not self.db:
            self.db = await get_database_connection()
        return self.db
    
    async def create_user(
        self,
        email: str,
        username: str,
        full_name: str,
        hashed_password: str,
        role: UserRole = UserRole.USER,
        organization: Optional[str] = None
    ) -> User:
        """
        Create new user
        
        Inserts user record into database.
        """
        try:
            db = await self.get_database()
            user_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO users (
                    user_id, email, username, full_name, hashed_password,
                    role, organization, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await db.execute(query, (
                user_id, email, username, full_name, hashed_password,
                role.value, organization, True, datetime.utcnow()
            ))
            await db.commit()
            
            return await self.get_user_by_id(user_id)
            
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address"""
        try:
            db = await self.get_database()
            
            query = "SELECT * FROM users WHERE email = ? AND is_active = 1"
            cursor = await db.execute(query, (email,))
            row = await cursor.fetchone()
            
            if row:
                return self._row_to_user(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by email: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            db = await self.get_database()
            
            query = "SELECT * FROM users WHERE user_id = ?"
            cursor = await db.execute(query, (user_id,))
            row = await cursor.fetchone()
            
            if row:
                return self._row_to_user(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user by ID: {str(e)}")
            return None
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user with email and password
        
        Verifies credentials and returns user if valid.
        """
        try:
            user = await self.get_user_by_email(email)
            if user and verify_password(password, user.hashed_password):
                return user
            return None
            
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return None
    
    async def update_last_login(self, user_id: str):
        """Update user's last login timestamp"""
        try:
            db = await self.get_database()
            
            query = "UPDATE users SET last_login = ? WHERE user_id = ?"
            await db.execute(query, (datetime.utcnow(), user_id))
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update last login: {str(e)}")
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> User:
        """Update user information"""
        try:
            db = await self.get_database()
            
            # Build dynamic update query
            set_clauses = []
            values = []
            
            allowed_fields = ['username', 'full_name', 'organization']
            for field, value in update_data.items():
                if field in allowed_fields and value is not None:
                    set_clauses.append(f"{field} = ?")
                    values.append(value)
            
            if not set_clauses:
                raise ValueError("No valid fields to update")
            
            set_clauses.append("updated_at = ?")
            values.append(datetime.utcnow())
            values.append(user_id)
            
            query = f"UPDATE users SET {', '.join(set_clauses)} WHERE user_id = ?"
            await db.execute(query, values)
            await db.commit()
            
            return await self.get_user_by_id(user_id)
            
        except Exception as e:
            logger.error(f"Failed to update user: {str(e)}")
            raise
    
    async def update_password(self, user_id: str, new_hashed_password: str):
        """Update user password"""
        try:
            db = await self.get_database()
            
            query = "UPDATE users SET hashed_password = ?, updated_at = ? WHERE user_id = ?"
            await db.execute(query, (new_hashed_password, datetime.utcnow(), user_id))
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update password: {str(e)}")
            raise
    
    async def update_user_role(self, user_id: str, new_role: UserRole):
        """Update user role"""
        try:
            db = await self.get_database()
            
            query = "UPDATE users SET role = ?, updated_at = ? WHERE user_id = ?"
            await db.execute(query, (new_role.value, datetime.utcnow(), user_id))
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update user role: {str(e)}")
            raise
    
    async def update_user_status(self, user_id: str, is_active: bool):
        """Update user active status"""
        try:
            db = await self.get_database()
            
            query = "UPDATE users SET is_active = ?, updated_at = ? WHERE user_id = ?"
            await db.execute(query, (is_active, datetime.utcnow(), user_id))
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update user status: {str(e)}")
            raise
    
    async def list_users(
        self,
        page: int = 1,
        page_size: int = 50,
        role_filter: Optional[UserRole] = None,
        organization_filter: Optional[str] = None
    ) -> tuple[List[User], int]:
        """List users with pagination and filtering"""
        try:
            db = await self.get_database()
            
            # Build query with filters
            where_clauses = []
            values = []
            
            if role_filter:
                where_clauses.append("role = ?")
                values.append(role_filter.value)
            
            if organization_filter:
                where_clauses.append("organization = ?")
                values.append(organization_filter)
            
            where_clause = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM users {where_clause}"
            cursor = await db.execute(count_query, values)
            total_count = (await cursor.fetchone())[0]
            
            # Get paginated results
            offset = (page - 1) * page_size
            query = f"""
                SELECT * FROM users {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            
            cursor = await db.execute(query, values + [page_size, offset])
            rows = await cursor.fetchall()
            
            users = [self._row_to_user(row) for row in rows]
            
            return users, total_count
            
        except Exception as e:
            logger.error(f"Failed to list users: {str(e)}")
            return [], 0
    
    # API Key Management
    
    async def create_api_key(
        self,
        user_id: str,
        name: str,
        api_key: str,
        permissions: List[str],
        expires_at: Optional[datetime] = None
    ) -> APIKey:
        """Create new API key"""
        try:
            db = await self.get_database()
            key_id = str(uuid.uuid4())
            
            # Hash the API key for storage
            hashed_key = hash_api_key(api_key)
            
            query = """
                INSERT INTO api_keys (
                    key_id, user_id, name, hashed_key, permissions,
                    expires_at, is_active, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await db.execute(query, (
                key_id, user_id, name, hashed_key, ','.join(permissions),
                expires_at, True, datetime.utcnow()
            ))
            await db.commit()
            
            return await self.get_api_key(key_id)
            
        except Exception as e:
            logger.error(f"Failed to create API key: {str(e)}")
            raise
    
    async def get_api_key(self, key_id: str) -> Optional[APIKey]:
        """Get API key by ID"""
        try:
            db = await self.get_database()
            
            query = "SELECT * FROM api_keys WHERE key_id = ?"
            cursor = await db.execute(query, (key_id,))
            row = await cursor.fetchone()
            
            if row:
                return self._row_to_api_key(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get API key: {str(e)}")
            return None
    
    async def get_api_key_by_value(self, api_key: str) -> Optional[APIKey]:
        """Get API key by value"""
        try:
            db = await self.get_database()
            hashed_key = hash_api_key(api_key)
            
            query = "SELECT * FROM api_keys WHERE hashed_key = ? AND is_active = 1"
            cursor = await db.execute(query, (hashed_key,))
            row = await cursor.fetchone()
            
            if row:
                return self._row_to_api_key(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get API key by value: {str(e)}")
            return None
    
    async def get_user_api_keys(self, user_id: str) -> List[APIKey]:
        """Get all API keys for a user"""
        try:
            db = await self.get_database()
            
            query = "SELECT * FROM api_keys WHERE user_id = ? ORDER BY created_at DESC"
            cursor = await db.execute(query, (user_id,))
            rows = await cursor.fetchall()
            
            return [self._row_to_api_key(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get user API keys: {str(e)}")
            return []
    
    async def update_api_key_last_used(self, key_id: str):
        """Update API key last used timestamp"""
        try:
            db = await self.get_database()
            
            query = "UPDATE api_keys SET last_used = ? WHERE key_id = ?"
            await db.execute(query, (datetime.utcnow(), key_id))
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to update API key last used: {str(e)}")
    
    async def delete_api_key(self, key_id: str):
        """Delete API key"""
        try:
            db = await self.get_database()
            
            query = "DELETE FROM api_keys WHERE key_id = ?"
            await db.execute(query, (key_id,))
            await db.commit()
            
        except Exception as e:
            logger.error(f"Failed to delete API key: {str(e)}")
            raise
    
    # Helper methods
    
    async def get_user_deployment_count(self, user_id: str) -> int:
        """Get total deployment count for user"""
        try:
            db = await self.get_database()
            
            query = "SELECT COUNT(*) FROM deployment_sessions WHERE user_id = ?"
            cursor = await db.execute(query, (user_id,))
            count = (await cursor.fetchone())[0]
            
            return count
            
        except Exception as e:
            logger.error(f"Failed to get deployment count: {str(e)}")
            return 0
    
    async def get_user_quota(self, user_id: str) -> Dict[str, Any]:
        """Get user quota information"""
        try:
            # This would implement quota logic based on user role/plan
            user = await self.get_user_by_id(user_id)
            if not user:
                return {}
            
            # Default quotas based on role
            quotas = {
                UserRole.VIEWER: {"deployments_per_month": 0, "concurrent_deployments": 0},
                UserRole.USER: {"deployments_per_month": 50, "concurrent_deployments": 3},
                UserRole.ADMIN: {"deployments_per_month": -1, "concurrent_deployments": -1}  # Unlimited
            }
            
            return quotas.get(user.role, quotas[UserRole.USER])
            
        except Exception as e:
            logger.error(f"Failed to get user quota: {str(e)}")
            return {}
    
    async def validate_invitation(self, invitation_code: str) -> bool:
        """Validate invitation code"""
        try:
            db = await self.get_database()
            
            query = """
                SELECT * FROM invitations 
                WHERE code = ? AND is_used = 0 AND expires_at > ?
            """
            
            cursor = await db.execute(query, (invitation_code, datetime.utcnow()))
            row = await cursor.fetchone()
            
            return row is not None
            
        except Exception as e:
            logger.error(f"Failed to validate invitation: {str(e)}")
            return False
    
    def _row_to_user(self, row) -> User:
        """Convert database row to User object"""
        return User(
            user_id=row[0],
            email=row[1],
            username=row[2],
            full_name=row[3],
            hashed_password=row[4],
            role=UserRole(row[5]),
            organization=row[6],
            is_active=bool(row[7]),
            created_at=row[8],
            updated_at=row[9],
            last_login=row[10]
        )
    
    def _row_to_api_key(self, row) -> APIKey:
        """Convert database row to APIKey object"""
        return APIKey(
            key_id=row[0],
            user_id=row[1],
            name=row[2],
            hashed_key=row[3],
            permissions=row[4].split(',') if row[4] else [],
            expires_at=row[5],
            is_active=bool(row[6]),
            created_at=row[7],
            last_used=row[8]
        )


# Utility functions

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """
    Create JWT access token
    
    Generates signed JWT token with expiration.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token
    
    Validates token signature and expiration.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt
    
    Generates secure password hash with salt.
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Compares plain password with bcrypt hash.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception:
        return False


def generate_api_key() -> str:
    """
    Generate secure API key
    
    Creates cryptographically secure random API key.
    """
    return f"cfops_{secrets.token_urlsafe(32)}"


def hash_api_key(api_key: str) -> str:
    """
    Hash API key for secure storage
    
    Uses SHA-256 to hash API key for database storage.
    """
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()


# JWT utility functions
def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Dict containing token payload
        
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.ExpiredSignatureError("Token has expired")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Invalid token")

def create_jwt_token(user_data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT token for user
    
    Args:
        user_data: User data to encode in token
        expires_delta: Optional expiration time delta
        
    Returns:
        JWT token string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode = user_data.copy()
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def create_refresh_token(user_data: Dict[str, Any]) -> str:
    """
    Create refresh token for user
    
    Args:
        user_data: User data to encode in token
        
    Returns:
        Refresh token string
    """
    # Create refresh token with longer expiration (7 days)
    expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode = user_data.copy()
    to_encode.update({
        "exp": expire,
        "type": "refresh"  # Mark as refresh token
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt

async def get_user_by_id(user_id: str) -> Optional[User]:
    """
    Get user by ID from database
    
    Args:
        user_id: User ID
        
    Returns:
        User object if found, None otherwise
    """
    try:
        # This is a placeholder implementation
        # In real implementation, would query the database
        
        # For testing, return a mock user
        class MockUser:
            def __init__(self, user_id):
                self.id = user_id
                self.email = f"user{user_id}@example.com"
                self.name = f"User {user_id}"
                self.role = "user"
                self.plan = "free"
                self.is_active = True
        
        return MockUser(user_id)
        
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {str(e)}")
        return None

# Import fix for circular dependency
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Wrapper function to avoid circular imports"""
    return AuthManager.get_current_user(credentials)
