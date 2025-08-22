# Stripe Integration Service for CodeFlowOps Billing
import os
import stripe
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models.billing_models import (
    BillingPlan, OrganizationSubscription, Invoice, Payment, UsageEvent,
    PlanTier, SubscriptionStatus, PaymentStatus, PLAN_CONFIGS
)
from ..models.enhanced_models import Organization
from ..utils.database import get_db_session
from ..config.stripe_config import stripe_config

# Configure Stripe
stripe.api_key = stripe_config.get_secret_key()
STRIPE_WEBHOOK_SECRET = stripe_config.get_webhook_secret()

class StripeService:
    """
    Service for managing Stripe billing operations
    """
    
    def __init__(self):
        self.stripe = stripe
    
    async def initialize_plans(self, db: Session):
        """
        Initialize billing plans in database and create Stripe products/prices
        """
        for tier, config in PLAN_CONFIGS.items():
            # Check if plan exists
            existing_plan = db.query(BillingPlan).filter(
                BillingPlan.tier == tier
            ).first()
            
            if not existing_plan:
                # Create Stripe product for paid plans
                stripe_product_id = None
                stripe_price_id = None
                
                if config["price_monthly"] > 0:
                    # Create Stripe product
                    stripe_product = self.stripe.Product.create(
                        name=f"CodeFlowOps {config['name']}",
                        description=config["description"],
                        metadata={
                            "tier": tier.value,
                            "max_projects": str(config["max_projects"]),
                            "max_minutes": str(config["max_minutes_per_month"])
                        }
                    )
                    stripe_product_id = stripe_product.id
                    
                    # Create Stripe price (monthly)
                    stripe_price = self.stripe.Price.create(
                        product=stripe_product_id,
                        unit_amount=config["price_monthly"],
                        currency="usd",
                        recurring={"interval": "month"},
                        metadata={"tier": tier.value}
                    )
                    stripe_price_id = stripe_price.id
                
                # Create billing plan in database
                plan = BillingPlan(
                    **config,
                    stripe_product_id=stripe_product_id,
                    stripe_price_id=stripe_price_id
                )
                db.add(plan)
        
        db.commit()
    
    async def create_customer(self, organization: Organization, email: str) -> str:
        """
        Create a Stripe customer for an organization
        """
        try:
            customer = self.stripe.Customer.create(
                email=email,
                name=organization.name,
                metadata={
                    "organization_id": organization.id,
                    "organization_name": organization.name
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Failed to create customer: {str(e)}")
    
    async def create_subscription(
        self, 
        db: Session,
        organization_id: str,
        plan_tier: PlanTier,
        payment_method_id: str,
        trial_days: int = 0
    ) -> OrganizationSubscription:
        """
        Create a new subscription for an organization
        """
        try:
            # Get organization and plan
            organization = db.query(Organization).filter(Organization.id == organization_id).first()
            if not organization:
                raise HTTPException(status_code=404, detail="Organization not found")
            
            plan = db.query(BillingPlan).filter(BillingPlan.tier == plan_tier).first()
            if not plan:
                raise HTTPException(status_code=404, detail="Plan not found")
            
            # Create Stripe customer if needed
            if not hasattr(organization, 'stripe_customer_id') or not organization.stripe_customer_id:
                stripe_customer_id = await self.create_customer(organization, organization.admin_email)
                # Update organization with Stripe customer ID (would need to add this field to Organization model)
            else:
                stripe_customer_id = organization.stripe_customer_id
            
            # Attach payment method to customer
            self.stripe.PaymentMethod.attach(
                payment_method_id,
                customer=stripe_customer_id
            )
            
            # Set as default payment method
            self.stripe.Customer.modify(
                stripe_customer_id,
                invoice_settings={"default_payment_method": payment_method_id}
            )
            
            # Create subscription params
            subscription_params = {
                "customer": stripe_customer_id,
                "items": [{"price": plan.stripe_price_id}],
                "expand": ["latest_invoice.payment_intent"],
                "metadata": {
                    "organization_id": organization_id,
                    "plan_tier": plan_tier.value
                }
            }
            
            # Add trial if specified
            if trial_days > 0:
                subscription_params["trial_period_days"] = trial_days
            
            # Create Stripe subscription
            stripe_subscription = self.stripe.Subscription.create(**subscription_params)
            
            # Create database subscription record
            subscription = OrganizationSubscription(
                id=f"sub_{organization_id}_{datetime.utcnow().timestamp()}",
                organization_id=organization_id,
                plan_id=plan.id,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=stripe_customer_id,
                stripe_payment_method_id=payment_method_id,
                status=SubscriptionStatus(stripe_subscription.status),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                next_billing_date=datetime.fromtimestamp(stripe_subscription.current_period_end)
            )
            
            # Handle trial
            if stripe_subscription.trial_start and stripe_subscription.trial_end:
                subscription.trial_start = datetime.fromtimestamp(stripe_subscription.trial_start)
                subscription.trial_end = datetime.fromtimestamp(stripe_subscription.trial_end)
            
            db.add(subscription)
            db.commit()
            
            return subscription
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Failed to create subscription: {str(e)}")
    
    async def cancel_subscription(
        self, 
        db: Session,
        subscription_id: str,
        immediate: bool = False
    ) -> OrganizationSubscription:
        """
        Cancel a subscription
        """
        try:
            # Get subscription from database
            subscription = db.query(OrganizationSubscription).filter(
                OrganizationSubscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise HTTPException(status_code=404, detail="Subscription not found")
            
            # Cancel in Stripe
            if immediate:
                stripe_subscription = self.stripe.Subscription.delete(
                    subscription.stripe_subscription_id
                )
                subscription.status = SubscriptionStatus.CANCELED
                subscription.canceled_at = datetime.utcnow()
            else:
                stripe_subscription = self.stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.cancel_at_period_end = True
            
            db.commit()
            return subscription
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Failed to cancel subscription: {str(e)}")
    
    async def change_plan(
        self,
        db: Session,
        subscription_id: str,
        new_plan_tier: PlanTier,
        prorate: bool = True
    ) -> OrganizationSubscription:
        """
        Change subscription plan
        """
        try:
            # Get subscription and new plan
            subscription = db.query(OrganizationSubscription).filter(
                OrganizationSubscription.id == subscription_id
            ).first()
            
            if not subscription:
                raise HTTPException(status_code=404, detail="Subscription not found")
            
            new_plan = db.query(BillingPlan).filter(BillingPlan.tier == new_plan_tier).first()
            if not new_plan:
                raise HTTPException(status_code=404, detail="New plan not found")
            
            # Get current Stripe subscription
            stripe_subscription = self.stripe.Subscription.retrieve(
                subscription.stripe_subscription_id
            )
            
            # Update subscription in Stripe
            updated_subscription = self.stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                items=[{
                    "id": stripe_subscription["items"]["data"][0]["id"],
                    "price": new_plan.stripe_price_id
                }],
                proration_behavior="create_prorations" if prorate else "none",
                metadata={
                    "organization_id": subscription.organization_id,
                    "plan_tier": new_plan_tier.value
                }
            )
            
            # Update database record
            subscription.plan_id = new_plan.id
            subscription.current_period_start = datetime.fromtimestamp(updated_subscription.current_period_start)
            subscription.current_period_end = datetime.fromtimestamp(updated_subscription.current_period_end)
            subscription.next_billing_date = datetime.fromtimestamp(updated_subscription.current_period_end)
            
            db.commit()
            return subscription
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Failed to change plan: {str(e)}")
    
    async def process_usage_event(
        self,
        db: Session,
        organization_id: str,
        user_id: str,
        event_type: str,
        quantity: int = 1,
        metadata: Dict = None
    ):
        """
        Record a usage event for billing purposes
        """
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        usage_event = UsageEvent(
            id=f"usage_{organization_id}_{datetime.utcnow().timestamp()}",
            organization_id=organization_id,
            user_id=user_id,
            event_type=event_type,
            quantity=quantity,
            billing_month=current_month,
            metadata_json=json.dumps(metadata or {})
        )
        
        db.add(usage_event)
        
        # Update subscription usage counters
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.organization_id == organization_id,
            OrganizationSubscription.status == SubscriptionStatus.ACTIVE
        ).first()
        
        if subscription:
            if event_type == "deployment_minute":
                subscription.current_month_minutes_used += quantity
            elif event_type == "project_created":
                subscription.current_month_projects_count += quantity
        
        db.commit()
    
    async def get_usage_summary(self, db: Session, organization_id: str) -> Dict:
        """
        Get current month usage summary for an organization
        """
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        # Get subscription and plan
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.organization_id == organization_id,
            OrganizationSubscription.status == SubscriptionStatus.ACTIVE
        ).first()
        
        if not subscription:
            # Return free plan limits
            plan_config = PLAN_CONFIGS[PlanTier.FREE]
            return {
                "plan_name": "Free",
                "plan_tier": "free",
                "minutes_used": 0,
                "minutes_limit": plan_config["max_minutes_per_month"],
                "projects_count": 0,
                "projects_limit": plan_config["max_projects"],
                "team_members_count": 1,
                "team_members_limit": plan_config["max_team_members"]
            }
        
        plan = subscription.plan
        
        return {
            "plan_name": plan.name,
            "plan_tier": plan.tier.value,
            "minutes_used": subscription.current_month_minutes_used,
            "minutes_limit": plan.max_minutes_per_month,
            "projects_count": subscription.current_month_projects_count,
            "projects_limit": plan.max_projects,
            "team_members_count": 1,  # Would need to calculate from actual team
            "team_members_limit": plan.max_team_members,
            "billing_period_start": subscription.current_period_start,
            "billing_period_end": subscription.current_period_end,
            "next_billing_date": subscription.next_billing_date
        }
    
    async def handle_webhook(self, payload: str, signature: str, db: Session):
        """
        Handle Stripe webhook events
        """
        try:
            event = self.stripe.Webhook.construct_event(
                payload, signature, STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle different event types
        if event["type"] == "invoice.payment_succeeded":
            await self._handle_payment_succeeded(db, event["data"]["object"])
        elif event["type"] == "invoice.payment_failed":
            await self._handle_payment_failed(db, event["data"]["object"])
        elif event["type"] == "customer.subscription.updated":
            await self._handle_subscription_updated(db, event["data"]["object"])
        elif event["type"] == "customer.subscription.deleted":
            await self._handle_subscription_deleted(db, event["data"]["object"])
        elif event["type"] == "invoice.created":
            await self._handle_invoice_created(db, event["data"]["object"])
    
    async def _handle_payment_succeeded(self, db: Session, invoice_data: Dict):
        """Handle successful payment"""
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.stripe_subscription_id == invoice_data["subscription"]
        ).first()
        
        if subscription:
            # Update subscription status
            subscription.status = SubscriptionStatus.ACTIVE
            subscription.last_payment_date = datetime.utcnow()
            
            # Reset monthly usage counters at start of new billing period
            if datetime.utcnow() >= subscription.current_period_end:
                subscription.current_month_minutes_used = 0
                subscription.current_month_projects_count = 0
            
            # Create payment record
            payment = Payment(
                id=f"pay_{subscription.id}_{datetime.utcnow().timestamp()}",
                subscription_id=subscription.id,
                stripe_payment_intent_id=invoice_data.get("payment_intent"),
                amount=invoice_data["amount_paid"],
                currency=invoice_data["currency"],
                status=PaymentStatus.SUCCEEDED,
                description=f"Payment for {subscription.plan.name} plan"
            )
            db.add(payment)
            
            db.commit()
    
    async def _handle_payment_failed(self, db: Session, invoice_data: Dict):
        """Handle failed payment"""
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.stripe_subscription_id == invoice_data["subscription"]
        ).first()
        
        if subscription:
            subscription.status = SubscriptionStatus.PAST_DUE
            
            # Create failed payment record
            payment = Payment(
                id=f"pay_{subscription.id}_{datetime.utcnow().timestamp()}",
                subscription_id=subscription.id,
                stripe_payment_intent_id=invoice_data.get("payment_intent"),
                amount=invoice_data["amount_due"],
                currency=invoice_data["currency"],
                status=PaymentStatus.FAILED,
                failure_reason=invoice_data.get("last_payment_error", {}).get("message"),
                description=f"Failed payment for {subscription.plan.name} plan"
            )
            db.add(payment)
            
            db.commit()
    
    async def _handle_subscription_updated(self, db: Session, subscription_data: Dict):
        """Handle subscription updates"""
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.stripe_subscription_id == subscription_data["id"]
        ).first()
        
        if subscription:
            subscription.status = SubscriptionStatus(subscription_data["status"])
            subscription.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
            subscription.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])
            subscription.cancel_at_period_end = subscription_data["cancel_at_period_end"]
            
            if subscription_data.get("canceled_at"):
                subscription.canceled_at = datetime.fromtimestamp(subscription_data["canceled_at"])
            
            db.commit()
    
    async def _handle_subscription_deleted(self, db: Session, subscription_data: Dict):
        """Handle subscription deletion"""
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.stripe_subscription_id == subscription_data["id"]
        ).first()
        
        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            subscription.canceled_at = datetime.utcnow()
            db.commit()
    
    async def _handle_invoice_created(self, db: Session, invoice_data: Dict):
        """Handle invoice creation"""
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.stripe_subscription_id == invoice_data["subscription"]
        ).first()
        
        if subscription:
            # Create invoice record
            invoice = Invoice(
                id=f"inv_{subscription.id}_{datetime.utcnow().timestamp()}",
                subscription_id=subscription.id,
                stripe_invoice_id=invoice_data["id"],
                invoice_number=invoice_data.get("number"),
                amount_due=invoice_data["amount_due"],
                amount_paid=invoice_data["amount_paid"],
                amount_remaining=invoice_data["amount_remaining"],
                period_start=datetime.fromtimestamp(invoice_data["period_start"]),
                period_end=datetime.fromtimestamp(invoice_data["period_end"]),
                status=invoice_data["status"],
                paid=invoice_data["paid"],
                invoice_pdf=invoice_data.get("invoice_pdf"),
                hosted_invoice_url=invoice_data.get("hosted_invoice_url"),
                due_date=datetime.fromtimestamp(invoice_data["due_date"]) if invoice_data.get("due_date") else None
            )
            db.add(invoice)
            db.commit()

# Global instance
stripe_service = StripeService()
