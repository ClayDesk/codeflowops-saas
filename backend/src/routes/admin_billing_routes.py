# Admin Routes with Billing Management for CodeFlowOps
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

from ..models.billing_models import (
    OrganizationSubscription, BillingPlan, Invoice, Payment,
    SubscriptionStatus, PaymentStatus, PlanTier
)
from ..models.enhanced_models import Organization, User, Project, DeploymentHistory
from ..utils.database import get_db_session
from ..utils.stripe_service import stripe_service
from auth.cognito_rbac import verify_admin_access, get_current_user

router = APIRouter(prefix="/admin/billing", tags=["admin-billing"])

@router.get("/revenue-overview")
async def get_revenue_overview(
    admin_user: User = Depends(verify_admin_access),
    db: Session = Depends(get_db_session)
):
    """
    Get revenue overview for admin dashboard
    """
    current_month = datetime.utcnow().replace(day=1)
    last_month = (current_month - timedelta(days=1)).replace(day=1)
    
    # Get active subscriptions
    active_subscriptions = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.status == SubscriptionStatus.ACTIVE
    ).all()
    
    # Calculate Monthly Recurring Revenue (MRR)
    monthly_revenue = sum(
        sub.plan.price_monthly for sub in active_subscriptions
        if sub.plan.price_monthly > 0
    ) / 100  # Convert from cents to dollars
    
    # Calculate Annual Revenue (ARR)
    annual_revenue = monthly_revenue * 12
    
    # Get plan distribution
    plan_distribution = {}
    for sub in active_subscriptions:
        tier = sub.plan.tier.value
        if tier not in plan_distribution:
            plan_distribution[tier] = {
                "count": 0,
                "revenue": 0
            }
        plan_distribution[tier]["count"] += 1
        plan_distribution[tier]["revenue"] += sub.plan.price_monthly / 100
    
    # Calculate churn rate (simplified - would need more sophisticated calculation)
    total_subscriptions = db.query(OrganizationSubscription).count()
    canceled_this_month = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.status == SubscriptionStatus.CANCELED,
        OrganizationSubscription.canceled_at >= current_month
    ).count()
    
    churn_rate = (canceled_this_month / total_subscriptions * 100) if total_subscriptions > 0 else 0
    
    # Recent revenue trends (last 12 months)
    revenue_trends = []
    for i in range(12):
        month_start = current_month - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        
        month_payments = db.query(Payment).filter(
            Payment.status == PaymentStatus.SUCCEEDED,
            Payment.created_at >= month_start,
            Payment.created_at < month_end
        ).all()
        
        month_revenue = sum(payment.amount for payment in month_payments) / 100
        
        revenue_trends.append({
            "month": month_start.strftime("%Y-%m"),
            "revenue": month_revenue,
            "payments_count": len(month_payments)
        })
    
    return {
        "monthly_revenue": monthly_revenue,
        "annual_revenue": annual_revenue,
        "active_subscriptions": len(active_subscriptions),
        "churn_rate": round(churn_rate, 2),
        "plan_distribution": [
            {
                "tier": tier,
                "count": data["count"],
                "revenue": data["revenue"]
            }
            for tier, data in plan_distribution.items()
        ],
        "revenue_trends": list(reversed(revenue_trends))  # Most recent first
    }

@router.get("/subscriptions")
async def get_subscriptions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    plan_tier: Optional[str] = None,
    admin_user: User = Depends(verify_admin_access),
    db: Session = Depends(get_db_session)
):
    """
    Get paginated list of subscriptions with filtering
    """
    query = db.query(OrganizationSubscription)
    
    # Apply filters
    if status:
        try:
            status_enum = SubscriptionStatus(status)
            query = query.filter(OrganizationSubscription.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")
    
    if plan_tier:
        query = query.join(BillingPlan).filter(BillingPlan.tier == plan_tier)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * limit
    subscriptions = query.offset(offset).limit(limit).all()
    
    return {
        "subscriptions": [
            {
                "id": sub.id,
                "organization": {
                    "id": sub.organization_id,
                    "name": sub.organization.name if sub.organization else "Unknown",
                    "admin_email": sub.organization.admin_email if sub.organization else "Unknown"
                },
                "plan": {
                    "name": sub.plan.name,
                    "tier": sub.plan.tier.value,
                    "price_monthly": sub.plan.price_monthly
                },
                "status": sub.status.value,
                "current_period_start": sub.current_period_start.isoformat() if sub.current_period_start else None,
                "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
                "next_billing_date": sub.next_billing_date.isoformat() if sub.next_billing_date else None,
                "cancel_at_period_end": sub.cancel_at_period_end,
                "trial_end": sub.trial_end.isoformat() if sub.trial_end else None,
                "usage": {
                    "minutes_used": sub.current_month_minutes_used,
                    "projects_count": sub.current_month_projects_count
                }
            }
            for sub in subscriptions
        ],
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "pages": (total + limit - 1) // limit
        }
    }

@router.post("/subscriptions/{subscription_id}/update")
async def update_subscription(
    subscription_id: str,
    new_plan_tier: str,
    reason: str,
    admin_user: User = Depends(verify_admin_access),
    db: Session = Depends(get_db_session)
):
    """
    Admin override to change subscription plan
    """
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    try:
        new_plan_tier_enum = PlanTier(new_plan_tier)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid plan tier")
    
    # Use Stripe service to change plan
    updated_subscription = await stripe_service.change_plan(
        db=db,
        subscription_id=subscription_id,
        new_plan_tier=new_plan_tier_enum,
        prorate=False  # Admin overrides usually don't prorate
    )
    
    # Log admin action
    # TODO: Add audit logging for admin actions
    
    return {
        "message": f"Subscription updated to {new_plan_tier}",
        "subscription_id": updated_subscription.id,
        "new_plan": updated_subscription.plan.name,
        "reason": reason,
        "updated_by": admin_user.email
    }

@router.post("/subscriptions/{subscription_id}/extend-trial")
async def extend_trial(
    subscription_id: str,
    days: int,
    reason: str,
    admin_user: User = Depends(verify_admin_access),
    db: Session = Depends(get_db_session)
):
    """
    Extend trial period for a subscription
    """
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Extend trial in Stripe
    try:
        stripe_service.stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            trial_end=int((datetime.utcnow() + timedelta(days=days)).timestamp())
        )
        
        # Update local record
        subscription.trial_end = datetime.utcnow() + timedelta(days=days)
        db.commit()
        
        return {
            "message": f"Trial extended by {days} days",
            "new_trial_end": subscription.trial_end.isoformat(),
            "reason": reason,
            "updated_by": admin_user.email
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to extend trial: {str(e)}")

@router.get("/failed-payments")
async def get_failed_payments(
    limit: int = Query(50, ge=1, le=100),
    admin_user: User = Depends(verify_admin_access),
    db: Session = Depends(get_db_session)
):
    """
    Get recent failed payments for admin review
    """
    failed_payments = db.query(Payment).filter(
        Payment.status == PaymentStatus.FAILED
    ).order_by(Payment.created_at.desc()).limit(limit).all()
    
    return {
        "payments": [
            {
                "id": payment.id,
                "organization": {
                    "id": payment.subscription.organization_id,
                    "name": payment.subscription.organization.name if payment.subscription.organization else "Unknown",
                    "admin_email": payment.subscription.organization.admin_email if payment.subscription.organization else "Unknown"
                },
                "amount": payment.amount,
                "currency": payment.currency,
                "failure_reason": payment.failure_reason,
                "created_at": payment.created_at.isoformat(),
                "stripe_payment_intent_id": payment.stripe_payment_intent_id
            }
            for payment in failed_payments
        ]
    }

@router.post("/payments/{payment_id}/retry")
async def retry_payment(
    payment_id: str,
    admin_user: User = Depends(verify_admin_access),
    db: Session = Depends(get_db_session)
):
    """
    Retry a failed payment
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.status != PaymentStatus.FAILED:
        raise HTTPException(status_code=400, detail="Payment is not in failed status")
    
    try:
        # Retry payment in Stripe
        if payment.stripe_payment_intent_id:
            stripe_service.stripe.PaymentIntent.confirm(
                payment.stripe_payment_intent_id
            )
        
        return {
            "message": "Payment retry initiated",
            "payment_id": payment_id,
            "retried_by": admin_user.email
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to retry payment: {str(e)}")

@router.get("/analytics/usage")
async def get_usage_analytics(
    days: int = Query(30, ge=1, le=365),
    admin_user: User = Depends(verify_admin_access),
    db: Session = Depends(get_db_session)
):
    """
    Get usage analytics across all organizations
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all active subscriptions
    subscriptions = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.status == SubscriptionStatus.ACTIVE
    ).all()
    
    # Calculate total usage
    total_minutes_used = sum(sub.current_month_minutes_used for sub in subscriptions)
    total_projects = sum(sub.current_month_projects_count for sub in subscriptions)
    
    # Usage by plan
    usage_by_plan = {}
    for sub in subscriptions:
        tier = sub.plan.tier.value
        if tier not in usage_by_plan:
            usage_by_plan[tier] = {
                "customers": 0,
                "minutes_used": 0,
                "projects": 0,
                "revenue": 0
            }
        
        usage_by_plan[tier]["customers"] += 1
        usage_by_plan[tier]["minutes_used"] += sub.current_month_minutes_used
        usage_by_plan[tier]["projects"] += sub.current_month_projects_count
        usage_by_plan[tier]["revenue"] += sub.plan.price_monthly / 100
    
    # Top users by usage
    top_users = sorted(
        [
            {
                "organization_name": sub.organization.name if sub.organization else "Unknown",
                "plan": sub.plan.name,
                "minutes_used": sub.current_month_minutes_used,
                "projects_count": sub.current_month_projects_count
            }
            for sub in subscriptions
        ],
        key=lambda x: x["minutes_used"],
        reverse=True
    )[:10]
    
    return {
        "period_days": days,
        "total_metrics": {
            "total_minutes_used": total_minutes_used,
            "total_projects": total_projects,
            "active_customers": len(subscriptions)
        },
        "usage_by_plan": [
            {
                "plan": plan,
                **metrics
            }
            for plan, metrics in usage_by_plan.items()
        ],
        "top_users": top_users
    }

@router.post("/discounts/apply")
async def apply_discount(
    subscription_id: str,
    discount_percent: int,
    duration_months: int,
    reason: str,
    admin_user: User = Depends(verify_admin_access),
    db: Session = Depends(get_db_session)
):
    """
    Apply a discount to a subscription
    """
    subscription = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.id == subscription_id
    ).first()
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    try:
        # Create discount coupon in Stripe
        coupon = stripe_service.stripe.Coupon.create(
            percent_off=discount_percent,
            duration="repeating",
            duration_in_months=duration_months,
            metadata={
                "created_by": admin_user.email,
                "reason": reason,
                "subscription_id": subscription_id
            }
        )
        
        # Apply coupon to subscription
        stripe_service.stripe.Subscription.modify(
            subscription.stripe_subscription_id,
            coupon=coupon.id
        )
        
        return {
            "message": f"Applied {discount_percent}% discount for {duration_months} months",
            "coupon_id": coupon.id,
            "reason": reason,
            "applied_by": admin_user.email
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to apply discount: {str(e)}")

@router.get("/customers/at-risk")
async def get_at_risk_customers(
    admin_user: User = Depends(verify_admin_access),
    db: Session = Depends(get_db_session)
):
    """
    Get customers at risk of churning
    """
    # Customers with failed payments in last 30 days
    recent_failures = db.query(Payment).filter(
        Payment.status == PaymentStatus.FAILED,
        Payment.created_at >= datetime.utcnow() - timedelta(days=30)
    ).all()
    
    # Customers approaching usage limits
    high_usage_subscriptions = db.query(OrganizationSubscription).filter(
        OrganizationSubscription.status == SubscriptionStatus.ACTIVE
    ).all()
    
    at_risk_customers = []
    
    # Add customers with failed payments
    for payment in recent_failures:
        if payment.subscription:
            at_risk_customers.append({
                "organization_id": payment.subscription.organization_id,
                "organization_name": payment.subscription.organization.name if payment.subscription.organization else "Unknown",
                "risk_type": "payment_failed",
                "risk_score": 8,  # High risk
                "details": f"Payment failed: {payment.failure_reason}",
                "last_activity": payment.created_at.isoformat()
            })
    
    # Add customers near usage limits
    for sub in high_usage_subscriptions:
        if sub.plan.max_minutes_per_month > 0:  # Not unlimited
            usage_percent = (sub.current_month_minutes_used / sub.plan.max_minutes_per_month) * 100
            if usage_percent >= 90:
                at_risk_customers.append({
                    "organization_id": sub.organization_id,
                    "organization_name": sub.organization.name if sub.organization else "Unknown",
                    "risk_type": "usage_limit",
                    "risk_score": 6,  # Medium risk
                    "details": f"Using {usage_percent:.1f}% of monthly minutes",
                    "last_activity": datetime.utcnow().isoformat()
                })
    
    # Remove duplicates and sort by risk score
    unique_customers = {}
    for customer in at_risk_customers:
        org_id = customer["organization_id"]
        if org_id not in unique_customers or customer["risk_score"] > unique_customers[org_id]["risk_score"]:
            unique_customers[org_id] = customer
    
    sorted_customers = sorted(unique_customers.values(), key=lambda x: x["risk_score"], reverse=True)
    
    return {
        "at_risk_customers": sorted_customers,
        "total_count": len(sorted_customers)
    }
