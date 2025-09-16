"""
Simple Payment API Routes
Just subscription creation and webhook handling
"""

from fastapi import APIRouter, HTTPException, Request, Header, Depends
from pydantic import BaseModel
from typing import Optional
import logging
import time

# Import service with fallback paths
try:
    from ..services.stripe_service import StripeService
    from ..auth.dependencies import get_current_user
except ImportError:
    from src.services.stripe_service import StripeService
    from src.auth.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

# Request models
class CreateSubscriptionRequest(BaseModel):
    email: str
    name: Optional[str] = None
    trial_days: Optional[int] = 0

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
async def get_user_subscription(current_user = Depends(get_current_user)):
    """Get current user's subscription"""
    try:
        from ..services.subscription_service import SubscriptionService
        
        # Get user's subscription from database
        subscription_data = await SubscriptionService.get_user_subscription(current_user.id)
        
        if not subscription_data:
            # No subscription found - user is on free plan
            return {
                "success": True,
                "subscription": None,
                "plan": "free",
                "message": "No active subscription found"
            }
        
        # Format subscription data for frontend
        formatted_subscription = {
            'id': subscription_data.get('stripe_subscription_id'),
            'status': subscription_data.get('status'),
            'current_period_start': subscription_data.get('current_period_start'),
            'current_period_end': subscription_data.get('current_period_end'),
            'cancel_at_period_end': subscription_data.get('cancel_at_period_end', False),
            'trial_start': subscription_data.get('trial_start'),
            'trial_end': subscription_data.get('trial_end'),
            'plan': {
                'id': subscription_data.get('plan', 'pro'),
                'amount': subscription_data.get('amount', 0),
                'currency': subscription_data.get('currency', 'usd'),
                'interval': subscription_data.get('interval', 'month'),
                'product': f"CodeFlowOps {subscription_data.get('plan', 'Pro').title()}"
            },
            'is_active': subscription_data.get('is_active', False),
            'is_trial': subscription_data.get('is_trial', False),
            'days_until_end': subscription_data.get('days_until_end', 0)
        }
        
        return {
            "success": True,
            "subscription": formatted_subscription,
            "plan": subscription_data.get('plan', 'free')
        }
        
    except Exception as e:
        logger.error(f"Failed to get user subscription: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
