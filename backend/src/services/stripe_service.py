"""
Simple Stripe Payment Service
Handles subscription creation and webhook events
"""

import stripe
import logging
from typing import Dict, Any, Optional, List

# Import config with relative imports
from ..config.env import get_settings

# Import stripe config with proper path handling
import sys
import os
from pathlib import Path

# Get the backend directory and add to path
backend_dir = Path(__file__).parent.parent.parent
config_dir = backend_dir / "config"

if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

try:
    from config.stripe_config import StripeConfig
except ImportError:
    # Fallback: try direct import from config directory
    spec = os.path.join(str(config_dir), "stripe_config.py")
    import importlib.util
    spec = importlib.util.spec_from_file_location("stripe_config", str(config_dir / "stripe_config.py"))
    stripe_config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stripe_config_module)
    StripeConfig = stripe_config_module.StripeConfig

settings = get_settings()

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        # Set Stripe API key from environment
        stripe.api_key = StripeConfig.get_secret_key()
        logger.info("✅ Stripe service initialized")
    
    async def create_customer_and_subscription(
        self, 
        email: str, 
        name: str = None,
        trial_days: int = 0
    ) -> Dict[str, Any]:
        """Create a customer and subscription"""
        try:
            # Create customer
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={'source': 'codeflowops'}
            )
            logger.info(f"Created customer: {customer.id}")
            
            # Create subscription with trial
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{
                    'price': StripeConfig.get_price_id()
                }],
                trial_period_days=trial_days,
                metadata={
                    'plan': 'pro',
                    'trial_days': str(trial_days)
                }
            )
            
            logger.info(f"Created subscription: {subscription.id} with {trial_days} day trial")
            
            return {
                'success': True,
                'customer_id': customer.id,
                'subscription_id': subscription.id,
                'status': subscription.status,
                'trial_end': subscription.trial_end,
                'current_period_end': subscription.current_period_end,
                'plan': 'pro',
                'amount': 1200,  # $12.00 in cents
                'currency': 'usd'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Payment processing failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Service error: {str(e)}")
    
    async def create_checkout_session(self, email: str, name: Optional[str] = None, trial_days: int = 0) -> Dict[str, Any]:
        """Create a Stripe Checkout Session for subscription with payment collection"""
        try:
            import stripe
            stripe.api_key = StripeConfig.get_secret_key()
            
            # Get frontend URL from settings
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
            
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': StripeConfig.get_price_id(),
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f'{frontend_url}/deploy?success=true&subscription=completed',
                cancel_url=f'{frontend_url}/pricing',
                customer_email=email,
                payment_method_collection='always',  # Force payment method collection
                subscription_data={
                    **({'trial_period_days': trial_days} if trial_days > 0 else {}),
                    'metadata': {
                        'plan': 'pro',
                        'trial_days': str(trial_days)
                    }
                },
                metadata={
                    'customer_name': name or '',
                    'plan': 'pro'
                }
            )
            
            logger.info(f"Created checkout session: {checkout_session.id}")
            
            return {
                'success': True,
                'checkout_session_id': checkout_session.id,
                'checkout_url': checkout_session.url,
                'trial_days': trial_days
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            raise Exception(f"Payment processing failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise Exception(f"Service error: {str(e)}")
    
    async def handle_webhook(self, payload: str, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            # Import SubscriptionService here to avoid circular imports
            from .subscription_service import SubscriptionService
            
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, 
                sig_header, 
                StripeConfig.get_webhook_secret()
            )
            
            event_type = event['type']
            event_data = event['data']['object']
            
            logger.info(f"Processing webhook: {event_type}")
            
            webhook_processed = False
            
            # Handle subscription events
            if event_type == 'customer.subscription.created':
                logger.info(f"New subscription created: {event_data['id']}")
                webhook_processed = await SubscriptionService.handle_stripe_webhook_subscription_created(event)
                
            elif event_type == 'customer.subscription.updated':
                logger.info(f"Subscription updated: {event_data['id']}")
                webhook_processed = await SubscriptionService.handle_stripe_webhook_subscription_updated(event)
                
            elif event_type == 'customer.subscription.deleted':
                logger.info(f"Subscription cancelled: {event_data['id']}")
                webhook_processed = await SubscriptionService.handle_stripe_webhook_subscription_updated(event)
                
            elif event_type == 'customer.subscription.trial_will_end':
                logger.info(f"Trial ending soon: {event_data['id']}")
                # For now, just log this - could send notifications later
                webhook_processed = True
                
            elif event_type == 'invoice.payment_succeeded':
                logger.info(f"Payment succeeded: {event_data['id']}")
                # Get subscription data from invoice and update if needed
                subscription_id = event_data.get('subscription')
                if subscription_id:
                    # Retrieve subscription to ensure it's up to date
                    subscription = stripe.Subscription.retrieve(subscription_id)
                    # Create a mock event for subscription update
                    mock_event = {
                        'type': 'customer.subscription.updated',
                        'data': {'object': subscription}
                    }
                    webhook_processed = await SubscriptionService.handle_stripe_webhook_subscription_updated(mock_event)
                else:
                    webhook_processed = True
                
            elif event_type == 'invoice.payment_failed':
                logger.error(f"Payment failed: {event_data['id']}")
                # Could update subscription status to past_due
                subscription_id = event_data.get('subscription')
                if subscription_id:
                    # Update subscription status
                    from ..models.enhanced_models import SubscriptionStatus
                    await SubscriptionService.update_subscription(
                        stripe_subscription_id=subscription_id,
                        status=SubscriptionStatus.PAST_DUE
                    )
                    webhook_processed = True
                else:
                    webhook_processed = True
                    
            elif event_type == 'checkout.session.completed':
                logger.info(f"Checkout session completed: {event_data['id']}")
                # This happens when a customer completes payment
                customer_id = event_data.get('customer')
                customer_email = event_data.get('customer_email')
                subscription_id = event_data.get('subscription')
                
                if customer_id and customer_email:
                    # For now, just log - customer creation will be handled by subscription.created
                    logger.info(f"Customer {customer_id} completed checkout for subscription {subscription_id}")
                    webhook_processed = True
                else:
                    webhook_processed = True
            
            else:
                # For unknown events, don't fail - just log
                logger.info(f"Unhandled webhook event type: {event_type}")
                webhook_processed = True
            
            return {
                'success': True,
                'event_type': event_type,
                'processed': webhook_processed
            }
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise Exception("Invalid webhook signature")
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            raise Exception(f"Webhook error: {str(e)}")
    
    async def get_subscription_status(self, subscription_id: str) -> Dict[str, Any]:
        """Get subscription status"""
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            return {
                'id': subscription.id,
                'status': subscription.status,
                'trial_end': subscription.trial_end,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'customer_id': subscription.customer
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {str(e)}")
            raise Exception(f"Failed to get subscription: {str(e)}")

    async def cancel_subscription(self, subscription_id: str, cancel_at_period_end: bool = True) -> Dict[str, Any]:
        """Cancel a Stripe subscription"""
        try:
            import stripe
            stripe.api_key = StripeConfig.get_secret_key()

            # Cancel the subscription
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=cancel_at_period_end
            )

            logger.info(f"Subscription {subscription_id} cancelled successfully")

            return {
                'id': subscription.id,
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'canceled_at': subscription.canceled_at,
                'current_period_end': subscription.current_period_end,
                'customer_id': subscription.customer
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error cancelling subscription: {str(e)}")
            raise Exception(f"Failed to cancel subscription: {str(e)}")

    async def get_customer_subscriptions(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get all subscriptions for a customer"""
        try:
            import stripe
            stripe.api_key = StripeConfig.get_secret_key()

            subscriptions = stripe.Subscription.list(customer=customer_id)

            return [{
                'id': sub.id,
                'status': sub.status,
                'current_period_start': sub.current_period_start,
                'current_period_end': sub.current_period_end,
                'cancel_at_period_end': sub.cancel_at_period_end,
                'plan': {
                    'id': sub.items.data[0].plan.id,
                    'amount': sub.items.data[0].plan.amount,
                    'currency': sub.items.data[0].plan.currency,
                    'interval': sub.items.data[0].plan.interval
                } if sub.items.data else None
            } for sub in subscriptions.data]

        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving customer subscriptions: {str(e)}")
            raise Exception(f"Failed to get customer subscriptions: {str(e)}")
