"""
Stripe Payment Service for Dynamic Pricing Integration
Handles subscription creation, payment processing, and webhook events
"""

import stripe
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from ..models.billing_models import User, Subscription, PLAN_CONFIGS
from ..services.dynamic_pricing_service import DynamicPricingService
from ..utils.database import get_db

# Configure logging
logger = logging.getLogger(__name__)

class StripePaymentService:
    def __init__(self):
        # Set Stripe API key from environment
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        self.webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
        self.dynamic_pricing = DynamicPricingService()
        
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable is required")
    
    async def create_customer(self, user_email: str, user_name: str = None, metadata: Dict = None) -> str:
        """Create a Stripe customer"""
        try:
            customer_data = {
                'email': user_email,
                'metadata': metadata or {}
            }
            
            if user_name:
                customer_data['name'] = user_name
            
            customer = stripe.Customer.create(**customer_data)
            logger.info(f"Created Stripe customer: {customer.id} for {user_email}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating Stripe customer: {str(e)}")
            raise
    
    async def create_subscription_with_trial(
        self, 
        customer_id: str, 
        plan_tier: str,
        pricing_context: Dict = None,
        trial_days: int = None
    ) -> Dict[str, Any]:
        """Create a subscription with free trial using dynamic pricing"""
        try:
            # Get dynamic pricing for the plan
            pricing_data = await self.dynamic_pricing.get_personalized_pricing(
                context=pricing_context or {}
            )
            
            # Find the specific plan
            plan_data = None
            for plan in pricing_data['plans']:
                if plan['tier'] == plan_tier:
                    plan_data = plan
                    break
            
            if not plan_data:
                raise ValueError(f"Plan {plan_tier} not found")
            
            # Determine trial period
            trial_period_days = trial_days or plan_data.get('trial_days', 0)
            
            # Create price if promotional pricing is applied
            price_amount = plan_data.get('promotional_price') or plan_data['price_monthly']
            
            # Create or get Stripe price
            stripe_price = await self._get_or_create_price(
                amount=price_amount,
                currency=pricing_data.get('currency', 'USD').lower(),
                interval='month',
                plan_tier=plan_tier,
                promotional=bool(plan_data.get('promotional_price'))
            )
            
            # Create subscription
            subscription_data = {
                'customer': customer_id,
                'items': [{'price': stripe_price.id}],
                'metadata': {
                    'plan_tier': plan_tier,
                    'original_price': plan_data['price_monthly'],
                    'promotional_price': plan_data.get('promotional_price'),
                    'geographic_discount': plan_data.get('geographic_discount', False),
                    'user_segment': pricing_data['personalization']['user_segment']
                },
                'expand': ['latest_invoice.payment_intent']
            }
            
            # Add trial period if applicable
            if trial_period_days > 0:
                subscription_data['trial_period_days'] = trial_period_days
                subscription_data['metadata']['trial_days'] = trial_period_days
            
            subscription = stripe.Subscription.create(**subscription_data)
            
            logger.info(f"Created subscription: {subscription.id} for customer: {customer_id}")
            
            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice.payment_intent else None,
                'trial_end': subscription.trial_end,
                'current_period_end': subscription.current_period_end,
                'pricing_details': {
                    'amount': price_amount,
                    'currency': pricing_data.get('currency', 'USD'),
                    'plan_tier': plan_tier,
                    'discounts_applied': pricing_data['personalization']['applied']
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    async def _get_or_create_price(
        self,
        amount: int,
        currency: str,
        interval: str,
        plan_tier: str,
        promotional: bool = False
    ) -> stripe.Price:
        """Get existing price or create new one"""
        try:
            # Create a unique price ID based on parameters
            price_nickname = f"{plan_tier}_{amount}_{currency}_{interval}"
            if promotional:
                price_nickname += "_promo"
            
            # Search for existing price
            prices = stripe.Price.list(
                product=await self._get_or_create_product(plan_tier),
                active=True,
                type='recurring'
            )
            
            for price in prices.data:
                if (price.unit_amount == amount and 
                    price.currency == currency and 
                    price.recurring.interval == interval):
                    return price
            
            # Create new price if not found
            price = stripe.Price.create(
                unit_amount=amount,
                currency=currency,
                recurring={'interval': interval},
                product=await self._get_or_create_product(plan_tier),
                nickname=price_nickname,
                metadata={
                    'plan_tier': plan_tier,
                    'promotional': promotional
                }
            )
            
            logger.info(f"Created new price: {price.id} for {plan_tier}")
            return price
            
        except stripe.error.StripeError as e:
            logger.error(f"Error getting/creating price: {str(e)}")
            raise
    
    async def _get_or_create_product(self, plan_tier: str) -> str:
        """Get existing product or create new one"""
        try:
            plan_config = PLAN_CONFIGS.get(plan_tier)
            if not plan_config:
                raise ValueError(f"Invalid plan tier: {plan_tier}")
            
            product_name = f"CodeFlowOps {plan_config['name']}"
            
            # Search for existing product
            products = stripe.Product.list(active=True)
            for product in products.data:
                if product.name == product_name:
                    return product.id
            
            # Create new product
            product = stripe.Product.create(
                name=product_name,
                description=plan_config.get('description', f"CodeFlowOps {plan_config['name']} Plan"),
                metadata={
                    'plan_tier': plan_tier,
                    'max_projects': plan_config['max_projects'],
                    'max_team_members': plan_config['max_team_members']
                }
            )
            
            logger.info(f"Created new product: {product.id} for {plan_tier}")
            return product.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Error getting/creating product: {str(e)}")
            raise
    
    async def create_payment_intent(
        self,
        amount: int,
        currency: str = 'usd',
        customer_id: str = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Create a payment intent for one-time payments"""
        try:
            payment_intent_data = {
                'amount': amount,
                'currency': currency,
                'automatic_payment_methods': {'enabled': True},
                'metadata': metadata or {}
            }
            
            if customer_id:
                payment_intent_data['customer'] = customer_id
            
            payment_intent = stripe.PaymentIntent.create(**payment_intent_data)
            
            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'status': payment_intent.status
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise
    
    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Dict[str, Any]:
        """Cancel a subscription"""
        try:
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            
            logger.info(f"Cancelled subscription: {subscription_id}")
            
            return {
                'subscription_id': subscription.id,
                'status': subscription.status,
                'canceled_at': subscription.canceled_at,
                'cancel_at_period_end': subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            raise
    
    async def upgrade_subscription(
        self,
        subscription_id: str,
        new_plan_tier: str,
        pricing_context: Dict = None
    ) -> Dict[str, Any]:
        """Upgrade/downgrade a subscription to a new plan"""
        try:
            # Get current subscription
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Get dynamic pricing for new plan
            pricing_data = await self.dynamic_pricing.get_personalized_pricing(
                context=pricing_context or {}
            )
            
            # Find the new plan
            new_plan_data = None
            for plan in pricing_data['plans']:
                if plan['tier'] == new_plan_tier:
                    new_plan_data = plan
                    break
            
            if not new_plan_data:
                raise ValueError(f"Plan {new_plan_tier} not found")
            
            # Create or get new price
            new_price = await self._get_or_create_price(
                amount=new_plan_data.get('promotional_price') or new_plan_data['price_monthly'],
                currency=pricing_data.get('currency', 'USD').lower(),
                interval='month',
                plan_tier=new_plan_tier,
                promotional=bool(new_plan_data.get('promotional_price'))
            )
            
            # Update subscription
            updated_subscription = stripe.Subscription.modify(
                subscription_id,
                items=[{
                    'id': subscription['items']['data'][0].id,
                    'price': new_price.id,
                }],
                proration_behavior='immediate_with_remainder',
                metadata={
                    'plan_tier': new_plan_tier,
                    'upgraded_at': datetime.utcnow().isoformat(),
                    'previous_plan': subscription.metadata.get('plan_tier'),
                    'user_segment': pricing_data['personalization']['user_segment']
                }
            )
            
            logger.info(f"Updated subscription: {subscription_id} to {new_plan_tier}")
            
            return {
                'subscription_id': updated_subscription.id,
                'status': updated_subscription.status,
                'new_plan_tier': new_plan_tier,
                'pricing_details': {
                    'amount': new_plan_data.get('promotional_price') or new_plan_data['price_monthly'],
                    'currency': pricing_data.get('currency', 'USD'),
                    'discounts_applied': pricing_data['personalization']['applied']
                }
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error upgrading subscription: {str(e)}")
            raise
    
    async def handle_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            event_type = event['type']
            event_data = event['data']['object']
            
            logger.info(f"Processing webhook event: {event_type}")
            
            handlers = {
                'invoice.payment_succeeded': self._handle_payment_succeeded,
                'invoice.payment_failed': self._handle_payment_failed,
                'customer.subscription.created': self._handle_subscription_created,
                'customer.subscription.updated': self._handle_subscription_updated,
                'customer.subscription.deleted': self._handle_subscription_deleted,
                'customer.subscription.trial_will_end': self._handle_trial_will_end,
            }
            
            handler = handlers.get(event_type)
            if handler:
                return await handler(event_data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {'status': 'ignored', 'event_type': event_type}
                
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            raise
    
    async def _handle_payment_succeeded(self, invoice: Dict) -> Dict[str, Any]:
        """Handle successful payment"""
        logger.info(f"Payment succeeded for invoice: {invoice['id']}")
        # Update user subscription status in database
        # Implementation depends on your database structure
        return {'status': 'processed', 'action': 'payment_succeeded'}
    
    async def _handle_payment_failed(self, invoice: Dict) -> Dict[str, Any]:
        """Handle failed payment"""
        logger.info(f"Payment failed for invoice: {invoice['id']}")
        # Handle failed payment (send notification, update status, etc.)
        return {'status': 'processed', 'action': 'payment_failed'}
    
    async def _handle_subscription_created(self, subscription: Dict) -> Dict[str, Any]:
        """Handle subscription creation"""
        logger.info(f"Subscription created: {subscription['id']}")
        # Update user subscription in database
        return {'status': 'processed', 'action': 'subscription_created'}
    
    async def _handle_subscription_updated(self, subscription: Dict) -> Dict[str, Any]:
        """Handle subscription update"""
        logger.info(f"Subscription updated: {subscription['id']}")
        # Update user subscription in database
        return {'status': 'processed', 'action': 'subscription_updated'}
    
    async def _handle_subscription_deleted(self, subscription: Dict) -> Dict[str, Any]:
        """Handle subscription deletion"""
        logger.info(f"Subscription deleted: {subscription['id']}")
        # Update user subscription status in database
        return {'status': 'processed', 'action': 'subscription_deleted'}
    
    async def _handle_trial_will_end(self, subscription: Dict) -> Dict[str, Any]:
        """Handle trial ending soon"""
        logger.info(f"Trial will end for subscription: {subscription['id']}")
        # Send notification to user about trial ending
        return {'status': 'processed', 'action': 'trial_will_end'}
    
    async def get_subscription_details(self, subscription_id: str) -> Dict[str, Any]:
        """Get detailed subscription information"""
        try:
            subscription = stripe.Subscription.retrieve(
                subscription_id,
                expand=['customer', 'latest_invoice', 'items.data.price.product']
            )
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_start': subscription.current_period_start,
                'current_period_end': subscription.current_period_end,
                'trial_start': subscription.trial_start,
                'trial_end': subscription.trial_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'customer_email': subscription.customer.email,
                'plan_tier': subscription.metadata.get('plan_tier'),
                'amount': subscription.items.data[0].price.unit_amount,
                'currency': subscription.items.data[0].price.currency,
                'interval': subscription.items.data[0].price.recurring.interval,
                'metadata': subscription.metadata
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error getting subscription details: {str(e)}")
            raise
