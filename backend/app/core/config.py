"""
Configuration and Environment Setup for Enhanced Deployment Services
"""

import os
from typing import Dict, Any, Optional

# Environment Configuration
class Config:
    """
    Configuration class for deployment services
    """
    
    # Deployment Settings
    MAX_DEPLOYMENT_RETRIES: int = int(os.getenv("MAX_DEPLOYMENT_RETRIES", "3"))
    DEPLOYMENT_TIMEOUT_MINUTES: int = int(os.getenv("DEPLOYMENT_TIMEOUT_MINUTES", "30"))
    
    # URL Verification Settings
    URL_VERIFICATION_RETRIES: int = int(os.getenv("URL_VERIFICATION_RETRIES", "3"))
    URL_VERIFICATION_TIMEOUT: int = int(os.getenv("URL_VERIFICATION_TIMEOUT", "30"))
    
    # Integration Test Settings
    INTEGRATION_TEST_REPO: str = os.getenv(
        "INTEGRATION_TEST_REPO", 
        "https://github.com/vercel/next.js/tree/canary/examples/hello-world"
    )
    
    # Backend Configuration
    BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def get_deployment_config(cls) -> Dict[str, Any]:
        """Get deployment configuration"""
        return {
            "max_retries": cls.MAX_DEPLOYMENT_RETRIES,
            "timeout_minutes": cls.DEPLOYMENT_TIMEOUT_MINUTES,
            "url_verification_retries": cls.URL_VERIFICATION_RETRIES,
            "url_verification_timeout": cls.URL_VERIFICATION_TIMEOUT
        }


# Environment file template for setup
ENV_TEMPLATE = """
# Enhanced Deployment Configuration

# Deployment Settings
MAX_DEPLOYMENT_RETRIES=3
DEPLOYMENT_TIMEOUT_MINUTES=30

# URL Verification Settings
URL_VERIFICATION_RETRIES=3
URL_VERIFICATION_TIMEOUT=30

# Integration Testing
INTEGRATION_TEST_REPO=https://github.com/vercel/next.js/tree/canary/examples/hello-world
BACKEND_BASE_URL=http://localhost:8000

# Logging
LOG_LEVEL=INFO
"""


def create_env_file_if_missing():
    """
    Create .env file with template if it doesn't exist
    """
    env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    
    if not os.path.exists(env_path):
        with open(env_path, 'w') as f:
            f.write(ENV_TEMPLATE)
        print(f"Created environment file template: {env_path}")
        print("Please update with your actual configuration values")


# Initialize configuration
config = Config()

# Create env file if missing
if __name__ == "__main__":
    create_env_file_if_missing()
