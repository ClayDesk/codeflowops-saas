"""
Payment API Routes for Stripe Integration
Handles subscription creation, payment processing, and webhooks
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List
import logging
from ..services.stripe_payment_service import StripePaymentService
from ..services.dynamic_pricing_service import DynamicPricingService
from ..auth.cognito_rbac import get_current_user
from ..models.auth_models import User

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# Pydantic models for request/response
class CreateSubscriptionRequest(BaseModel):
    plan_tier: str
    pricing_context: Optional[Dict[str, Any]] = {}
    trial_days: Optional[int] = None

class CreatePaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "usd"
    metadata: Optional[Dict[str, Any]] = {}

class UpgradeSubscriptionRequest(BaseModel):
    subscription_id: str
    new_plan_tier: str
    pricing_context: Optional[Dict[str, Any]] = {}

class CancelSubscriptionRequest(BaseModel):
    subscription_id: str
    at_period_end: bool = True

# Initialize services
stripe_service = StripePaymentService()
dynamic_pricing = DynamicPricingService()

@router.post("/create-subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new subscription with free trial"""
    try:
        # Create or get Stripe customer
        customer_id = await stripe_service.create_customer(
            user_email=current_user.email,
            user_name=current_user.full_name,
            metadata={
                'user_id': str(current_user.id),
                'signup_date': current_user.created_at.isoformat() if current_user.created_at else None
            }
        )
        
        # Create subscription
        subscription_result = await stripe_service.create_subscription_with_trial(
            customer_id=customer_id,
            plan_tier=request.plan_tier,
            pricing_context=request.pricing_context,
            trial_days=request.trial_days
        )
        
        # TODO: Update user subscription in database
        
        return {
            "success": True,
            "subscription": subscription_result,
            "message": f"Subscription created successfully for {request.plan_tier} plan"
        }
        
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-payment-intent")
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a payment intent for one-time payments"""
    try:
        # Create or get Stripe customer
        customer_id = await stripe_service.create_customer(
            user_email=current_user.email,
            user_name=current_user.full_name,
            metadata={'user_id': str(current_user.id)}
        )
        
        payment_intent = await stripe_service.create_payment_intent(
            amount=request.amount,
            currency=request.currency,
            customer_id=customer_id,
            metadata=request.metadata
        )
        
        return {
            "success": True,
            "payment_intent": payment_intent,
            "message": "Payment intent created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating payment intent: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upgrade-subscription")
async def upgrade_subscription(
    request: UpgradeSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Upgrade or downgrade an existing subscription"""
    try:
        upgrade_result = await stripe_service.upgrade_subscription(
            subscription_id=request.subscription_id,
            new_plan_tier=request.new_plan_tier,
            pricing_context=request.pricing_context
        )
        
        # TODO: Update user subscription in database
        
        return {
            "success": True,
            "subscription": upgrade_result,
            "message": f"Subscription upgraded to {request.new_plan_tier} plan"
        }
        
    except Exception as e:
        logger.error(f"Error upgrading subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cancel-subscription")
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user)
):
    """Cancel an existing subscription"""
    try:
        cancel_result = await stripe_service.cancel_subscription(
            subscription_id=request.subscription_id,
            at_period_end=request.at_period_end
        )
        
        # TODO: Update user subscription status in database
        
        return {
            "success": True,
            "subscription": cancel_result,
            "message": "Subscription cancelled successfully"
        }
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/subscription/{subscription_id}")
async def get_subscription_details(
    subscription_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get detailed subscription information"""
    try:
        subscription_details = await stripe_service.get_subscription_details(subscription_id)
        
        return {
            "success": True,
            "subscription": subscription_details
        }
        
    except Exception as e:
        logger.error(f"Error getting subscription details: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events (snapshot payloads)"""
    try:
        payload = await request.body()
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        webhook_result = await stripe_service.handle_webhook(
            payload=payload.decode('utf-8'),
            sig_header=stripe_signature
        )
        
        return {
            "success": True,
            "result": webhook_result
        }
        
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook-thin")
async def stripe_webhook_thin(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events (thin payloads) - backup endpoint"""
    try:
        payload = await request.body()
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing stripe-signature header")
        
        # For thin payloads, we'd need to fetch the full object from Stripe
        # But for now, just log and acknowledge
        logger.info("Received thin payload webhook - acknowledging")
        
        return {
            "success": True,
            "result": {"status": "acknowledged", "payload_type": "thin"}
        }
        
    except Exception as e:
        logger.error(f"Error handling thin webhook: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pricing-with-payment-info")
async def get_pricing_with_payment_info(
    country: Optional[str] = None,
    currency: Optional[str] = None,
    referral_code: Optional[str] = None,
    company_size: Optional[str] = None,
    ab_variant: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get dynamic pricing with Stripe-specific payment information"""
    try:
        # Build context for pricing
        context = {}
        if country:
            context['country'] = country
        if currency:
            context['currency'] = currency
        if referral_code:
            context['referral_code'] = referral_code
        if company_size:
            context['company_size'] = company_size
        if ab_variant:
            context['ab_variant'] = ab_variant
        
        # Add user context if authenticated
        if current_user:
            context['user_id'] = str(current_user.id)
            context['user_email'] = current_user.email
            context['signup_date'] = current_user.created_at.isoformat() if current_user.created_at else None
        
        # Get dynamic pricing
        pricing_data = await dynamic_pricing.get_personalized_pricing(context)
        
        # Add Stripe-specific information
        for plan in pricing_data['plans']:
            if plan['tier'] != 'free':
                # Add payment information
                plan['stripe_info'] = {
                    'supports_trial': plan.get('trial_days', 0) > 0,
                    'trial_description': f"{plan.get('trial_days', 0)} days free trial" if plan.get('trial_days', 0) > 0 else None,
                    'payment_methods': ['card', 'paypal'],  # Stripe supports these
                    'currencies': ['USD', 'EUR', 'GBP'],  # Supported currencies
                    'billing_cycles': ['monthly', 'yearly'],
                    'instant_activation': True
                }
            else:
                plan['stripe_info'] = {
                    'supports_trial': False,
                    'payment_methods': [],
                    'instant_activation': True
                }
        
        return {
            "success": True,
            "pricing": pricing_data,
            "stripe_publishable_key": "pk_test_...",  # Will be set from environment
            "message": "Pricing retrieved with payment information"
        }
        
    except Exception as e:
        logger.error(f"Error getting pricing with payment info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user-subscription-status")
async def get_user_subscription_status(
    current_user: User = Depends(get_current_user)
):
    """Get current user's subscription status"""
    try:
        # TODO: Get user's current subscription from database
        # This would typically query your User/Subscription models
        
        # For now, return a mock response
        return {
            "success": True,
            "subscription": {
                "has_subscription": False,
                "plan_tier": "free",
                "status": "active",
                "trial_end": None,
                "current_period_end": None,
                "can_upgrade": True,
                "can_cancel": False
            },
            "available_actions": {
                "can_start_trial": True,
                "can_upgrade": True,
                "can_downgrade": False,
                "can_cancel": False
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
