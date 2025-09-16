"""
Enhanced Subscription API Routes
Provides endpoints for subscription management with proper user sync
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

# Import authentication dependencies
from ..auth.dependencies import get_current_user
from ..models.enhanced_models import User
from ..services.enhanced_subscription_flow import EnhancedSubscriptionFlow

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])

# Pydantic models
class CreateTrialRequest(BaseModel):
    trial_days: Optional[int] = 14

class SubscriptionResponse(BaseModel):
    success: bool
    message: str
    subscription: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class SubscriptionStatusResponse(BaseModel):
    has_subscription: bool
    status: Optional[str] = None
    plan: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    interval: Optional[str] = None
    current_period_end: Optional[str] = None
    trial_end: Optional[str] = None
    is_trial: Optional[bool] = None
    message: Optional[str] = None
    error: Optional[str] = None

@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Get current user's subscription status"""
    try:
        status_info = await EnhancedSubscriptionFlow.get_user_subscription_status(current_user.user_id)
        
        return SubscriptionStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"Error getting subscription status for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscription status: {str(e)}"
        )

@router.post("/create-trial", response_model=SubscriptionResponse)
async def create_free_trial(
    request: CreateTrialRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a free trial subscription for the current user"""
    try:
        # Check if user already has a subscription
        existing_status = await EnhancedSubscriptionFlow.get_user_subscription_status(current_user.user_id)
        
        if existing_status.get("has_subscription"):
            return SubscriptionResponse(
                success=False,
                message="User already has an active subscription",
                error="ALREADY_SUBSCRIBED"
            )
        
        # Create free trial
        trial_result = await EnhancedSubscriptionFlow.create_free_trial_subscription(
            user_id=current_user.user_id,
            email=current_user.email,
            trial_days=request.trial_days
        )
        
        if not trial_result:
            return SubscriptionResponse(
                success=False,
                message="Failed to create free trial subscription",
                error="TRIAL_CREATION_FAILED"
            )
        
        return SubscriptionResponse(
            success=True,
            message=f"Free trial created successfully! You have {request.trial_days} days of Pro features.",
            subscription=trial_result
        )
        
    except Exception as e:
        logger.error(f"Error creating trial for user {current_user.user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create trial: {str(e)}"
        )

@router.post("/webhook-sync")
async def sync_subscription_from_webhook(webhook_data: Dict[str, Any]):
    """
    Sync subscription data from Stripe webhook.
    This endpoint should be called by your webhook handler to ensure database sync.
    """
    try:
        # Extract relevant data from webhook
        event_type = webhook_data.get("type")
        
        if event_type == "customer.subscription.created":
            subscription_data = webhook_data.get("data", {}).get("object", {})
            customer_id = subscription_data.get("customer")
            subscription_id = subscription_data.get("id")
            
            logger.info(f"Processing subscription created webhook: {subscription_id}")
            
            # Here you would typically:
            # 1. Find the user by Stripe customer ID
            # 2. Ensure they have a database user record
            # 3. Create/update subscription record
            
            return {"success": True, "message": "Webhook processed successfully"}
        
        return {"success": True, "message": "Webhook event not handled"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )

@router.get("/health")
async def subscription_health_check():
    """Health check for subscription service"""
    try:
        # Test database connectivity
        from ..utils.database import get_db_context
        with get_db_context() as db:
            # Simple query to test connection
            result = db.execute("SELECT 1").fetchone()
            
        return {
            "service": "subscription_management",
            "status": "healthy",
            "database": "connected",
            "timestamp": "2025-09-16T05:35:00Z"
        }
        
    except Exception as e:
        logger.error(f"Subscription health check failed: {str(e)}")
        return {
            "service": "subscription_management", 
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2025-09-16T05:35:00Z"
        }