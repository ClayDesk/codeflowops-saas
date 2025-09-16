"""
Subscription Service for managing user subscriptions and Stripe integration.
Handles database operations for storing and retrieving subscription data.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..utils.database import get_db_context
from ..models.enhanced_models import User, Customer, Subscription, Payment, SubscriptionPlan, SubscriptionStatus
import logging
import uuid

logger = logging.getLogger(__name__)

class SubscriptionService:
    """Service for managing user subscriptions"""
    
    @staticmethod
    async def create_customer(
        user_id: str,
        stripe_customer_id: str,
        email: str,
        name: Optional[str] = None
    ) -> Customer:
        """Create a new customer record"""
        try:
            with get_db_context() as db:
                # Check if customer already exists
                existing_customer = db.query(Customer).filter(
                    Customer.user_id == user_id
                ).first()
                
                if existing_customer:
                    logger.info(f"Customer already exists for user {user_id}")
                    return {
                        "id": existing_customer.id,
                        "user_id": existing_customer.user_id,
                        "stripe_customer_id": existing_customer.stripe_customer_id,
                        "email": existing_customer.email,
                        "name": existing_customer.name,
                        "created_at": existing_customer.created_at.isoformat() if existing_customer.created_at else None
                    }
                
                # Create new customer
                customer = Customer(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    stripe_customer_id=stripe_customer_id,
                    email=email,
                    name=name,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(customer)
                db.commit()
                db.refresh(customer)
                
                customer_dict = {
                    "id": customer.id,
                    "user_id": customer.user_id,
                    "stripe_customer_id": customer.stripe_customer_id,
                    "email": customer.email,
                    "name": customer.name,
                    "created_at": customer.created_at.isoformat() if customer.created_at else None
                }
                
                logger.info(f"Created customer {customer.id} for user {user_id}")
                return customer_dict
                
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise
    
    @staticmethod
    async def get_customer_by_user_id(user_id: str) -> Optional[Customer]:
        """Get customer by user ID"""
        try:
            with get_db_context() as db:
                customer = db.query(Customer).filter(
                    Customer.user_id == user_id
                ).first()
                return customer
        except Exception as e:
            logger.error(f"Error getting customer for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    async def get_customer_by_stripe_id(stripe_customer_id: str) -> Optional[Customer]:
        """Get customer by Stripe customer ID"""
        try:
            with get_db_context() as db:
                customer = db.query(Customer).filter(
                    Customer.stripe_customer_id == stripe_customer_id
                ).first()
                return customer
        except Exception as e:
            logger.error(f"Error getting customer by Stripe ID {stripe_customer_id}: {str(e)}")
            return None
    
    @staticmethod
    async def create_subscription(
        customer_id: str,
        stripe_subscription_id: str,
        stripe_price_id: str,
        plan: SubscriptionPlan,
        status: SubscriptionStatus,
        amount: int,
        currency: str = "usd",
        interval: str = "month",
        current_period_start: datetime = None,
        current_period_end: datetime = None,
        trial_start: Optional[datetime] = None,
        trial_end: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Subscription:
        """Create a new subscription record"""
        try:
            with get_db_context() as db:
                # Check if subscription already exists
                existing_subscription = db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == stripe_subscription_id
                ).first()
                
                if existing_subscription:
                    logger.info(f"Subscription already exists: {stripe_subscription_id}")
                    return {
                        "id": existing_subscription.id,
                        "customer_id": existing_subscription.customer_id,
                        "stripe_subscription_id": existing_subscription.stripe_subscription_id,
                        "plan": existing_subscription.plan.value,
                        "status": existing_subscription.status.value,
                        "amount": existing_subscription.amount,
                        "currency": existing_subscription.currency,
                        "interval": existing_subscription.interval,
                        "created_at": existing_subscription.created_at.isoformat() if existing_subscription.created_at else None
                    }
                
                # Create new subscription
                subscription = Subscription(
                    id=str(uuid.uuid4()),
                    customer_id=customer_id,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_price_id=stripe_price_id,
                    plan=plan,
                    status=status,
                    amount=amount,
                    currency=currency,
                    interval=interval,
                    current_period_start=current_period_start or datetime.utcnow(),
                    current_period_end=current_period_end or datetime.utcnow(),
                    trial_start=trial_start,
                    trial_end=trial_end,
                    metadata_json=str(metadata) if metadata else None,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(subscription)
                db.commit()
                db.refresh(subscription)
                
                subscription_dict = {
                    "id": subscription.id,
                    "customer_id": subscription.customer_id,
                    "stripe_subscription_id": subscription.stripe_subscription_id,
                    "plan": subscription.plan.value,
                    "status": subscription.status.value,
                    "amount": subscription.amount,
                    "currency": subscription.currency,
                    "interval": subscription.interval,
                    "created_at": subscription.created_at.isoformat() if subscription.created_at else None
                }
                
                logger.info(f"Created subscription {subscription.id} for customer {customer_id}")
                return subscription_dict
                
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    @staticmethod
    async def update_subscription(
        stripe_subscription_id: str,
        status: Optional[SubscriptionStatus] = None,
        current_period_start: Optional[datetime] = None,
        current_period_end: Optional[datetime] = None,
        cancel_at_period_end: Optional[bool] = None,
        canceled_at: Optional[datetime] = None,
        ended_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Subscription]:
        """Update an existing subscription"""
        try:
            with get_db_context() as db:
                subscription = db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == stripe_subscription_id
                ).first()
                
                if not subscription:
                    logger.warning(f"Subscription not found: {stripe_subscription_id}")
                    return None
                
                # Update fields if provided
                if status is not None:
                    subscription.status = status
                if current_period_start is not None:
                    subscription.current_period_start = current_period_start
                if current_period_end is not None:
                    subscription.current_period_end = current_period_end
                if cancel_at_period_end is not None:
                    subscription.cancel_at_period_end = cancel_at_period_end
                if canceled_at is not None:
                    subscription.canceled_at = canceled_at
                if ended_at is not None:
                    subscription.ended_at = ended_at
                if metadata is not None:
                    subscription.metadata_json = str(metadata)
                
                subscription.updated_at = datetime.utcnow()
                
                db.commit()
                db.refresh(subscription)
                
                logger.info(f"Updated subscription {subscription.id}")
                return subscription
                
        except Exception as e:
            logger.error(f"Error updating subscription {stripe_subscription_id}: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_subscription(user_id: str) -> Optional[Dict[str, Any]]:
        """Get the active subscription for a user"""
        try:
            with get_db_context() as db:
                # Get customer for user
                customer = db.query(Customer).filter(
                    Customer.user_id == user_id
                ).first()
                
                if not customer:
                    logger.info(f"No customer found for user {user_id}")
                    return None
                
                # Get active subscription
                subscription = db.query(Subscription).filter(
                    and_(
                        Subscription.customer_id == customer.id,
                        Subscription.status.in_([
                            SubscriptionStatus.ACTIVE,
                            SubscriptionStatus.TRIALING,
                            SubscriptionStatus.PAST_DUE
                        ])
                    )
                ).order_by(desc(Subscription.created_at)).first()
                
                if not subscription:
                    logger.info(f"No active subscription found for user {user_id}")
                    return None
                
                # Return subscription data
                return {
                    "id": subscription.id,
                    "stripe_subscription_id": subscription.stripe_subscription_id,
                    "plan": subscription.plan.value,
                    "status": subscription.status.value,
                    "amount": subscription.amount,
                    "currency": subscription.currency,
                    "interval": subscription.interval,
                    "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
                    "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                    "trial_start": subscription.trial_start.isoformat() if subscription.trial_start else None,
                    "trial_end": subscription.trial_end.isoformat() if subscription.trial_end else None,
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "canceled_at": subscription.canceled_at.isoformat() if subscription.canceled_at else None,
                    "is_active": subscription.is_active,
                    "is_trial": subscription.is_trial,
                    "days_until_end": subscription.days_until_end,
                    "created_at": subscription.created_at.isoformat() if subscription.created_at else None
                }
                
        except Exception as e:
            logger.error(f"Error getting subscription for user {user_id}: {str(e)}")
            return None
    
    @staticmethod
    async def get_subscription_by_stripe_id(stripe_subscription_id: str) -> Optional[Subscription]:
        """Get subscription by Stripe subscription ID"""
        try:
            with get_db_context() as db:
                subscription = db.query(Subscription).filter(
                    Subscription.stripe_subscription_id == stripe_subscription_id
                ).first()
                return subscription
        except Exception as e:
            logger.error(f"Error getting subscription {stripe_subscription_id}: {str(e)}")
            return None
    
    @staticmethod
    async def create_payment(
        customer_id: str,
        amount: int,
        currency: str,
        status: str,
        subscription_id: Optional[str] = None,
        stripe_payment_intent_id: Optional[str] = None,
        stripe_invoice_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """Create a payment record"""
        try:
            with get_db_context() as db:
                payment = Payment(
                    id=str(uuid.uuid4()),
                    customer_id=customer_id,
                    subscription_id=subscription_id,
                    stripe_payment_intent_id=stripe_payment_intent_id,
                    stripe_invoice_id=stripe_invoice_id,
                    amount=amount,
                    currency=currency,
                    status=status,
                    description=description,
                    metadata_json=str(metadata) if metadata else None,
                    created_at=datetime.utcnow()
                )
                
                db.add(payment)
                db.commit()
                db.refresh(payment)
                
                logger.info(f"Created payment {payment.id} for customer {customer_id}")
                return payment
                
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_payments(user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get payment history for a user"""
        try:
            with get_db_context() as db:
                # Get customer for user
                customer = db.query(Customer).filter(
                    Customer.user_id == user_id
                ).first()
                
                if not customer:
                    return []
                
                # Get payments
                payments = db.query(Payment).filter(
                    Payment.customer_id == customer.id
                ).order_by(desc(Payment.created_at)).limit(limit).all()
                
                return [
                    {
                        "id": payment.id,
                        "amount": payment.amount,
                        "currency": payment.currency,
                        "status": payment.status,
                        "description": payment.description,
                        "created_at": payment.created_at.isoformat() if payment.created_at else None
                    }
                    for payment in payments
                ]
                
        except Exception as e:
            logger.error(f"Error getting payments for user {user_id}: {str(e)}")
            return []
    
    @staticmethod
    async def handle_stripe_webhook_subscription_created(webhook_data: Dict[str, Any]) -> bool:
        """Handle Stripe webhook for subscription created event"""
        try:
            subscription_data = webhook_data.get('data', {}).get('object', {})
            
            if not subscription_data:
                logger.error("No subscription data in webhook")
                return False
            
            stripe_subscription_id = subscription_data.get('id')
            stripe_customer_id = subscription_data.get('customer')
            
            if not stripe_subscription_id or not stripe_customer_id:
                logger.error("Missing subscription or customer ID in webhook data")
                return False
            
            # Get customer from database
            customer = await SubscriptionService.get_customer_by_stripe_id(stripe_customer_id)
            if not customer:
                logger.error(f"Customer not found for Stripe ID: {stripe_customer_id}")
                return False
            
            # Extract subscription details
            items = subscription_data.get('items', {}).get('data', [])
            if not items:
                logger.error("No items in subscription")
                return False
            
            price_data = items[0].get('price', {})
            amount = price_data.get('unit_amount', 0)
            currency = price_data.get('currency', 'usd')
            interval = price_data.get('recurring', {}).get('interval', 'month')
            
            # Determine plan based on amount
            plan = SubscriptionPlan.PRO if amount >= 1000 else SubscriptionPlan.FREE
            
            # Convert status
            stripe_status = subscription_data.get('status', 'active')
            status = SubscriptionStatus.ACTIVE
            if stripe_status == 'trialing':
                status = SubscriptionStatus.TRIALING
            elif stripe_status == 'past_due':
                status = SubscriptionStatus.PAST_DUE
            elif stripe_status == 'canceled':
                status = SubscriptionStatus.CANCELED
            elif stripe_status == 'incomplete':
                status = SubscriptionStatus.INCOMPLETE
            
            # Create subscription
            await SubscriptionService.create_subscription(
                customer_id=customer.id,
                stripe_subscription_id=stripe_subscription_id,
                stripe_price_id=price_data.get('id', ''),
                plan=plan,
                status=status,
                amount=amount,
                currency=currency,
                interval=interval,
                current_period_start=datetime.fromtimestamp(subscription_data.get('current_period_start', 0)),
                current_period_end=datetime.fromtimestamp(subscription_data.get('current_period_end', 0)),
                trial_start=datetime.fromtimestamp(subscription_data['trial_start']) if subscription_data.get('trial_start') else None,
                trial_end=datetime.fromtimestamp(subscription_data['trial_end']) if subscription_data.get('trial_end') else None,
                metadata=subscription_data.get('metadata', {})
            )
            
            logger.info(f"Successfully processed subscription created webhook for {stripe_subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing subscription created webhook: {str(e)}")
            return False
    
    @staticmethod
    async def handle_stripe_webhook_subscription_updated(webhook_data: Dict[str, Any]) -> bool:
        """Handle Stripe webhook for subscription updated event"""
        try:
            subscription_data = webhook_data.get('data', {}).get('object', {})
            stripe_subscription_id = subscription_data.get('id')
            
            if not stripe_subscription_id:
                logger.error("No subscription ID in webhook data")
                return False
            
            # Convert status
            stripe_status = subscription_data.get('status', 'active')
            status = SubscriptionStatus.ACTIVE
            if stripe_status == 'trialing':
                status = SubscriptionStatus.TRIALING
            elif stripe_status == 'past_due':
                status = SubscriptionStatus.PAST_DUE
            elif stripe_status == 'canceled':
                status = SubscriptionStatus.CANCELED
            elif stripe_status == 'incomplete':
                status = SubscriptionStatus.INCOMPLETE
            
            # Update subscription
            await SubscriptionService.update_subscription(
                stripe_subscription_id=stripe_subscription_id,
                status=status,
                current_period_start=datetime.fromtimestamp(subscription_data.get('current_period_start', 0)),
                current_period_end=datetime.fromtimestamp(subscription_data.get('current_period_end', 0)),
                cancel_at_period_end=subscription_data.get('cancel_at_period_end', False),
                canceled_at=datetime.fromtimestamp(subscription_data['canceled_at']) if subscription_data.get('canceled_at') else None,
                ended_at=datetime.fromtimestamp(subscription_data['ended_at']) if subscription_data.get('ended_at') else None,
                metadata=subscription_data.get('metadata', {})
            )
            
            logger.info(f"Successfully processed subscription updated webhook for {stripe_subscription_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing subscription updated webhook: {str(e)}")
            return False