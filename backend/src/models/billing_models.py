# Billing and Subscription Models for CodeFlowOps SaaS
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Float, Text, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List
import enum

Base = declarative_base()

class PlanTier(enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(enum.Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"

class BillingPlan(Base):
    """
    Available billing plans with features and pricing
    """
    __tablename__ = "billing_plans"
    
    id = Column(String, primary_key=True)
    name = Column(String(100), nullable=False)
    tier = Column(Enum(PlanTier), nullable=False)
    stripe_price_id = Column(String(100), unique=True)  # Stripe Price ID
    stripe_product_id = Column(String(100))  # Stripe Product ID
    
    # Pricing
    price_monthly = Column(Float, default=0.0)  # USD cents
    price_yearly = Column(Float, default=0.0)   # USD cents (with discount)
    
    # Feature Limits
    max_projects = Column(Integer, default=3)
    max_team_members = Column(Integer, default=1)
    max_concurrent_deployments = Column(Integer, default=1)
    
    # Features
    custom_domains = Column(Boolean, default=False)
    priority_support = Column(Boolean, default=False)
    advanced_analytics = Column(Boolean, default=False)
    sso_integration = Column(Boolean, default=False)
    api_access = Column(Boolean, default=False)
    
    # Metadata
    description = Column(Text)
    features_json = Column(Text)  # JSON string of additional features
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("OrganizationSubscription", back_populates="plan")

class OrganizationSubscription(Base):
    """
    Organization's subscription to a billing plan
    """
    __tablename__ = "organization_subscriptions"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    plan_id = Column(String, ForeignKey("billing_plans.id"), nullable=False)
    
    # Stripe Integration
    stripe_subscription_id = Column(String(100), unique=True)
    stripe_customer_id = Column(String(100))
    stripe_payment_method_id = Column(String(100))
    
    # Subscription Details
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE)
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime)
    
    # Trial Information
    trial_start = Column(DateTime)
    trial_end = Column(DateTime)
    
    # Usage Tracking
    current_month_projects_count = Column(Integer, default=0)
    
    # Billing
    next_billing_date = Column(DateTime)
    last_payment_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    plan = relationship("BillingPlan", back_populates="subscriptions")
    organization = relationship("Organization", back_populates="subscription")
    invoices = relationship("Invoice", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription")

class Invoice(Base):
    """
    Stripe invoices for subscription billing
    """
    __tablename__ = "invoices"
    
    id = Column(String, primary_key=True)
    subscription_id = Column(String, ForeignKey("organization_subscriptions.id"), nullable=False)
    
    # Stripe Integration
    stripe_invoice_id = Column(String(100), unique=True, nullable=False)
    stripe_payment_intent_id = Column(String(100))
    
    # Invoice Details
    invoice_number = Column(String(100))
    amount_paid = Column(Integer, default=0)  # Amount in cents
    amount_due = Column(Integer, default=0)   # Amount in cents
    amount_remaining = Column(Integer, default=0)  # Amount in cents
    
    # Billing Period
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    
    # Status and Dates
    status = Column(String(50))  # Stripe invoice status
    paid = Column(Boolean, default=False)
    invoice_pdf = Column(String(500))  # URL to Stripe PDF
    hosted_invoice_url = Column(String(500))  # Stripe hosted page
    
    due_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscription = relationship("OrganizationSubscription", back_populates="invoices")

class Payment(Base):
    """
    Payment transactions and history
    """
    __tablename__ = "payments"
    
    id = Column(String, primary_key=True)
    subscription_id = Column(String, ForeignKey("organization_subscriptions.id"), nullable=False)
    invoice_id = Column(String, ForeignKey("invoices.id"))
    
    # Stripe Integration
    stripe_payment_intent_id = Column(String(100), unique=True)
    stripe_charge_id = Column(String(100))
    
    # Payment Details
    amount = Column(Integer, nullable=False)  # Amount in cents
    currency = Column(String(3), default="usd")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # Payment Method
    payment_method_type = Column(String(50))  # card, bank_transfer, etc.
    last_four = Column(String(4))  # Last 4 digits of card
    brand = Column(String(50))  # visa, mastercard, etc.
    
    # Metadata
    description = Column(Text)
    failure_reason = Column(Text)
    receipt_url = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscription = relationship("OrganizationSubscription", back_populates="payments")
    invoice = relationship("Invoice")

class UsageEvent(Base):
    """
    Track usage events for billing purposes
    """
    __tablename__ = "usage_events"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Usage Details
    event_type = Column(String(50), nullable=False)  # deployment, build_minute, api_call
    quantity = Column(Integer, default=1)
    metadata_json = Column(Text)  # Additional event data
    
    # Billing Period
    billing_month = Column(String(7))  # YYYY-MM format
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization")
    user = relationship("User")

class BillingAddress(Base):
    """
    Organization billing address for invoices
    """
    __tablename__ = "billing_addresses"
    
    id = Column(String, primary_key=True)
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    
    # Address Details
    company_name = Column(String(200))
    line1 = Column(String(200), nullable=False)
    line2 = Column(String(200))
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    postal_code = Column(String(20), nullable=False)
    country = Column(String(2), nullable=False)  # ISO country code
    
    # Tax Information
    tax_id = Column(String(100))  # VAT ID, EIN, etc.
    tax_id_type = Column(String(50))  # vat, ein, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="billing_address")

# Predefined plan configurations
PLAN_CONFIGS = {
    PlanTier.FREE: {
        "id": "plan_free",
        "name": "Free",
        "tier": PlanTier.FREE,
        "price_monthly": 0,
        "price_yearly": 0,
        "max_projects": 3,
        "max_team_members": 1,
        "max_concurrent_deployments": 1,
        "custom_domains": False,
        "priority_support": False,
        "advanced_analytics": False,
        "sso_integration": False,
        "api_access": False,
        "description": "Perfect for personal projects and getting started",
        "features_json": '["3 projects", "Public repositories", "Community support", "Basic analytics"]'
    },
    PlanTier.STARTER: {
        "id": "plan_starter",
        "name": "Starter",
        "tier": PlanTier.STARTER,
        "price_monthly": 1900,  # $19.00
        "price_yearly": 19000,  # $190.00 (2 months free)
        "max_projects": 10,
        "max_team_members": 3,
        "max_concurrent_deployments": 2,
        "custom_domains": True,
        "priority_support": False,
        "advanced_analytics": False,
        "sso_integration": False,
        "api_access": True,
        "description": "Great for small teams and growing projects",
        "features_json": '["10 projects", "Private repositories", "Custom domains", "API access", "Email support"]'
    },
    PlanTier.PRO: {
        "id": "plan_pro",
        "name": "Pro",
        "tier": PlanTier.PRO,
        "price_monthly": 4900,  # $49.00
        "price_yearly": 49000,  # $490.00 (2 months free)
        "max_projects": -1,  # Unlimited
        "max_team_members": 10,
        "max_concurrent_deployments": 5,
        "custom_domains": True,
        "priority_support": True,
        "advanced_analytics": True,
        "sso_integration": True,
        "api_access": True,
        "description": "For professional teams with advanced needs",
        "features_json": '["Unlimited projects", "Private repositories", "Priority support", "Advanced analytics", "Team collaboration", "SSO integration"]'
    },
    PlanTier.ENTERPRISE: {
        "id": "plan_enterprise",
        "name": "Enterprise",
        "tier": PlanTier.ENTERPRISE,
        "price_monthly": 0,  # Custom pricing
        "price_yearly": 0,   # Custom pricing
        "max_projects": -1,  # Unlimited
        "max_team_members": -1,  # Unlimited
        "max_concurrent_deployments": -1,  # Unlimited
        "custom_domains": True,
        "priority_support": True,
        "advanced_analytics": True,
        "sso_integration": True,
        "api_access": True,
        "description": "Custom solutions for large organizations",
        "features_json": '["Unlimited everything", "Dedicated support", "Custom integrations", "SLA guarantees", "On-premise deployment", "Custom contracts"]'
    }
}

# Add billing relationships to existing models
def add_billing_relationships():
    """
    Add billing relationships to existing Organization and User models
    This should be imported after the existing models are defined
    """
    from ..models.enhanced_models import Organization, User
    
    # Add to Organization model
    Organization.subscription = relationship("OrganizationSubscription", back_populates="organization", uselist=False)
    Organization.billing_address = relationship("BillingAddress", back_populates="organization", uselist=False)
    
    # Add billing-related properties
    def get_current_plan(self):
        if self.subscription and self.subscription.status == SubscriptionStatus.ACTIVE:
            return self.subscription.plan
        return None  # Default to free plan
    
    def is_within_limits(self, resource_type: str, current_usage: int = 0):
        plan = self.get_current_plan()
        if not plan:
            plan_config = PLAN_CONFIGS[PlanTier.FREE]
            if resource_type == "projects":
                return plan_config["max_projects"] == -1 or current_usage < plan_config["max_projects"]
            elif resource_type == "minutes":
                return plan_config["max_minutes_per_month"] == -1 or current_usage < plan_config["max_minutes_per_month"]
            elif resource_type == "team_members":
                return plan_config["max_team_members"] == -1 or current_usage < plan_config["max_team_members"]
            elif resource_type == "concurrent_deployments":
                return plan_config["max_concurrent_deployments"] == -1 or current_usage < plan_config["max_concurrent_deployments"]
        else:
            if resource_type == "projects":
                return plan.max_projects == -1 or current_usage < plan.max_projects
            elif resource_type == "minutes":
                return plan.max_minutes_per_month == -1 or current_usage < plan.max_minutes_per_month
            elif resource_type == "team_members":
                return plan.max_team_members == -1 or current_usage < plan.max_team_members
            elif resource_type == "concurrent_deployments":
                return plan.max_concurrent_deployments == -1 or current_usage < plan.max_concurrent_deployments
        
        return True
    
    Organization.get_current_plan = get_current_plan
    Organization.is_within_limits = is_within_limits
