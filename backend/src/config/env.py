"""
Environment configuration for CodeFlowOps
Centralized settings management with environment variable support
"""

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from pydantic import Field, field_validator
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    APP_NAME: str = "CodeFlowOps"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    
    # Security Settings
    SECRET_KEY: str = Field(default="your-super-secret-key-change-this-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # Authentication Settings
    REQUIRE_INVITATION: bool = Field(default=False)
    MAX_API_KEYS_PER_USER: int = Field(default=5)
    PASSWORD_MIN_LENGTH: int = Field(default=8)
    DEFAULT_ADMIN_EMAIL: Optional[str] = Field(None)
    DEFAULT_ADMIN_PASSWORD: Optional[str] = Field(None)
    
    # Database Settings
    DATABASE_URL: Optional[str] = Field(None)
    SQLITE_DATABASE_PATH: str = Field(default="data/codeflowops.db")
    DB_POOL_MIN_SIZE: int = Field(default=5)
    DB_POOL_MAX_SIZE: int = Field(default=20)
    
    # Redis Settings
    REDIS_URL: Optional[str] = Field(None)
    REDIS_SESSION_PREFIX: str = Field(default="codeflowops:session")
    REDIS_MAX_CONNECTIONS: int = Field(default=50)
    SESSION_TTL_HOURS: int = Field(default=24)
    MAX_SESSION_LOGS: int = Field(default=1000)
    
    # AWS Settings
    AWS_REGION: str = Field(default="us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None)
    
    # AWS Cognito Settings  
    COGNITO_USER_POOL_ID: Optional[str] = Field(None)
    COGNITO_CLIENT_ID: Optional[str] = Field(None)
    COGNITO_CLIENT_SECRET: Optional[str] = Field(None)
    COGNITO_DOMAIN: Optional[str] = Field(None)
    
    # AWS CodeBuild Settings
    CODEBUILD_PROJECT_NAME: str = Field(default="codeflowops-react-build")
    CODEBUILD_ROLE_ARN: Optional[str] = Field(None)
    
    # AWS S3 Settings
    S3_BUCKET_NAME: str = Field(default="codeflowops-deployments")
    S3_STATIC_BUCKET: str = Field(default="codeflowops-static")
    
    # GitHub Settings
    GITHUB_TOKEN: Optional[str] = Field(None)
    GITHUB_WEBHOOK_SECRET: Optional[str] = Field(None)
    
    # OAuth Settings
    GITHUB_CLIENT_ID: Optional[str] = Field(None)
    GITHUB_CLIENT_SECRET: Optional[str] = Field(None)
    GOOGLE_CLIENT_ID: Optional[str] = Field(None)
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(None)

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings

from pydantic import Field, field_validator
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application Settings
    APP_NAME: str = "CodeFlowOps"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    
    # Security Settings
    SECRET_KEY: str = Field(default="your-super-secret-key-change-this-in-production")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    
    # Authentication Settings
    REQUIRE_INVITATION: bool = Field(default=False)
    MAX_API_KEYS_PER_USER: int = Field(default=5)
    PASSWORD_MIN_LENGTH: int = Field(default=8)
    DEFAULT_ADMIN_EMAIL: Optional[str] = Field(None)
    DEFAULT_ADMIN_PASSWORD: Optional[str] = Field(None)
    
    # Database Settings
    DATABASE_URL: Optional[str] = Field(None)
    SQLITE_DATABASE_PATH: str = Field(default="data/codeflowops.db")
    DB_POOL_MIN_SIZE: int = Field(default=5)
    DB_POOL_MAX_SIZE: int = Field(default=20)
    
    # Redis Settings
    REDIS_URL: Optional[str] = Field(None)
    REDIS_SESSION_PREFIX: str = Field(default="codeflowops:session")
    REDIS_MAX_CONNECTIONS: int = Field(default=50)
    SESSION_TTL_HOURS: int = Field(default=24)
    MAX_SESSION_LOGS: int = Field(default=1000)
    
    # Rate Limiting Settings
    RATE_LIMIT_ENABLED: bool = Field(default=True)
    DEFAULT_RATE_LIMIT: int = Field(default=100)
    AUTH_RATE_LIMIT: int = Field(default=5)
    DEPLOYMENT_RATE_LIMIT: int = Field(default=10)
    
    # AWS Settings
    AWS_REGION: str = Field(default="us-east-1")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None)
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None)
    AWS_S3_BUCKET_PREFIX: str = Field(default="codeflowops")
    AWS_CLOUDFRONT_DISTRIBUTION_PREFIX: str = Field(default="codeflowops")
    
    # AWS Cognito Settings
    COGNITO_USER_POOL_ID: Optional[str] = Field(None)
    COGNITO_CLIENT_ID: Optional[str] = Field(None)
    COGNITO_CLIENT_SECRET: Optional[str] = Field(None)
    COGNITO_DOMAIN: Optional[str] = Field(None)
    COGNITO_REDIRECT_URI: str = Field(default="http://localhost:3000/auth/callback")
    
    # GitHub Settings
    GITHUB_TOKEN: Optional[str] = Field(None)
    GITHUB_WEBHOOK_SECRET: Optional[str] = Field(None)
    
    # OAuth Settings
    GITHUB_CLIENT_ID: Optional[str] = Field(None)
    GITHUB_CLIENT_SECRET: Optional[str] = Field(None)
    GOOGLE_CLIENT_ID: Optional[str] = Field(None)
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(None)
    
    # Deployment Settings
    MAX_CONCURRENT_DEPLOYMENTS: int = Field(default=5)
    DEPLOYMENT_TIMEOUT_MINUTES: int = Field(default=30)
    BUILD_TIMEOUT_MINUTES: int = Field(default=15)
    
    # Storage Settings
    UPLOAD_MAX_SIZE_MB: int = Field(default=100)
    TEMP_DIR: str = Field(default="/tmp/codeflowops")
    LOG_RETENTION_DAYS: int = Field(default=30)
    
    # WebSocket Settings
    WEBSOCKET_MAX_CONNECTIONS: int = Field(default=1000)
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30)
    
    # Monitoring Settings
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=8001)
    HEALTH_CHECK_INTERVAL: int = Field(default=60)
    
    # Email Settings (for notifications)
    SMTP_HOST: Optional[str] = Field(None)
    SMTP_PORT: int = Field(default=587)
    SMTP_USERNAME: Optional[str] = Field(None)
    SMTP_PASSWORD: Optional[str] = Field(None)
    SMTP_FROM_EMAIL: Optional[str] = Field(None)
    
    # Logging Settings
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # CORS Settings
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        return self.CORS_ORIGINS
    
    # Frontend Settings
    FRONTEND_URL: str = Field(default="http://localhost:3000")
    API_PREFIX: str = Field(default="/api/v1")
    
    # Feature Flags
    ENABLE_WEBSOCKETS: bool = Field(default=True)
    ENABLE_API_KEYS: bool = Field(default=True)
    ENABLE_INVITATIONS: bool = Field(default=True)
    ENABLE_AUDIT_LOGS: bool = Field(default=True)
    
    # Development Settings
    RELOAD_ON_CHANGE: bool = Field(default=False)
    SHOW_SQL_QUERIES: bool = Field(default=False)
    MOCK_AWS_SERVICES: bool = Field(default=False)
    
    model_config = {
        "env_file": os.path.join(os.path.dirname(__file__), "..", ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }
    
    def get_database_url(self) -> str:
        """Get appropriate database URL"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        # Ensure SQLite directory exists
        db_path = Path(self.SQLITE_DATABASE_PATH)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        return f"sqlite:///{self.SQLITE_DATABASE_PATH}"
    
    def get_redis_url(self) -> Optional[str]:
        """Get Redis URL if configured"""
        return self.REDIS_URL
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT.lower() in ["development", "dev"]
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins list"""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    def get_temp_dir(self) -> Path:
        """Get temp directory path and ensure it exists"""
        temp_path = Path(self.TEMP_DIR)
        temp_path.mkdir(parents=True, exist_ok=True)
        return temp_path


# Global settings instance
_settings = None


def get_settings() -> Settings:
    """
    Get application settings singleton
    
    In production, loads settings from AWS Parameter Store
    In development, loads from environment variables and .env file
    """
    global _settings
    
    if _settings is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()
        
        if environment == "production":
            # Use production settings with AWS Parameter Store
            _settings = get_production_settings_with_aws()
        else:
            # Use standard settings for development
            _settings = Settings()
    
    return _settings


def get_production_settings_with_aws() -> Settings:
    """Get production settings with AWS Parameter Store integration"""
    try:
        from .aws_config import config_manager
        
        # Get configuration from AWS Parameter Store
        aws_config = config_manager.get_all_config()
        
        # Create settings instance with AWS config
        settings_data = {}
        
        # Map AWS config to settings fields
        for key, value in aws_config.items():
            if value is not None:
                settings_data[key] = value
        
        # Create settings with the loaded configuration
        _settings = Settings(**settings_data)
        
        return _settings
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not load AWS configuration, falling back to environment variables: {e}")
        
        # Fallback to regular settings
        return Settings()


def reload_settings():
    """Reload settings (useful for testing)"""
    global _settings
    _settings = None
    return get_settings()


# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    RELOAD_ON_CHANGE: bool = True
    SHOW_SQL_QUERIES: bool = True
    MOCK_AWS_SERVICES: bool = True


class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"
    RELOAD_ON_CHANGE: bool = False
    SHOW_SQL_QUERIES: bool = False
    MOCK_AWS_SERVICES: bool = False
    REQUIRE_INVITATION: bool = True


class TestingSettings(Settings):
    """Testing environment settings"""
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"
    LOG_LEVEL: str = "DEBUG"
    SQLITE_DATABASE_PATH: str = ":memory:"
    REDIS_URL: Optional[str] = None  # Use memory store for testing
    MOCK_AWS_SERVICES: bool = True


def get_environment_settings(environment: str = None) -> Settings:
    """Get settings for specific environment"""
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development")
    
    environment = environment.lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()
