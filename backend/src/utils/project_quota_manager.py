"""
Simplified Project-Based Quota Management
Tracks and enforces project limits only
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.enhanced_models import User, Organization, DeploymentHistory
from ..models.billing_models import OrganizationSubscription, PlanTier, PLAN_CONFIGS

logger = logging.getLogger(__name__)


class ProjectQuotaManager:
    """Manages project quotas and usage tracking"""
    
    def __init__(self):
        self.db_manager = None
    
    def get_project_count(self, session: Session, organization_id: str) -> int:
        """Get current project count for organization"""
        try:
            # Count active projects/deployments for this organization
            # This could be based on unique repository URLs or project names
            project_count = session.query(DeploymentHistory).filter(
                DeploymentHistory.organization_id == organization_id,
                DeploymentHistory.status.in_(['completed', 'active', 'deployed'])
            ).distinct(DeploymentHistory.repository_url).count()
            
            return project_count
        except Exception as e:
            logger.error(f"Failed to get project count: {e}")
            return 0
    
    def get_plan_limits(self, session: Session, organization_id: str) -> Dict[str, Any]:
        """Get plan limits for organization"""
        try:
            # Get active subscription
            subscription = session.query(OrganizationSubscription).filter(
                OrganizationSubscription.organization_id == organization_id,
                OrganizationSubscription.status == 'active'
            ).first()
            
            if not subscription:
                # Default to free plan
                return PLAN_CONFIGS[PlanTier.FREE]
            
            # Get plan configuration
            plan_tier = subscription.plan.tier
            return PLAN_CONFIGS[plan_tier]
            
        except Exception as e:
            logger.error(f"Failed to get plan limits: {e}")
            return PLAN_CONFIGS[PlanTier.FREE]
    
    def can_create_project(self, session: Session, organization_id: str) -> Tuple[bool, str]:
        """Check if organization can create another project"""
        try:
            current_count = self.get_project_count(session, organization_id)
            plan_config = self.get_plan_limits(session, organization_id)
            
            max_projects = plan_config["max_projects"]
            
            # -1 means unlimited
            if max_projects == -1:
                return True, "Unlimited projects"
            
            if current_count >= max_projects:
                plan_name = plan_config["name"]
                return False, f"Project limit reached. {plan_name} plan allows {max_projects} projects. You have {current_count}."
            
            remaining = max_projects - current_count
            return True, f"{remaining} projects remaining"
            
        except Exception as e:
            logger.error(f"Failed to check project quota: {e}")
            return False, "Failed to check quota"
    
    def get_usage_summary(self, session: Session, organization_id: str) -> Dict[str, Any]:
        """Get current usage summary for organization"""
        try:
            current_count = self.get_project_count(session, organization_id)
            plan_config = self.get_plan_limits(session, organization_id)
            
            max_projects = plan_config["max_projects"]
            plan_name = plan_config["name"]
            
            if max_projects == -1:
                usage_percentage = 0  # Unlimited
                remaining = -1
            else:
                usage_percentage = round((current_count / max_projects * 100), 1) if max_projects > 0 else 0
                remaining = max_projects - current_count
            
            return {
                "plan_name": plan_name,
                "plan_tier": plan_config["tier"].value,
                "projects": {
                    "used": current_count,
                    "limit": max_projects,
                    "percentage": usage_percentage,
                    "remaining": remaining
                },
                "team_members": {
                    "used": 1,  # TODO: Calculate actual team member count
                    "limit": plan_config["max_team_members"],
                    "percentage": 0,
                    "remaining": plan_config["max_team_members"] - 1
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            return {
                "plan_name": "Free",
                "plan_tier": "free",
                "projects": {"used": 0, "limit": 3, "percentage": 0, "remaining": 3},
                "team_members": {"used": 1, "limit": 1, "percentage": 100, "remaining": 0}
            }
    
    def record_project_creation(self, session: Session, organization_id: str, project_name: str, repository_url: str):
        """Record a new project creation"""
        try:
            # This would be called when a project is successfully deployed
            # The actual recording happens via DeploymentHistory creation
            # This method can be used for additional tracking if needed
            
            logger.info(f"Project created for organization {organization_id}: {project_name}")
            
            # Update subscription project count if needed
            subscription = session.query(OrganizationSubscription).filter(
                OrganizationSubscription.organization_id == organization_id,
                OrganizationSubscription.status == 'active'
            ).first()
            
            if subscription:
                subscription.current_month_projects_count = self.get_project_count(session, organization_id)
                session.commit()
                
        except Exception as e:
            logger.error(f"Failed to record project creation: {e}")


# Global instance
project_quota_manager = ProjectQuotaManager()
