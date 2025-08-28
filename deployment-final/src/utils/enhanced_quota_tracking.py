# Enhanced Quota Tracking with Billing Integration
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from sqlalchemy.orm import Session
from dataclasses import dataclass

from ..models.billing_models import (
    OrganizationSubscription, BillingPlan, PlanTier, SubscriptionStatus,
    PLAN_CONFIGS
)
from ..models.enhanced_models import Organization, User, Project, DeploymentHistory
from ..utils.database import get_db_session

@dataclass
class QuotaLimits:
    """Structure for quota limits based on billing plan"""
    max_projects: int
    max_minutes_per_month: int
    max_team_members: int
    max_concurrent_deployments: int
    max_storage_gb: int = 10  # Default storage limit
    
    def is_unlimited(self, resource: str) -> bool:
        """Check if a resource is unlimited (-1)"""
        return getattr(self, f"max_{resource}", 0) == -1

@dataclass
class QuotaUsage:
    """Current usage statistics"""
    projects_count: int
    minutes_used_this_month: int
    team_members_count: int
    active_deployments: int
    storage_used_gb: float

class EnhancedQuotaManager:
    """
    Enhanced quota manager with billing plan integration
    """
    
    def __init__(self):
        self.plan_limits = {
            PlanTier.FREE: QuotaLimits(
                max_projects=3,
                max_minutes_per_month=100,
                max_team_members=1,
                max_concurrent_deployments=1,
                max_storage_gb=5
            ),
            PlanTier.STARTER: QuotaLimits(
                max_projects=10,
                max_minutes_per_month=400,
                max_team_members=3,
                max_concurrent_deployments=2,
                max_storage_gb=25
            ),
            PlanTier.PRO: QuotaLimits(
                max_projects=-1,  # Unlimited
                max_minutes_per_month=3000,
                max_team_members=10,
                max_concurrent_deployments=5,
                max_storage_gb=100
            ),
            PlanTier.ENTERPRISE: QuotaLimits(
                max_projects=-1,  # Unlimited
                max_minutes_per_month=-1,  # Unlimited
                max_team_members=-1,  # Unlimited
                max_concurrent_deployments=-1,  # Unlimited
                max_storage_gb=-1  # Unlimited
            )
        }
    
    def get_organization_plan(self, db: Session, organization_id: str) -> PlanTier:
        """Get the current billing plan for an organization"""
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.organization_id == organization_id,
            OrganizationSubscription.status.in_([
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.TRIALING
            ])
        ).first()
        
        if subscription:
            return subscription.plan.tier
        
        return PlanTier.FREE  # Default to free plan
    
    def get_quota_limits(self, db: Session, organization_id: str) -> QuotaLimits:
        """Get quota limits for an organization based on their billing plan"""
        plan_tier = self.get_organization_plan(db, organization_id)
        return self.plan_limits[plan_tier]
    
    def get_current_usage(self, db: Session, organization_id: str) -> QuotaUsage:
        """Get current usage statistics for an organization"""
        current_month = datetime.utcnow().strftime("%Y-%m")
        
        # Count projects
        projects_count = db.query(Project).filter(
            Project.organization_id == organization_id,
            Project.is_active == True
        ).count()
        
        # Count team members
        team_members_count = db.query(User).filter(
            User.organization_id == organization_id,
            User.is_active == True
        ).count()
        
        # Get minutes used this month from subscription record
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.organization_id == organization_id
        ).first()
        
        minutes_used = subscription.current_month_minutes_used if subscription else 0
        
        # Count active deployments
        active_deployments = db.query(DeploymentHistory).filter(
            DeploymentHistory.organization_id == organization_id,
            DeploymentHistory.status.in_(['pending', 'running', 'deploying'])
        ).count()
        
        # Calculate storage used (placeholder - would need actual implementation)
        storage_used_gb = 0.0  # This would integrate with S3 usage tracking
        
        return QuotaUsage(
            projects_count=projects_count,
            minutes_used_this_month=minutes_used,
            team_members_count=team_members_count,
            active_deployments=active_deployments,
            storage_used_gb=storage_used_gb
        )
    
    def check_resource_quota(
        self, 
        db: Session, 
        organization_id: str, 
        resource_type: str,
        requested_quantity: int = 1
    ) -> Tuple[bool, str, Dict]:
        """
        Check if organization can use additional resources
        Returns: (allowed, reason, details)
        """
        limits = self.get_quota_limits(db, organization_id)
        usage = self.get_current_usage(db, organization_id)
        plan_tier = self.get_organization_plan(db, organization_id)
        
        # Check specific resource types
        if resource_type == "projects":
            if limits.is_unlimited("projects"):
                return True, "Unlimited projects", {"usage": usage.projects_count, "limit": "unlimited"}
            
            if usage.projects_count + requested_quantity > limits.max_projects:
                return False, f"Project limit exceeded. Current: {usage.projects_count}, Limit: {limits.max_projects}", {
                    "usage": usage.projects_count,
                    "limit": limits.max_projects,
                    "suggested_plan": self._suggest_upgrade_plan(plan_tier)
                }
        
        elif resource_type == "minutes":
            if limits.is_unlimited("minutes_per_month"):
                return True, "Unlimited minutes", {"usage": usage.minutes_used_this_month, "limit": "unlimited"}
            
            if usage.minutes_used_this_month + requested_quantity > limits.max_minutes_per_month:
                return False, f"Monthly minutes limit exceeded. Current: {usage.minutes_used_this_month}, Limit: {limits.max_minutes_per_month}", {
                    "usage": usage.minutes_used_this_month,
                    "limit": limits.max_minutes_per_month,
                    "reset_date": self._get_next_reset_date(db, organization_id),
                    "suggested_plan": self._suggest_upgrade_plan(plan_tier)
                }
        
        elif resource_type == "team_members":
            if limits.is_unlimited("team_members"):
                return True, "Unlimited team members", {"usage": usage.team_members_count, "limit": "unlimited"}
            
            if usage.team_members_count + requested_quantity > limits.max_team_members:
                return False, f"Team member limit exceeded. Current: {usage.team_members_count}, Limit: {limits.max_team_members}", {
                    "usage": usage.team_members_count,
                    "limit": limits.max_team_members,
                    "suggested_plan": self._suggest_upgrade_plan(plan_tier)
                }
        
        elif resource_type == "concurrent_deployments":
            if limits.is_unlimited("concurrent_deployments"):
                return True, "Unlimited concurrent deployments", {"usage": usage.active_deployments, "limit": "unlimited"}
            
            if usage.active_deployments + requested_quantity > limits.max_concurrent_deployments:
                return False, f"Concurrent deployment limit exceeded. Current: {usage.active_deployments}, Limit: {limits.max_concurrent_deployments}", {
                    "usage": usage.active_deployments,
                    "limit": limits.max_concurrent_deployments,
                    "suggested_plan": self._suggest_upgrade_plan(plan_tier)
                }
        
        elif resource_type == "storage":
            if limits.is_unlimited("storage_gb"):
                return True, "Unlimited storage", {"usage": usage.storage_used_gb, "limit": "unlimited"}
            
            if usage.storage_used_gb + requested_quantity > limits.max_storage_gb:
                return False, f"Storage limit exceeded. Current: {usage.storage_used_gb:.2f}GB, Limit: {limits.max_storage_gb}GB", {
                    "usage": usage.storage_used_gb,
                    "limit": limits.max_storage_gb,
                    "suggested_plan": self._suggest_upgrade_plan(plan_tier)
                }
        
        return True, "Within quota limits", {"usage": 0, "limit": "unknown"}
    
    def consume_quota(
        self, 
        db: Session, 
        organization_id: str, 
        resource_type: str, 
        quantity: int,
        metadata: Dict = None
    ):
        """
        Consume quota and record usage event
        """
        # Check if consumption is allowed
        allowed, reason, details = self.check_resource_quota(db, organization_id, resource_type, quantity)
        
        if not allowed:
            raise ValueError(f"Quota exceeded: {reason}")
        
        # Usage event recording removed (Stripe functionality removed)
        # Basic quota tracking continues without billing integration
        
        # Update subscription usage counters
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.organization_id == organization_id
        ).first()
        
        if subscription:
            if resource_type == "minutes":
                subscription.current_month_minutes_used += quantity
            elif resource_type == "projects":
                subscription.current_month_projects_count += quantity
            
            db.commit()
    
    def get_quota_summary(self, db: Session, organization_id: str) -> Dict:
        """
        Get comprehensive quota summary for organization
        """
        plan_tier = self.get_organization_plan(db, organization_id)
        limits = self.get_quota_limits(db, organization_id)
        usage = self.get_current_usage(db, organization_id)
        
        # Calculate usage percentages
        def calc_percentage(used, limit):
            if limit == -1:  # Unlimited
                return 0
            return min(100, (used / limit) * 100) if limit > 0 else 0
        
        return {
            "plan": {
                "name": plan_tier.value.title(),
                "tier": plan_tier.value
            },
            "limits": {
                "projects": {
                    "used": usage.projects_count,
                    "limit": limits.max_projects,
                    "unlimited": limits.is_unlimited("projects"),
                    "percentage": calc_percentage(usage.projects_count, limits.max_projects)
                },
                "minutes": {
                    "used": usage.minutes_used_this_month,
                    "limit": limits.max_minutes_per_month,
                    "unlimited": limits.is_unlimited("minutes_per_month"),
                    "percentage": calc_percentage(usage.minutes_used_this_month, limits.max_minutes_per_month),
                    "reset_date": self._get_next_reset_date(db, organization_id)
                },
                "team_members": {
                    "used": usage.team_members_count,
                    "limit": limits.max_team_members,
                    "unlimited": limits.is_unlimited("team_members"),
                    "percentage": calc_percentage(usage.team_members_count, limits.max_team_members)
                },
                "concurrent_deployments": {
                    "used": usage.active_deployments,
                    "limit": limits.max_concurrent_deployments,
                    "unlimited": limits.is_unlimited("concurrent_deployments"),
                    "percentage": calc_percentage(usage.active_deployments, limits.max_concurrent_deployments)
                },
                "storage": {
                    "used": usage.storage_used_gb,
                    "limit": limits.max_storage_gb,
                    "unlimited": limits.is_unlimited("storage_gb"),
                    "percentage": calc_percentage(usage.storage_used_gb, limits.max_storage_gb),
                    "unit": "GB"
                }
            },
            "warnings": self._get_quota_warnings(limits, usage),
            "upgrade_suggestions": self._get_upgrade_suggestions(plan_tier, limits, usage)
        }
    
    def _suggest_upgrade_plan(self, current_plan: PlanTier) -> Optional[str]:
        """Suggest the next plan tier for upgrade"""
        upgrade_path = {
            PlanTier.FREE: "starter",
            PlanTier.STARTER: "pro",
            PlanTier.PRO: "enterprise"
        }
        return upgrade_path.get(current_plan)
    
    def _get_next_reset_date(self, db: Session, organization_id: str) -> Optional[str]:
        """Get the next billing cycle reset date"""
        subscription = db.query(OrganizationSubscription).filter(
            OrganizationSubscription.organization_id == organization_id
        ).first()
        
        if subscription and subscription.current_period_end:
            return subscription.current_period_end.isoformat()
        
        # For free plans, reset on first of next month
        next_month = datetime.utcnow().replace(day=1) + timedelta(days=32)
        return next_month.replace(day=1).isoformat()
    
    def _get_quota_warnings(self, limits: QuotaLimits, usage: QuotaUsage) -> List[str]:
        """Generate warnings for resources approaching limits"""
        warnings = []
        
        # Check each resource at 80% and 90% thresholds
        resources = [
            ("projects", usage.projects_count, limits.max_projects),
            ("minutes", usage.minutes_used_this_month, limits.max_minutes_per_month),
            ("team_members", usage.team_members_count, limits.max_team_members),
            ("storage", usage.storage_used_gb, limits.max_storage_gb)
        ]
        
        for resource_name, used, limit in resources:
            if limit > 0:  # Not unlimited
                percentage = (used / limit) * 100
                if percentage >= 90:
                    warnings.append(f"{resource_name.replace('_', ' ').title()} usage is at {percentage:.0f}% of limit")
                elif percentage >= 80:
                    warnings.append(f"{resource_name.replace('_', ' ').title()} usage is at {percentage:.0f}% of limit")
        
        return warnings
    
    def _get_upgrade_suggestions(self, plan_tier: PlanTier, limits: QuotaLimits, usage: QuotaUsage) -> List[str]:
        """Generate upgrade suggestions based on usage patterns"""
        suggestions = []
        
        if plan_tier == PlanTier.FREE:
            if usage.projects_count >= 2:
                suggestions.append("Upgrade to Starter for 10 projects and more build minutes")
            if usage.minutes_used_this_month >= 80:
                suggestions.append("Upgrade to Starter for 400 minutes per month")
        
        elif plan_tier == PlanTier.STARTER:
            if usage.projects_count >= 8:
                suggestions.append("Upgrade to Pro for unlimited projects")
            if usage.minutes_used_this_month >= 320:  # 80% of 400
                suggestions.append("Upgrade to Pro for 3000 minutes per month")
            if usage.team_members_count >= 3:
                suggestions.append("Upgrade to Pro for up to 10 team members")
        
        elif plan_tier == PlanTier.PRO:
            if usage.minutes_used_this_month >= 2400:  # 80% of 3000
                suggestions.append("Contact us for Enterprise plan with unlimited build minutes")
            if usage.team_members_count >= 8:
                suggestions.append("Contact us for Enterprise plan with unlimited team members")
        
        return suggestions

# Global instance
enhanced_quota_manager = EnhancedQuotaManager()
