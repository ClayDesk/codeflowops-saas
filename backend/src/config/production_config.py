# Production Infrastructure Configuration
# This file defines production environment settings for Smart Deploy Platform

import os
from typing import Dict, Any, List, Optional

class ProductionConfig:
    """Production environment configuration for Smart Deploy Platform"""
    
    # Database Configuration
    DATABASE_CONFIG = {
        "provider": "postgresql",  # Change from SQLite to PostgreSQL for production
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "smartdeploy_prod"),
        "username": os.getenv("DB_USER", "smartdeploy"),
        "password": os.getenv("DB_PASSWORD"),
        "ssl_mode": "require",
        "pool_size": 20,
        "max_overflow": 30,
        "echo": False  # Set to True for SQL debugging
    }
    
    # Redis Configuration
    REDIS_CONFIG = {
        "host": os.getenv("REDIS_HOST", "localhost"),
        "port": int(os.getenv("REDIS_PORT", "6379")),
        "db": int(os.getenv("REDIS_DB", "0")),
        "password": os.getenv("REDIS_PASSWORD"),
        "ssl": os.getenv("REDIS_SSL", "false").lower() == "true",
        "decode_responses": True
    }
    
    # AWS Configuration
    AWS_CONFIG = {
        "region": os.getenv("AWS_REGION", "us-east-1"),
        "account_id": os.getenv("AWS_ACCOUNT_ID"),
        "profile": os.getenv("AWS_PROFILE"),
        "terraform_state_bucket": os.getenv("TERRAFORM_STATE_BUCKET", "smartdeploy-terraform-state"),
        "terraform_state_dynamodb_table": os.getenv("TERRAFORM_DYNAMODB_TABLE", "smartdeploy-terraform-locks")
    }
    
    # AI Configuration removed - using traditional Terraform templates
    # All AI/LLM integration has been removed from the system
    
    # Security Configuration
    SECURITY_CONFIG = {
        "jwt_secret": os.getenv("JWT_SECRET_KEY"),
        "jwt_algorithm": "HS256",
        "jwt_expiration_hours": 24,
        "cors_origins": os.getenv("CORS_ORIGINS", "*").split(","),
        "rate_limit_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
        "max_file_size_mb": int(os.getenv("MAX_FILE_SIZE_MB", "100"))
    }
    
    # Monitoring Configuration
    MONITORING_CONFIG = {
        "prometheus_enabled": os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true",
        "prometheus_port": int(os.getenv("PROMETHEUS_PORT", "9090")),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "structured_logging": True,
        "health_check_interval": int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    }
    
    # WebSocket Configuration
    WEBSOCKET_CONFIG = {
        "heartbeat_interval": int(os.getenv("WS_HEARTBEAT_INTERVAL", "30")),
        "max_connections": int(os.getenv("WS_MAX_CONNECTIONS", "1000")),
        "message_size_limit": int(os.getenv("WS_MESSAGE_SIZE_LIMIT", "1048576"))  # 1MB
    }
    
    # Production Infrastructure Defaults
    INFRASTRUCTURE_DEFAULTS = {
        "environment": "production",
        "complexity": "moderate",
        "availability_zones": 2,
        "backup_strategy": "automated",
        "monitoring_level": "standard",
        "auto_scaling": True,
        "cost_optimization": True,
        "security_level": "standard",
        "compliance_requirements": []
    }
    
    @classmethod
    def get_database_url(cls) -> str:
        """Get database connection URL"""
        config = cls.DATABASE_CONFIG
        return (
            f"postgresql://{config['username']}:{config['password']}"
            f"@{config['host']}:{config['port']}/{config['database']}"
            f"?sslmode={config['ssl_mode']}"
        )
    
    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis connection URL"""
        config = cls.REDIS_CONFIG
        protocol = "rediss" if config["ssl"] else "redis"
        auth = f":{config['password']}@" if config["password"] else ""
        return f"{protocol}://{auth}{config['host']}:{config['port']}/{config['db']}"
    
    @classmethod
    def validate_production_config(cls) -> List[str]:
        """Validate production configuration and return any issues"""
        issues = []
        
        # Check required environment variables
        required_env_vars = [
            "DB_PASSWORD",
            "JWT_SECRET_KEY",
            "AWS_ACCOUNT_ID"
        ]
        
        for var in required_env_vars:
            if not os.getenv(var):
                issues.append(f"Missing required environment variable: {var}")
        
        # Check AWS credentials
        try:
            import boto3
            boto3.client('sts').get_caller_identity()
        except Exception as e:
            issues.append(f"AWS credentials not configured: {e}")
        
        # Check database connectivity (if password provided)
        if os.getenv("DB_PASSWORD"):
            try:
                import asyncpg
                # This would be a real connection test in production
                # For now, just check if the driver is available
            except ImportError:
                issues.append("PostgreSQL driver (asyncpg) not installed")
        
        return issues
    
    @classmethod
    def get_terraform_backend_config(cls, project_name: str, environment: str) -> Dict[str, Any]:
        """Get Terraform backend configuration for remote state"""
        return {
            "backend": "s3",
            "config": {
                "bucket": cls.AWS_CONFIG["terraform_state_bucket"],
                "key": f"{project_name}/{environment}/terraform.tfstate",
                "region": cls.AWS_CONFIG["region"],
                "dynamodb_table": cls.AWS_CONFIG["terraform_state_dynamodb_table"],
                "encrypt": True
            }
        }
    
    @classmethod
    def get_production_tags(cls, project_name: str, environment: str) -> Dict[str, str]:
        """Get standard production tags for AWS resources"""
        return {
            "Project": project_name,
            "Environment": environment,
            "ManagedBy": "terraform",
            "CreatedBy": "smart-deploy-platform",
            "Owner": "smart-deploy",
            "CostCenter": "engineering",
            "Backup": "required" if environment == "production" else "optional"
        }

# Environment-specific configurations
class DevelopmentConfig(ProductionConfig):
    """Development environment overrides"""
    
    DATABASE_CONFIG = {
        **ProductionConfig.DATABASE_CONFIG,
        "provider": "sqlite",  # Use SQLite for development
        "database": "data/smartdeploy_dev.db",
        "echo": True  # Enable SQL debugging
    }
    
    INFRASTRUCTURE_DEFAULTS = {
        **ProductionConfig.INFRASTRUCTURE_DEFAULTS,
        "environment": "development",
        "complexity": "simple",
        "security_level": "basic",
        "auto_scaling": False
    }

class StagingConfig(ProductionConfig):
    """Staging environment overrides"""
    
    INFRASTRUCTURE_DEFAULTS = {
        **ProductionConfig.INFRASTRUCTURE_DEFAULTS,
        "environment": "staging",
        "complexity": "moderate",
        "security_level": "standard"
    }

# Configuration factory
def get_config(environment: Optional[str] = None):
    """Get configuration based on environment"""
    
    if environment is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "staging": StagingConfig,
        "production": ProductionConfig
    }
    
    return config_map.get(environment, DevelopmentConfig)

# Production readiness checks
def check_production_readiness() -> Dict[str, Any]:
    """Check if the system is ready for production deployment"""
    
    config = ProductionConfig()
    issues = config.validate_production_config()
    
    # Additional checks
    readiness_checks = {
        "database_configured": bool(os.getenv("DB_PASSWORD")),
        "aws_configured": bool(os.getenv("AWS_ACCOUNT_ID")),
        "security_configured": bool(os.getenv("JWT_SECRET_KEY")),
        "redis_configured": bool(os.getenv("REDIS_HOST")),
        "ssl_configured": bool(os.getenv("SSL_CERT_PATH")),
        "monitoring_configured": bool(os.getenv("PROMETHEUS_ENABLED"))
    }
    
    all_ready = all(readiness_checks.values()) and len(issues) == 0
    
    return {
        "ready": all_ready,
        "checks": readiness_checks,
        "issues": issues,
        "score": sum(readiness_checks.values()) / len(readiness_checks) * 100
    }
