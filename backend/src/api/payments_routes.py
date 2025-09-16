"""
Payments API Routes - Works with actual database structure
Provides subscription endpoints that the frontend expects
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging

# Import authentication dependencies
from ..auth.dependencies import get_current_user
from ..models.enhanced_models import User
from ..services.actual_subscription_service import ActualSubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

@router.get("/subscription/user")
async def get_user_subscription(current_user: User = Depends(get_current_user)):
    """
    Get current user's subscription status.
    This endpoint matches what the frontend expects: /api/v1/payments/subscription/user
    """
    try:
        logger.info(f"Fetching subscription status for user: {current_user.email}")
        
        # Use the user_id from the authenticated user
        user_id = getattr(current_user, 'user_id', None)
        email = getattr(current_user, 'email', None)
        
        if not user_id and not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User ID or email required"
            )
        
        # Get subscription status using actual database structure
        if user_id:
            subscription_status = await ActualSubscriptionService.get_user_subscription_status(user_id)
        else:
            subscription_status = await ActualSubscriptionService.get_user_subscription_by_email(email)
        
        # Format response to match frontend expectations
        if subscription_status.get("has_subscription"):
            response_data = {
                "subscription": {
                    "status": subscription_status.get("status", "active"),
                    "plan": {
                        "product": subscription_status.get("plan", "Pro"),
                        "amount": subscription_status.get("amount", 1900),
                        "currency": subscription_status.get("currency", "usd"),
                        "interval": subscription_status.get("interval", "month")
                    },
                    "current_period_end": subscription_status.get("current_period_end"),
                    "trial_end": subscription_status.get("trial_end"),
                    "cancel_at_period_end": False,
                    "id": f"sub_{user_id or email.split('@')[0]}"
                },
                "message": subscription_status.get("message", "Subscription found")
            }
        else:
            response_data = {
                "subscription": None,
                "message": subscription_status.get("message", "No active subscription")
            }
        
        logger.info(f"Subscription status response: {response_data}")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Error fetching subscription for user {getattr(current_user, 'email', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch subscription status: {str(e)}"
        )

@router.post("/cancel-subscription")
async def cancel_subscription(
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """
    Cancel user subscription (placeholder for now)
    """
    try:
        subscription_id = request_data.get("subscription_id")
        cancel_at_period_end = request_data.get("cancel_at_period_end", True)
        
        logger.info(f"Cancellation requested for subscription {subscription_id} by user {current_user.email}")
        
        # For now, return success (real implementation would cancel via Stripe)
        return JSONResponse(content={
            "success": True,
            "message": "Subscription cancellation processed",
            "subscription": {
                "id": subscription_id,
                "cancel_at_period_end": cancel_at_period_end,
                "status": "active"  # Would still be active until period end
            }
        })
        
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel subscription: {str(e)}"
        )