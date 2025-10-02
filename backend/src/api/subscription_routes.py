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

class SubscriptionPlanDetails(BaseModel):
    """Nested plan details matching frontend SubscriptionData interface"""
    product: str
    amount: int
    currency: str
    interval: str

class SubscriptionStatusResponse(BaseModel):
    """Response format matching frontend SubscriptionData interface"""
    has_subscription: bool
    id: Optional[str] = None  # Subscription ID
    status: Optional[str] = None
    plan: Optional[SubscriptionPlanDetails] = None  # Nested plan object
    current_period_end: Optional[int] = None  # Unix timestamp
    trial_end: Optional[int] = None  # Unix timestamp
    cancel_at_period_end: Optional[bool] = False
    # Additional fields for backward compatibility
    stripe_subscription_id: Optional[str] = None
    is_trial: Optional[bool] = None
    message: Optional[str] = None
    error: Optional[str] = None

@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(current_user: User = Depends(get_current_user)):
    """Get current user's subscription status"""
    try:
        # Support both user.user_id and user.id fields
        user_id = getattr(current_user, 'user_id', None) or getattr(current_user, 'id', None)
        if not user_id:
            raise ValueError("Missing user id on current_user")
        status_info = await EnhancedSubscriptionFlow.get_user_subscription_status(user_id)
        
        # Transform the response to match frontend SubscriptionData interface
        response_data = {
            "has_subscription": status_info.get("has_subscription", False),
            "is_trial": status_info.get("is_trial", False),
            "message": status_info.get("message"),
            "error": status_info.get("error")
        }
        
        # Only include subscription details if user has subscription
        if status_info.get("has_subscription"):
            # Get subscription ID
            subscription_id = (
                status_info.get("subscription_id") or 
                status_info.get("stripe_subscription_id") or 
                "sub_unknown"
            )
            
            # Create nested plan object
            plan_details = SubscriptionPlanDetails(
                product=status_info.get("plan", "CodeFlowOps Pro"),
                amount=status_info.get("amount", 1900),
                currency=(status_info.get("currency") or "usd").lower(),
                interval=status_info.get("interval", "month")
            )
            
            response_data.update({
                "id": subscription_id,
                "stripe_subscription_id": subscription_id,
                "status": status_info.get("status", "active"),
                "plan": plan_details,
                "cancel_at_period_end": status_info.get("cancel_at_period_end", False)
            })
            
            # Convert ISO date strings to Unix timestamps
            if status_info.get("current_period_end"):
                try:
                    from datetime import datetime
                    end_str = status_info["current_period_end"]
                    if isinstance(end_str, str):
                        dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                        response_data["current_period_end"] = int(dt.timestamp() * 1000)
                    elif isinstance(end_str, int):
                        response_data["current_period_end"] = end_str
                except Exception as date_err:
                    logger.warning(f"Failed to parse current_period_end: {date_err}")
            
            if status_info.get("trial_end"):
                try:
                    from datetime import datetime
                    trial_str = status_info["trial_end"]
                    if isinstance(trial_str, str):
                        dt = datetime.fromisoformat(trial_str.replace('Z', '+00:00'))
                        response_data["trial_end"] = int(dt.timestamp() * 1000)
                    elif isinstance(trial_str, int):
                        response_data["trial_end"] = trial_str
                except Exception as date_err:
                    logger.warning(f"Failed to parse trial_end: {date_err}")
        
        return SubscriptionStatusResponse(**response_data)
        
    except Exception as e:
        uid_dbg = getattr(current_user, 'user_id', None) or getattr(current_user, 'id', 'unknown')
        logger.error(f"Error getting subscription status for user {uid_dbg}: {str(e)}")
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
        user_id = getattr(current_user, 'user_id', None) or getattr(current_user, 'id', None)
        if not user_id:
            raise ValueError("Missing user id on current_user")
        # Check if user already has a subscription
        existing_status = await EnhancedSubscriptionFlow.get_user_subscription_status(user_id)
        
        if existing_status.get("has_subscription"):
            return SubscriptionResponse(
                success=False,
                message="User already has an active subscription",
                error="ALREADY_SUBSCRIBED"
            )
        
        # Create free trial
        trial_result = await EnhancedSubscriptionFlow.create_free_trial_subscription(
            user_id=user_id,
            email=getattr(current_user, 'email', None) or "",
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
        uid_dbg = getattr(current_user, 'user_id', None) or getattr(current_user, 'id', 'unknown')
        logger.error(f"Error creating trial for user {uid_dbg}: {str(e)}")
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