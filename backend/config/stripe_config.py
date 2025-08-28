"""
Minimal Stripe Configuration
Environment-based configuration to avoid exposing keys in code
"""

import os
from typing import Optional

class StripeConfig:
    """Simple Stripe configuration management"""
    
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
    def get_price_id() -> str:
        """Get the Pro plan price ID"""
        # Using your provided price ID for $12/month pro plan
        return "price_1S152qDkkBHtBd89SE5F7ayE"
    
    @staticmethod
    def get_product_id() -> str:
        """Get the product ID"""
        # Using your provided product ID
        return "prod_Swz08EJnc2Qksh"
