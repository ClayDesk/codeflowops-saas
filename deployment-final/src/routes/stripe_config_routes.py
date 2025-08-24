# Stripe Configuration API Routes
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..config.stripe_config import stripe_config

router = APIRouter(prefix="/api/v1/stripe", tags=["stripe-config"])

class StripeConfigResponse(BaseModel):
    publishable_key: str
    is_test_mode: bool

@router.get("/config", response_model=StripeConfigResponse)
async def get_stripe_config():
    """
    Get Stripe configuration for frontend
    Returns publishable key and test mode status
    """
    if not stripe_config.validate_config():
        raise HTTPException(
            status_code=500, 
            detail="Stripe configuration is not properly set up"
        )
    
    publishable_key = stripe_config.get_publishable_key()
    if not publishable_key:
        raise HTTPException(
            status_code=500,
            detail="Stripe publishable key not configured"
        )
    
    return StripeConfigResponse(
        publishable_key=publishable_key,
        is_test_mode=stripe_config.is_test_mode()
    )
