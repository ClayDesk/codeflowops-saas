"""
Minimal Stripe Configuration with AWS Parameter Store Support
Environment-based configuration with Parameter Store fallback
"""

import os
import boto3
from typing import Optional

class StripeConfig:
    """Stripe configuration management with AWS Parameter Store fallback"""
    
    @staticmethod
    def _get_parameter(name: str, secure: bool = True) -> Optional[str]:
        """Get parameter from AWS Parameter Store"""
        try:
            ssm = boto3.client('ssm', region_name='us-east-1')
            response = ssm.get_parameter(Name=name, WithDecryption=secure)
            return response['Parameter']['Value']
        except Exception as e:
            print(f"Warning: Could not fetch {name} from Parameter Store: {e}")
            return None
    
    @staticmethod
    def get_secret_key() -> str:
        """Get Stripe secret key from environment or Parameter Store"""
        # Try environment first
        key = os.getenv('STRIPE_SECRET_KEY')
        if key:
            return key
        
        # Fallback to Parameter Store
        try:
            key = StripeConfig._get_parameter("/codeflowops/stripe/secret_key", secure=True)
            if key:
                return key
        except Exception as e:
            print(f"Parameter Store fallback failed: {e}")
            
        # Final hardcoded fallback for production
        return "sk_live_Sbqrh9FiTBt2SB7qeG7kgxao"
    
    @staticmethod
    def get_webhook_secret() -> Optional[str]:
        """Get Stripe webhook secret from environment or Parameter Store"""
        # Try environment first
        secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        if secret:
            return secret
        
        # Fallback to Parameter Store
        try:
            secret = StripeConfig._get_parameter("/codeflowops/stripe/webhook_secret", secure=True)
            if secret:
                return secret
        except Exception as e:
            print(f"Parameter Store webhook secret fallback failed: {e}")
            
        # Final hardcoded fallback for production
        return "whsec_kRwwP44Te63bB6lODfYkZiiOmz3VCiuw"
    
    @staticmethod
    def get_publishable_key() -> str:
        """Get Stripe publishable key from environment"""
        key = os.getenv('STRIPE_PUBLISHABLE_KEY')
        if not key:
            raise ValueError("STRIPE_PUBLISHABLE_KEY environment variable must be set")
        return key
    
    @staticmethod
    def get_price_id() -> str:
        """Get Stripe price ID for Pro plan"""
        # Try environment first
        price_id = os.getenv('STRIPE_PRICE_ID_PRO')
        if price_id:
            return price_id
        
        # Fallback to Parameter Store
        price_id = StripeConfig._get_parameter("/codeflowops/stripe/price_id_pro", secure=False)
        if price_id:
            return price_id
            
        return "price_1S152qDkkBHtBd89SE5F7ayE"  # Hardcoded fallback
    
    @staticmethod
    def get_product_id() -> str:
        """Get Stripe product ID for Pro plan"""
        # Try environment first
        product_id = os.getenv('STRIPE_PRODUCT_ID_PRO')
        if product_id:
            return product_id
        
        # Fallback to Parameter Store
        product_id = StripeConfig._get_parameter("/codeflowops/stripe/product_id_pro", secure=False)
        if product_id:
            return product_id
            
        return "prod_Swz08EJnc2Qksh"  # Hardcoded fallback
