# Stripe Configuration for CodeFlowOps
import os
from typing import Optional

class StripeConfig:
    """
    Stripe configuration management
    """
    
    @staticmethod
    def get_publishable_key() -> Optional[str]:
        """Get Stripe publishable key for frontend use"""
        return os.getenv("STRIPE_PUBLISHABLE_KEY")
    
    @staticmethod
    def get_secret_key() -> Optional[str]:
        """Get Stripe secret key for backend use"""
        return os.getenv("STRIPE_SECRET_KEY")
    
    @staticmethod
    def get_webhook_secret() -> Optional[str]:
        """Get Stripe webhook secret"""
        return os.getenv("STRIPE_WEBHOOK_SECRET")
    
    @staticmethod
    def get_price_ids() -> dict:
        """Get Stripe price IDs for different plans"""
        return {
            "starter": os.getenv("STRIPE_PRICE_ID_STARTER"),
            "pro": os.getenv("STRIPE_PRICE_ID_PRO"),
            "enterprise": os.getenv("STRIPE_PRICE_ID_ENTERPRISE")
        }
    
    @staticmethod
    def is_test_mode() -> bool:
        """Check if we're in test mode based on keys"""
        secret_key = StripeConfig.get_secret_key()
        return secret_key is not None and secret_key.startswith("sk_test_")
    
    @staticmethod
    def validate_config() -> bool:
        """Validate that required Stripe configuration is present"""
        required_keys = [
            StripeConfig.get_publishable_key(),
            StripeConfig.get_secret_key()
        ]
        return all(key is not None and key.strip() != "" for key in required_keys)

# Global configuration instance
stripe_config = StripeConfig()
