"""
Simple Stripe Payment Service
Handles subscription creation and webhook events
"""

import stripe
import logging
from typing import Dict, Any, Optional

# Import config with fallback for different path structures
try:
    from ...config.stripe_config import StripeConfig
except ImportError:
    try:
        from config.stripe_config import StripeConfig
    except ImportError:
        from backend.config.stripe_config import StripeConfig

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
        trial_days: int = 14
    ) -> Dict[str, Any]:
        """Create a customer and subscription with free trial"""
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
    
    async def create_checkout_session(self, email: str, name: Optional[str] = None, trial_days: int = 14) -> Dict[str, Any]:
        """Create a Stripe Checkout Session for subscription with payment collection"""
        try:
            import stripe
            stripe.api_key = StripeConfig.get_secret_key()
            
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': StripeConfig.get_price_id(),
                    'quantity': 1,
                }],
                mode='subscription',
                success_url='https://codeflowops.com/profile?tab=subscription&success=true',
                cancel_url='https://codeflowops.com/pricing',
                customer_email=email,
                subscription_data={
                    'trial_period_days': trial_days,
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
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, 
                sig_header, 
                StripeConfig.get_webhook_secret()
            )
            
            event_type = event['type']
            event_data = event['data']['object']
            
            logger.info(f"Processing webhook: {event_type}")
            
            # Handle key events
            if event_type == 'customer.subscription.created':
                logger.info(f"New subscription created: {event_data['id']}")
                # TODO: Update user status in database
                
            elif event_type == 'customer.subscription.trial_will_end':
                logger.info(f"Trial ending soon: {event_data['id']}")
                # TODO: Send notification to user
                
            elif event_type == 'invoice.payment_succeeded':
                logger.info(f"Payment succeeded: {event_data['id']}")
                # TODO: Activate user subscription
                
            elif event_type == 'invoice.payment_failed':
                logger.error(f"Payment failed: {event_data['id']}")
                # TODO: Handle failed payment
                
            elif event_type == 'customer.subscription.deleted':
                logger.info(f"Subscription cancelled: {event_data['id']}")
                # TODO: Deactivate user account
            
            return {
                'success': True,
                'event_type': event_type,
                'processed': True
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
