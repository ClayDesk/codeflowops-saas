"""
Database connection and initialization for CodeFlowOps
Handles SQLite/PostgreSQL connections and schema creation
"""

import aiosqlite
import asyncpg
import logging
from typing import Optional, Union
from contextlib import asynccontextmanager
import os
from pathlib import Path

from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseManager:
    """
    Database connection manager
    Handles both SQLite and PostgreSQL connections
    """
    
    def __init__(self):
        self.connection = None
        self.connection_pool = None
        self.db_type = "sqlite"  # Default to SQLite
        
    async def initialize(self):
        """Initialize database connection and schema"""
        try:
            if settings.DATABASE_URL and settings.DATABASE_URL.startswith('postgresql'):
                await self._initialize_postgresql()
            else:
                await self._initialize_sqlite()
                
            await self._create_schema()
            logger.info(f"Database initialized successfully ({self.db_type})")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise
    
    async def _initialize_postgresql(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.connection_pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=settings.DB_POOL_MIN_SIZE,
                max_size=settings.DB_POOL_MAX_SIZE,
                command_timeout=60
            )
            self.db_type = "postgresql"
            logger.info("PostgreSQL connection pool created")
            
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {str(e)}")
            raise
    
    async def _initialize_sqlite(self):
        """Initialize SQLite connection"""
        try:
            # Ensure database directory exists
            db_path = settings.SQLITE_DATABASE_PATH or "data/codeflowops.db"
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            self.connection = await aiosqlite.connect(db_path)
            self.connection.row_factory = aiosqlite.Row
            self.db_type = "sqlite"
            logger.info(f"SQLite database connected: {db_path}")
            
        except Exception as e:
            logger.error(f"SQLite connection failed: {str(e)}")
            raise
    
    async def get_connection(self):
        """Get database connection"""
        if self.db_type == "postgresql":
            return await self.connection_pool.acquire()
        else:
            return self.connection
    
    async def release_connection(self, connection):
        """Release database connection"""
        if self.db_type == "postgresql":
            await self.connection_pool.release(connection)
        # SQLite connections are not released in the same way
    
    @asynccontextmanager
    async def get_transaction(self):
        """Get database transaction context"""
        if self.db_type == "postgresql":
            async with self.connection_pool.acquire() as conn:
                async with conn.transaction():
                    yield conn
        else:
            # SQLite auto-commits, but we can use manual transaction
            try:
                await self.connection.execute("BEGIN")
                yield self.connection
                await self.connection.commit()
            except Exception:
                await self.connection.rollback()
                raise
    
    async def _create_schema(self):
        """Create database schema"""
        try:
            if self.db_type == "postgresql":
                await self._create_postgresql_schema()
            else:
                await self._create_sqlite_schema()
                
        except Exception as e:
            logger.error(f"Schema creation failed: {str(e)}")
            raise
    
    async def _create_sqlite_schema(self):
        """Create SQLite schema"""
        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            organization TEXT,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            last_login TIMESTAMP
        );
        
        -- API Keys table
        CREATE TABLE IF NOT EXISTS api_keys (
            key_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            hashed_key TEXT UNIQUE NOT NULL,
            permissions TEXT NOT NULL,
            expires_at TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_used TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        
        -- Invitations table
        CREATE TABLE IF NOT EXISTS invitations (
            invitation_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            organization TEXT,
            code TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            is_used BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT NOT NULL,
            used_at TIMESTAMP,
            used_by TEXT,
            FOREIGN KEY (created_by) REFERENCES users (user_id) ON DELETE SET NULL,
            FOREIGN KEY (used_by) REFERENCES users (user_id) ON DELETE SET NULL
        );
        
        -- Deployment Sessions table (linked to auth system)
        CREATE TABLE IF NOT EXISTS deployment_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            github_url TEXT NOT NULL,
            project_name TEXT NOT NULL,
            project_type TEXT,
            current_step TEXT DEFAULT 'pending',
            progress_percentage INTEGER DEFAULT 0,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            completed_at TIMESTAMP,
            error_details TEXT,
            aws_resources TEXT,  -- JSON string of AWS resources
            deployment_url TEXT,
            build_logs TEXT,     -- JSON string of build logs
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        
        -- Session Audit Logs table
        CREATE TABLE IF NOT EXISTS session_audit_logs (
            log_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            resource TEXT NOT NULL,
            details TEXT,        -- JSON string
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES deployment_sessions (session_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        
        -- Authentication Events table
        CREATE TABLE IF NOT EXISTS auth_events (
            event_id TEXT PRIMARY KEY,
            user_id TEXT,
            email TEXT,
            event_type TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            ip_address TEXT NOT NULL,
            user_agent TEXT,
            details TEXT,        -- JSON string
            timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL
        );
        
        -- User Quotas table
        CREATE TABLE IF NOT EXISTS user_quotas (
            user_id TEXT PRIMARY KEY,
            deployments_per_month INTEGER NOT NULL DEFAULT 50,
            concurrent_deployments INTEGER NOT NULL DEFAULT 3,
            storage_limit_gb INTEGER DEFAULT 10,
            custom_quotas TEXT,  -- JSON string for additional quotas
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        
        -- Indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
        CREATE INDEX IF NOT EXISTS idx_users_organization ON users (organization);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);
        
        CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys (user_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_hashed_key ON api_keys (hashed_key);
        CREATE INDEX IF NOT EXISTS idx_api_keys_created_at ON api_keys (created_at);
        
        CREATE INDEX IF NOT EXISTS idx_deployment_sessions_user_id ON deployment_sessions (user_id);
        CREATE INDEX IF NOT EXISTS idx_deployment_sessions_status ON deployment_sessions (status);
        CREATE INDEX IF NOT EXISTS idx_deployment_sessions_created_at ON deployment_sessions (created_at);
        
        CREATE INDEX IF NOT EXISTS idx_session_audit_logs_session_id ON session_audit_logs (session_id);
        CREATE INDEX IF NOT EXISTS idx_session_audit_logs_user_id ON session_audit_logs (user_id);
        CREATE INDEX IF NOT EXISTS idx_session_audit_logs_timestamp ON session_audit_logs (timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_auth_events_user_id ON auth_events (user_id);
        CREATE INDEX IF NOT EXISTS idx_auth_events_email ON auth_events (email);
        CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events (timestamp);
        CREATE INDEX IF NOT EXISTS idx_auth_events_event_type ON auth_events (event_type);
        """
        
        # Execute schema creation
        await self.connection.executescript(schema_sql)
        await self.connection.commit()
        logger.info("SQLite schema created successfully")
    
    async def _create_postgresql_schema(self):
        """Create PostgreSQL schema"""
        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            organization TEXT,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            last_login TIMESTAMP WITH TIME ZONE
        );
        
        -- API Keys table
        CREATE TABLE IF NOT EXISTS api_keys (
            key_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            hashed_key TEXT UNIQUE NOT NULL,
            permissions TEXT NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_used TIMESTAMP WITH TIME ZONE,
            CONSTRAINT fk_api_keys_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        
        -- Invitations table
        CREATE TABLE IF NOT EXISTS invitations (
            invitation_id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            organization TEXT,
            code TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            is_used BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            created_by TEXT NOT NULL,
            used_at TIMESTAMP WITH TIME ZONE,
            used_by TEXT,
            CONSTRAINT fk_invitations_created_by FOREIGN KEY (created_by) REFERENCES users (user_id) ON DELETE SET NULL,
            CONSTRAINT fk_invitations_used_by FOREIGN KEY (used_by) REFERENCES users (user_id) ON DELETE SET NULL
        );
        
        -- Deployment Sessions table
        CREATE TABLE IF NOT EXISTS deployment_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            github_url TEXT NOT NULL,
            project_name TEXT NOT NULL,
            project_type TEXT,
            current_step TEXT DEFAULT 'pending',
            progress_percentage INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            error_details TEXT,
            aws_resources JSONB,
            deployment_url TEXT,
            build_logs JSONB,
            CONSTRAINT fk_deployment_sessions_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        
        -- Session Audit Logs table
        CREATE TABLE IF NOT EXISTS session_audit_logs (
            log_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            resource TEXT NOT NULL,
            details JSONB,
            ip_address INET,
            user_agent TEXT,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_session_audit_logs_session_id FOREIGN KEY (session_id) REFERENCES deployment_sessions (session_id) ON DELETE CASCADE,
            CONSTRAINT fk_session_audit_logs_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        
        -- Authentication Events table
        CREATE TABLE IF NOT EXISTS auth_events (
            event_id TEXT PRIMARY KEY,
            user_id TEXT,
            email TEXT,
            event_type TEXT NOT NULL,
            success BOOLEAN NOT NULL,
            ip_address INET NOT NULL,
            user_agent TEXT,
            details JSONB,
            timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_auth_events_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE SET NULL
        );
        
        -- User Quotas table
        CREATE TABLE IF NOT EXISTS user_quotas (
            user_id TEXT PRIMARY KEY,
            deployments_per_month INTEGER NOT NULL DEFAULT 50,
            concurrent_deployments INTEGER NOT NULL DEFAULT 3,
            storage_limit_gb INTEGER DEFAULT 10,
            custom_quotas JSONB,
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            CONSTRAINT fk_user_quotas_user_id FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
        );
        
        -- Indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
        CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
        CREATE INDEX IF NOT EXISTS idx_users_organization ON users (organization);
        CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at);
        
        CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys (user_id);
        CREATE INDEX IF NOT EXISTS idx_api_keys_hashed_key ON api_keys (hashed_key);
        CREATE INDEX IF NOT EXISTS idx_api_keys_created_at ON api_keys (created_at);
        
        CREATE INDEX IF NOT EXISTS idx_deployment_sessions_user_id ON deployment_sessions (user_id);
        CREATE INDEX IF NOT EXISTS idx_deployment_sessions_status ON deployment_sessions (status);
        CREATE INDEX IF NOT EXISTS idx_deployment_sessions_created_at ON deployment_sessions (created_at);
        
        CREATE INDEX IF NOT EXISTS idx_session_audit_logs_session_id ON session_audit_logs (session_id);
        CREATE INDEX IF NOT EXISTS idx_session_audit_logs_user_id ON session_audit_logs (user_id);
        CREATE INDEX IF NOT EXISTS idx_session_audit_logs_timestamp ON session_audit_logs (timestamp);
        
        CREATE INDEX IF NOT EXISTS idx_auth_events_user_id ON auth_events (user_id);
        CREATE INDEX IF NOT EXISTS idx_auth_events_email ON auth_events (email);
        CREATE INDEX IF NOT EXISTS idx_auth_events_timestamp ON auth_events (timestamp);
        CREATE INDEX IF NOT EXISTS idx_auth_events_event_type ON auth_events (event_type);
        """
        
        async with self.connection_pool.acquire() as conn:
            await conn.execute(schema_sql)
        
        logger.info("PostgreSQL schema created successfully")
    
    async def create_default_admin(self):
        """Create default admin user if none exists"""
        try:
            from auth.auth_utils import hash_password
            import uuid
            
            # Check if any admin users exist
            if self.db_type == "postgresql":
                async with self.connection_pool.acquire() as conn:
                    admin_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM users WHERE role = 'admin'"
                    )
            else:
                cursor = await self.connection.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'admin'"
                )
                admin_count = (await cursor.fetchone())[0]
            
            if admin_count == 0:
                # Create default admin user
                admin_id = str(uuid.uuid4())
                admin_email = settings.DEFAULT_ADMIN_EMAIL or "admin@codeflowops.com"
                admin_password = settings.DEFAULT_ADMIN_PASSWORD or "CodeFlow2024!"
                hashed_password = hash_password(admin_password)
                
                if self.db_type == "postgresql":
                    async with self.connection_pool.acquire() as conn:
                        await conn.execute("""
                            INSERT INTO users (
                                user_id, email, username, full_name, hashed_password, role
                            ) VALUES ($1, $2, $3, $4, $5, $6)
                        """, admin_id, admin_email, "admin", "System Administrator", 
                            hashed_password, "admin")
                else:
                    await self.connection.execute("""
                        INSERT INTO users (
                            user_id, email, username, full_name, hashed_password, role
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (admin_id, admin_email, "admin", "System Administrator", 
                          hashed_password, "admin"))
                    await self.connection.commit()
                
                logger.info(f"Default admin user created: {admin_email}")
                logger.warning(f"Default admin password: {admin_password}")
                logger.warning("Please change the default admin password immediately!")
                
        except Exception as e:
            logger.error(f"Failed to create default admin: {str(e)}")
    
    async def close(self):
        """Close database connections"""
        try:
            if self.db_type == "postgresql" and self.connection_pool:
                await self.connection_pool.close()
            elif self.connection:
                await self.connection.close()
                
            logger.info("Database connections closed")
            
        except Exception as e:
            logger.error(f"Error closing database connections: {str(e)}")


# Global database manager instance
_db_manager = None


async def get_database_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()
        await _db_manager.create_default_admin()
    
    return _db_manager


async def get_database_connection():
    """Get database connection for dependency injection"""
    db_manager = await get_database_manager()
    return await db_manager.get_connection()


async def close_database():
    """Close database connections (for shutdown)"""
    global _db_manager
    
    if _db_manager:
        await _db_manager.close()
        _db_manager = None
