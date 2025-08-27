"""
Secure Configuration Management for CodeFlowOps
Industry-standard approach for handling sensitive credentials
"""

import os
from typing import Optional

class StripeConfig:
    """Centralized Stripe configuration management"""
    
    @staticmethod
    def get_secret_key() -> str:
        """Get Stripe secret key from environment"""
        key = os.getenv('STRIPE_SECRET_KEY')
        if not key:
            raise ValueError("STRIPE_SECRET_KEY environment variable must be set")
        return key
    
    @staticmethod
    def get_webhook_secret() -> str:
        """Get Stripe webhook secret from environment"""
        secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        if not secret:
            raise ValueError("STRIPE_WEBHOOK_SECRET environment variable must be set")
        return secret
    
    @staticmethod
    def get_publishable_key() -> str:
        """Get Stripe publishable key from environment"""
        key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        if not key:
            raise ValueError("STRIPE_PUBLISHABLE_KEY environment variable must be set")
        return key
    
    @staticmethod
    def is_production() -> bool:
        """Check if running in production environment"""
        return os.getenv('ENVIRONMENT', '').lower() == 'production' or \
               os.getenv('AWS_EXECUTION_ENV') is not None
