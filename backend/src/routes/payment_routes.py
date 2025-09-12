"""
Simple Payment API Routes
Just subscription creation and webhook handling
"""

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Optional
import logging
import time

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

class CancelSubscriptionRequest(BaseModel):
    subscription_id: str
    cancel_at_period_end: Optional[bool] = True

# Initialize service
stripe_service = StripeService()

@router.post("/create-subscription")
async def create_subscription(request: CreateSubscriptionRequest):
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

@router.post("/cancel-subscription")
async def cancel_subscription(request: CancelSubscriptionRequest):
    """Cancel a subscription"""
    try:
        result = await stripe_service.cancel_subscription(
            subscription_id=request.subscription_id,
            cancel_at_period_end=request.cancel_at_period_end
        )

        return {
            "success": True,
            "message": "Subscription cancelled successfully",
            "subscription": result
        }
    except Exception as e:
        logger.error(f"Failed to cancel subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

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

@router.get("/subscription/user")
async def get_user_subscription(request: Request):
    """Get current user's subscription"""
    try:
        # Get user from auth token (simplified for demo)
        # In production, you'd validate the JWT token and get user info
        auth_header = request.headers.get('authorization', '')
        if not auth_header.startswith('Bearer '):
            raise HTTPException(status_code=401, detail="Invalid authorization header")
        
        # For demo purposes, return mock subscription data
        # In production, you'd look up the user's subscription from your database
        current_time = int(time.time())
        thirty_days = 30 * 24 * 60 * 60
        
        mock_subscription = {
            'id': 'sub_demo123',
            'status': 'active',
            'current_period_start': current_time - thirty_days,  # 30 days ago
            'current_period_end': current_time + thirty_days,    # 30 days from now
            'cancel_at_period_end': False,
            'customer_id': 'cus_demo123',
            'plan': {
                'id': 'plan_pro_monthly',
                'amount': 1900,
                'currency': 'usd',
                'interval': 'month',
                'product': 'CodeFlowOps Pro'
            }
        }
        
        return {
            "success": True,
            "subscription": mock_subscription
        }
        
    except Exception as e:
        logger.error(f"Failed to get user subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
