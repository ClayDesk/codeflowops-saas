"""
Simple Payment API Routes
Just subscription creation and webhook handling
"""

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
import logging

# Import service with fallback paths
try:
    from ..services.stripe_service import StripeService
except ImportError:
    from src.services.stripe_service import StripeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# Request models
class CreateSubscriptionRequest(BaseModel):
    email: str
    name: Optional[str] = None
    trial_days: Optional[int] = 14

# Initialize service
stripe_service = StripeService()

@router.post("/create-subscription")
async def create_subscription(request: CreateSubscriptionRequest):
    """Create a subscription with free trial"""
    try:
        result = await stripe_service.create_customer_and_subscription(
            email=request.email,
            name=request.name,
            trial_days=request.trial_days
        )
        
        return {
            "success": True,
            "subscription": result
        }
    except Exception as e:
        logger.error(f"Failed to create subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create-checkout-session")
async def create_checkout_session(request: CreateSubscriptionRequest):
    """Create a Stripe Checkout Session for subscription with payment collection"""
    try:
        result = await stripe_service.create_checkout_session(
            email=request.email,
            name=request.name,
            trial_days=request.trial_days
        )
        
        return {
            "success": True,
            "message": f"Subscription created with {request.trial_days} day trial",
            "subscription": result
        }
        
    except Exception as e:
        logger.error(f"Subscription creation failed: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to create subscription: {str(e)}"
        )

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        
        if not stripe_signature:
            raise HTTPException(
                status_code=400, 
                detail="Missing stripe-signature header"
            )
        
        result = await stripe_service.handle_webhook(
            payload=payload.decode('utf-8'),
            sig_header=stripe_signature
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Webhook handling failed: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Webhook error: {str(e)}"
        )

@router.get("/subscription/{subscription_id}")
async def get_subscription(subscription_id: str):
    """Get subscription status"""
    try:
        result = await stripe_service.get_subscription_status(subscription_id)
        return {
            "success": True,
            "subscription": result
        }
        
    except Exception as e:
        logger.error(f"Failed to get subscription: {str(e)}")
        raise HTTPException(
            status_code=400, 
            detail=f"Failed to get subscription: {str(e)}"
        )
