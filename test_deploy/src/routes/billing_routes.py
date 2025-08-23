# Billing and Subscription Management Routes for CodeFlowOps
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime
import json

from ..models.billing_models import (
    BillingPlan, OrganizationSubscription, Invoice, Payment,
    PlanTier, SubscriptionStatus, PLAN_CONFIGS
)
from ..models.enhanced_models import Organization, User
from ..utils.stripe_service import stripe_service
from ..utils.database import get_db_session
from auth.cognito_rbac import verify_token, get_current_user

router = APIRouter(prefix="/billing", tags=["billing"])
security = HTTPBearer()

@router.get("/plans")
async def get_billing_plans(db: Session = Depends(get_db_session)):
    """
    Get all available billing plans
    """
    plans = db.query(BillingPlan).filter(BillingPlan.is_active == True).all()
    
    # If no plans in database, return default configurations
    if not plans:
        return [
            {
                "id": config["id"],
                "name": config["name"],
                "tier": config["tier"].value,
                "price_monthly": config["price_monthly"],
                "price_yearly": config["price_yearly"],
                "max_projects": config["max_projects"],
                "max_minutes_per_month": config["max_minutes_per_month"],
                "max_team_members": config["max_team_members"],
                "max_concurrent_deployments": config["max_concurrent_deployments"],
                "features": json.loads(config["features_json"]),
                "description": config["description"],
                "custom_domains": config["custom_domains"],
                "priority_support": config["priority_support"],
                "advanced_analytics": config["advanced_analytics"],
                "sso_integration": config["sso_integration"],
                "api_access": config["api_access"]
            }
            for config in PLAN_CONFIGS.values()
        ]
    
    return [
        {
            "id": plan.id,
            "name": plan.name,
            "tier": plan.tier.value,
            "price_monthly": plan.price_monthly,
            "price_yearly": plan.price_yearly,
            "max_projects": plan.max_projects,
            "max_minutes_per_month": plan.max_minutes_per_month,
            "max_team_members": plan.max_team_members,
            "max_concurrent_deployments": plan.max_concurrent_deployments,
            "features": json.loads(plan.features_json) if plan.features_json else [],
            "description": plan.description,
            "custom_domains": plan.custom_domains,
            "priority_support": plan.priority_support,
            "advanced_analytics": plan.advanced_analytics,
            "sso_integration": plan.sso_integration,
            "api_access": plan.api_access,
            "stripe_price_id": plan.stripe_price_id
        }
        for plan in plans
    ]

@router.get("/subscription")
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get current user's organization subscription details
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization")
    
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == current_user.organization_id,
        OrganizationSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
    ).first()
    
    if not subscription:
        # Return free plan info
        free_config = PLAN_CONFIGS[PlanTier.FREE]
        return {
            "plan": {
                "name": free_config["name"],
                "tier": free_config["tier"].value,
                "max_projects": free_config["max_projects"],
                "max_minutes_per_month": free_config["max_minutes_per_month"],
                "max_team_members": free_config["max_team_members"],
                "features": json.loads(free_config["features_json"])
            },
            "status": "active",
            "current_period_end": None,
            "cancel_at_period_end": False,
            "usage": {
                "minutes_used": 0,
                "projects_count": 0,
                "team_members_count": 1
            }
        }
    
    # Get usage summary
    usage_summary = await stripe_service.get_usage_summary(db, current_user.organization_id)
    
    return {
        "id": subscription.id,
        "plan": {
            "name": subscription.plan.name,
            "tier": subscription.plan.tier.value,
            "max_projects": subscription.plan.max_projects,
            "max_minutes_per_month": subscription.plan.max_minutes_per_month,
            "max_team_members": subscription.plan.max_team_members,
            "features": json.loads(subscription.plan.features_json) if subscription.plan.features_json else []
        },
        "status": subscription.status.value,
        "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
        "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
        "cancel_at_period_end": subscription.cancel_at_period_end,
        "next_billing_date": subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
        "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None,
        "usage": usage_summary
    }

@router.post("/subscribe/{plan_tier}")
async def create_subscription(
    plan_tier: str,
    payment_method_id: str,
    trial_days: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Create a new subscription for the user's organization
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization")
    
    # Check if organization already has an active subscription
    existing_subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == current_user.organization_id,
        OrganizationSubscription.status.in_([
            SubscriptionStatus.ACTIVE, 
            SubscriptionStatus.TRIALING,
            SubscriptionStatus.PAST_DUE
        ])
    ).first()
    
    if existing_subscription:
        raise HTTPException(status_code=400, detail="Organization already has an active subscription")
    
    # Validate plan tier
    try:
        plan_tier_enum = PlanTier(plan_tier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan tier")
    
    if plan_tier_enum == PlanTier.FREE:
        raise HTTPException(status_code=400, detail="Cannot create subscription for free plan")
    
    if plan_tier_enum == PlanTier.ENTERPRISE:
        raise HTTPException(status_code=400, detail="Please contact support@codeflowops.com for Enterprise plans")
    
    # Create subscription
    subscription = await stripe_service.create_subscription(
        db=db,
        organization_id=current_user.organization_id,
        plan_tier=plan_tier_enum,
        payment_method_id=payment_method_id,
        trial_days=trial_days
    )
    
    return {
        "subscription_id": subscription.id,
        "status": subscription.status.value,
        "plan": subscription.plan.name,
        "current_period_end": subscription.current_period_end.isoformat(),
        "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None
    }

@router.post("/subscription/change-plan/{new_plan_tier}")
async def change_subscription_plan(
    new_plan_tier: str,
    prorate: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Change the subscription plan
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization")
    
    # Get current subscription
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == current_user.organization_id,
        OrganizationSubscription.status == SubscriptionStatus.ACTIVE
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    # Validate new plan tier
    try:
        new_plan_tier_enum = PlanTier(new_plan_tier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan tier")
    
    if new_plan_tier_enum == PlanTier.FREE:
        # Downgrade to free means canceling subscription
        updated_subscription = await stripe_service.cancel_subscription(
            db=db,
            subscription_id=subscription.id,
            immediate=False
        )
        return {
            "message": "Subscription will be canceled at the end of current period",
            "cancel_at_period_end": updated_subscription.cancel_at_period_end,
            "current_period_end": updated_subscription.current_period_end.isoformat()
        }
    
    if new_plan_tier_enum == PlanTier.ENTERPRISE:
        raise HTTPException(status_code=400, detail="Please contact support@codeflowops.com for Enterprise plans")
    
    # Change plan
    updated_subscription = await stripe_service.change_plan(
        db=db,
        subscription_id=subscription.id,
        new_plan_tier=new_plan_tier_enum,
        prorate=prorate
    )
    
    return {
        "subscription_id": updated_subscription.id,
        "new_plan": updated_subscription.plan.name,
        "status": updated_subscription.status.value,
        "current_period_end": updated_subscription.current_period_end.isoformat()
    }

@router.post("/subscription/cancel")
async def cancel_subscription(
    immediate: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Cancel the current subscription
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization")
    
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == current_user.organization_id,
        OrganizationSubscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    updated_subscription = await stripe_service.cancel_subscription(
        db=db,
        subscription_id=subscription.id,
        immediate=immediate
    )
    
    if immediate:
        return {
            "message": "Subscription canceled immediately",
            "status": updated_subscription.status.value,
            "canceled_at": updated_subscription.canceled_at.isoformat()
        }
    else:
        return {
            "message": "Subscription will be canceled at the end of current period",
            "cancel_at_period_end": updated_subscription.cancel_at_period_end,
            "current_period_end": updated_subscription.current_period_end.isoformat()
        }

@router.get("/usage")
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get detailed usage summary for the current billing period
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization")
    
    usage_summary = await stripe_service.get_usage_summary(db, current_user.organization_id)
    return usage_summary

@router.get("/invoices")
async def get_invoices(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get organization's billing invoices
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization")
    
    # Get subscription
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == current_user.organization_id
    ).first()
    
    if not subscription:
        return {"invoices": []}
    
    # Get invoices
    invoices = db.query(Invoice).filter(
        Invoice.subscription_id == subscription.id
    ).order_by(Invoice.created_at.desc()).limit(limit).all()
    
    return {
        "invoices": [
            {
                "id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "amount_paid": invoice.amount_paid,
                "amount_due": invoice.amount_due,
                "currency": "usd",
                "status": invoice.status,
                "paid": invoice.paid,
                "period_start": invoice.period_start.isoformat() if invoice.period_start else None,
                "period_end": invoice.period_end.isoformat() if invoice.period_end else None,
                "due_date": invoice.due_date.isoformat() if invoice.due_date else None,
                "created_at": invoice.created_at.isoformat(),
                "invoice_pdf": invoice.invoice_pdf,
                "hosted_invoice_url": invoice.hosted_invoice_url
            }
            for invoice in invoices
        ]
    }

@router.get("/payment-methods")
async def get_payment_methods(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Get organization's payment methods from Stripe
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization")
    
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == current_user.organization_id
    ).first()
    
    if not subscription or not subscription.stripe_customer_id:
        return {"payment_methods": []}
    
    try:
        # Get payment methods from Stripe
        payment_methods = stripe_service.stripe.PaymentMethod.list(
            customer=subscription.stripe_customer_id,
            type="card"
        )
        
        return {
            "payment_methods": [
                {
                    "id": pm.id,
                    "type": pm.type,
                    "card": {
                        "brand": pm.card.brand,
                        "last4": pm.card.last4,
                        "exp_month": pm.card.exp_month,
                        "exp_year": pm.card.exp_year
                    }
                }
                for pm in payment_methods.data
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to retrieve payment methods: {str(e)}")

@router.post("/payment-methods")
async def add_payment_method(
    payment_method_id: str,
    set_as_default: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Add a new payment method
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization")
    
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.organization_id == current_user.organization_id
    ).first()
    
    if not subscription or not subscription.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No subscription found")
    
    try:
        # Attach payment method to customer
        stripe_service.stripe.PaymentMethod.attach(
            payment_method_id,
            customer=subscription.stripe_customer_id
        )
        
        # Set as default if requested
        if set_as_default:
            stripe_service.stripe.Customer.modify(
                subscription.stripe_customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
            
            # Update subscription record
            subscription.stripe_payment_method_id = payment_method_id
            db.commit()
        
        return {"message": "Payment method added successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to add payment method: {str(e)}")

@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: Session = Depends(get_db_session)):
    """
    Handle Stripe webhook events
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature")
    
    await stripe_service.handle_webhook(payload.decode(), signature, db)
    
    return {"status": "success"}

@router.post("/enterprise-inquiry")
async def enterprise_inquiry(
    company_name: str,
    contact_email: str,
    contact_name: str,
    team_size: int,
    requirements: str,
    current_user: User = Depends(get_current_user)
):
    """
    Submit enterprise plan inquiry
    """
    # In a real implementation, this would:
    # 1. Send email to sales team
    # 2. Create a lead in CRM
    # 3. Trigger follow-up workflows
    
    # For now, just return success
    return {
        "message": "Enterprise inquiry submitted successfully",
        "next_steps": "Our sales team will contact you within 24 hours at the provided email address",
        "contact_email": "support@codeflowops.com"
    }

@router.get("/limits-check/{resource_type}")
async def check_resource_limits(
    resource_type: str,  # projects, minutes, team_members, concurrent_deployments
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session)
):
    """
    Check if organization is within resource limits
    """
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User not associated with an organization")
    
    organization = db.query(Organization).filter(Organization.id == current_user.organization_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get current usage (this would need to be implemented based on actual usage tracking)
    current_usage = 0  # Placeholder
    
    # Check limits
    within_limits = organization.is_within_limits(resource_type, current_usage)
    
    # Get current plan details
    usage_summary = await stripe_service.get_usage_summary(db, current_user.organization_id)
    
    return {
        "resource_type": resource_type,
        "within_limits": within_limits,
        "current_usage": current_usage,
        "plan_details": usage_summary
    }
