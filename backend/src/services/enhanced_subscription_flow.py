"""
Enhanced Subscription Flow - Ensures proper user->customer->subscription sync
Handles both free trial and paid subscription scenarios
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from ..utils.database import get_db_context
from ..models.enhanced_models import User, Customer, Subscription, SubscriptionPlan, SubscriptionStatus
from ..services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

class EnhancedSubscriptionFlow:
    """Enhanced subscription flow that ensures proper user sync"""
    
    @staticmethod
    async def ensure_customer_record(user_id: str, email: str, name: Optional[str] = None) -> Optional[Customer]:
        """
        Ensure user has a customer record before subscription operations.
        Creates customer record if it doesn't exist.
        
        Args:
            user_id: Database user ID
            email: User email
            name: User name (optional)
            
        Returns:
            Customer: The customer record
        """
        try:
            with get_db_context() as db:
                # Check if customer already exists
                existing_customer = db.query(Customer).filter(
                    Customer.user_id == user_id
                ).first()
                
                if existing_customer:
                    logger.debug(f"Customer record already exists for user {user_id}")
                    return existing_customer
                
                # Create new customer record (without Stripe customer yet)
                logger.info(f"Creating customer record for user {user_id}")
                
                customer = Customer(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    stripe_customer_id="",  # Will be updated when Stripe customer is created
                    email=email,
                    name=name or email.split('@')[0].title(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(customer)
                db.commit()
                db.refresh(customer)
                
                logger.info(f"✅ Created customer record {customer.id} for user {user_id}")
                return customer
                
        except Exception as e:
            logger.error(f"❌ Failed to create customer record for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    async def create_free_trial_subscription(
        user_id: str, 
        email: str, 
        trial_days: int = 14
    ) -> Optional[Dict[str, Any]]:
        """
        Create a free trial subscription for a user.
        Ensures proper user->customer->subscription flow.
        
        Args:
            user_id: Database user ID
            email: User email
            trial_days: Number of trial days (default 14)
            
        Returns:
            Dict: Subscription details or None if failed
        """
        try:
            logger.info(f"Creating free trial subscription for user {user_id}")
            
            # 1. Ensure customer record exists
            customer = await EnhancedSubscriptionFlow.ensure_customer_record(
                user_id=user_id,
                email=email
            )
            
            if not customer:
                logger.error(f"Failed to create customer record for trial subscription")
                return None
            
            # 2. Create trial subscription record
            trial_start = datetime.utcnow()
            trial_end = trial_start + timedelta(days=trial_days)
            
            subscription_data = await SubscriptionService.create_subscription(
                customer_id=customer.id,
                stripe_subscription_id=f"trial_{user_id}_{int(trial_start.timestamp())}",  # Placeholder
                stripe_price_id="trial_price",  # Placeholder
                plan=SubscriptionPlan.PRO,  # Give Pro features during trial
                status=SubscriptionStatus.TRIALING,
                amount=0,  # Free trial
                currency="usd",
                interval="month",
                current_period_start=trial_start,
                current_period_end=trial_end,
                trial_start=trial_start,
                trial_end=trial_end,
                metadata={
                    "type": "free_trial",
                    "trial_days": trial_days,
                    "source": "registration"
                }
            )
            
            logger.info(f"✅ Created free trial subscription for user {user_id}")
            logger.info(f"   Trial period: {trial_days} days")
            logger.info(f"   Expires: {trial_end.isoformat()}")
            
            return {
                "subscription_id": subscription_data["id"],
                "status": "trialing",
                "trial_days": trial_days,
                "trial_end": trial_end.isoformat(),
                "plan": "PRO",
                "amount": 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create free trial for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    async def handle_paid_subscription_signup(
        user_id: str,
        email: str,
        stripe_customer_id: str,
        stripe_subscription_id: str,
        plan: str = "PRO",
        amount: int = 1900  # $19.00 in cents
    ) -> Optional[Dict[str, Any]]:
        """
        Handle paid subscription signup with proper sync.
        Ensures user->customer->subscription flow for paid subscriptions.
        
        Args:
            user_id: Database user ID
            email: User email
            stripe_customer_id: Stripe customer ID
            stripe_subscription_id: Stripe subscription ID
            plan: Subscription plan (default PRO)
            amount: Amount in cents (default $19.00)
            
        Returns:
            Dict: Subscription details or None if failed
        """
        try:
            logger.info(f"Processing paid subscription signup for user {user_id}")
            
            # 1. Ensure customer record exists with Stripe ID
            customer = await SubscriptionService.create_customer(
                user_id=user_id,
                stripe_customer_id=stripe_customer_id,
                email=email
            )
            
            if not customer:
                logger.error(f"Failed to create customer record for paid subscription")
                return None
            
            # 2. Create paid subscription record
            subscription_data = await SubscriptionService.create_subscription(
                customer_id=customer["id"],
                stripe_subscription_id=stripe_subscription_id,
                stripe_price_id="price_pro_monthly",  # Should match your Stripe price ID
                plan=SubscriptionPlan.PRO,
                status=SubscriptionStatus.ACTIVE,
                amount=amount,
                currency="usd",
                interval="month",
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
                metadata={
                    "type": "paid_subscription",
                    "source": "registration",
                    "plan": plan
                }
            )
            
            logger.info(f"✅ Created paid subscription for user {user_id}")
            logger.info(f"   Plan: {plan}")
            logger.info(f"   Amount: ${amount/100:.2f}/month")
            
            return {
                "subscription_id": subscription_data["id"],
                "status": "active",
                "plan": plan,
                "amount": amount,
                "stripe_subscription_id": stripe_subscription_id
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create paid subscription for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    async def get_user_subscription_status(user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive subscription status for a user.
        
        Args:
            user_id: Database user ID
            
        Returns:
            Dict: Complete subscription status information
        """
        try:
            with get_db_context() as db:
                # Get user
                user = db.query(User).filter(User.user_id == user_id).first()
                if not user:
                    return {
                        "has_subscription": False,
                        "error": "User not found"
                    }
                
                # Get customer
                customer = db.query(Customer).filter(Customer.user_id == user_id).first()
                if not customer:
                    return {
                        "has_subscription": False,
                        "status": "no_customer_record",
                        "message": "User has no customer record - never subscribed"
                    }
                
                # Get active subscriptions
                active_subscriptions = db.query(Subscription).filter(
                    Subscription.customer_id == customer.id,
                    Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING])
                ).all()
                
                if not active_subscriptions:
                    return {
                        "has_subscription": False,
                        "status": "no_active_subscription",
                        "message": "User has customer record but no active subscriptions"
                    }
                
                # Return active subscription details
                subscription = active_subscriptions[0]  # Get the first active subscription
                
                return {
                    "has_subscription": True,
                    "status": subscription.status.value,
                    "plan": subscription.plan.value,
                    "amount": subscription.amount,
                    "currency": subscription.currency,
                    "interval": subscription.interval,
                    "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                    "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None,
                    "is_trial": subscription.status == SubscriptionStatus.TRIALING,
                    "stripe_subscription_id": subscription.stripe_subscription_id
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting subscription status for user {user_id}: {str(e)}")
            return {
                "has_subscription": False,
                "error": str(e)
            }