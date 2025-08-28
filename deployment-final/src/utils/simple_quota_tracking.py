# Simple Quota Tracking for CodeFlowOps
# Removed pricing plans - now uses basic limits for all users

from sqlalchemy.orm import Session
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from ..models.enhanced_models import Organization, User, Project, DeploymentHistory
from ..utils.database import get_db_session

@dataclass
class QuotaLimits:
    """Structure for basic quota limits"""
    max_projects: int
    max_minutes_per_month: int
    max_team_members: int
    max_concurrent_deployments: int
    max_storage_gb: float

@dataclass
class QuotaUsage:
    """Current usage statistics"""
    projects_count: int
    minutes_used_this_month: int
    team_members_count: int
    concurrent_deployments: int
    storage_used_gb: float

class SimpleQuotaTracker:
    """
    Simplified quota tracking without billing plans
    All users get the same basic limits
    """
    
    def __init__(self):
        # Basic limits for all users (generous free limits)
        self.default_limits = QuotaLimits(
            max_projects=50,  # Generous limit
            max_minutes_per_month=1000,  # 1000 minutes per month
            max_team_members=10,  # Up to 10 team members
            max_concurrent_deployments=5,  # 5 concurrent deployments
            max_storage_gb=10.0  # 10 GB storage
        )
    
    def get_organization_limits(self, organization_id: str) -> QuotaLimits:
        """Get quota limits for an organization"""
        return self.default_limits
    
    def get_current_usage(self, db: Session, organization_id: str) -> QuotaUsage:
        """Get current usage for an organization"""
        
        # Count projects
        projects_count = db.query(Project).filter(
            Project.organization_id == organization_id
        ).count()
        
        # Count team members
        team_members_count = db.query(User).join(Organization).filter(
            Organization.id == organization_id
        ).count()
        
        # Calculate minutes used this month
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        minutes_used = db.query(DeploymentHistory).filter(
            DeploymentHistory.organization_id == organization_id,
            DeploymentHistory.created_at >= start_of_month
        ).count() * 5  # Assume 5 minutes per deployment on average
        
        # Count concurrent deployments (simplified)
        concurrent_deployments = db.query(DeploymentHistory).filter(
            DeploymentHistory.organization_id == organization_id,
            DeploymentHistory.status.in_(['pending', 'running'])
        ).count()
        
        return QuotaUsage(
            projects_count=projects_count,
            minutes_used_this_month=minutes_used,
            team_members_count=team_members_count,
            concurrent_deployments=concurrent_deployments,
            storage_used_gb=0.0  # Not tracked in this simplified version
        )
    
    def check_resource_quota(self, db: Session, organization_id: str, resource_type: str, quantity: int = 1) -> tuple[bool, str, Dict[str, Any]]:
        """
        Check if organization can consume the specified resource
        Returns: (allowed: bool, reason: str, details: dict)
        """
        limits = self.get_organization_limits(organization_id)
        current_usage = self.get_current_usage(db, organization_id)
        
        details = {
            "current_usage": current_usage,
            "limits": limits,
            "resource_type": resource_type,
            "requested_quantity": quantity
        }
        
        if resource_type == "project":
            if current_usage.projects_count + quantity > limits.max_projects:
                return False, f"Project limit exceeded. You have {current_usage.projects_count}/{limits.max_projects} projects.", details
        
        elif resource_type == "deployment_minutes":
            if current_usage.minutes_used_this_month + quantity > limits.max_minutes_per_month:
                return False, f"Monthly minute limit exceeded. You have used {current_usage.minutes_used_this_month}/{limits.max_minutes_per_month} minutes this month.", details
        
        elif resource_type == "team_member":
            if current_usage.team_members_count + quantity > limits.max_team_members:
                return False, f"Team member limit exceeded. You have {current_usage.team_members_count}/{limits.max_team_members} team members.", details
        
        elif resource_type == "concurrent_deployment":
            if current_usage.concurrent_deployments + quantity > limits.max_concurrent_deployments:
                return False, f"Concurrent deployment limit exceeded. You have {current_usage.concurrent_deployments}/{limits.max_concurrent_deployments} running deployments.", details
        
        return True, "Resource available", details
    
    def consume_resource(self, db: Session, organization_id: str, resource_type: str, quantity: int = 1, metadata: Optional[Dict] = None):
        """
        Consume a resource after checking quota
        Simplified version without billing integration
        """
        allowed, reason, details = self.check_resource_quota(db, organization_id, resource_type, quantity)
        
        if not allowed:
            raise ValueError(f"Quota exceeded: {reason}")
        
        # Basic quota tracking continues without billing integration
        # In a real implementation, you might want to log this usage
        
        return details
    
    def get_quota_summary(self, db: Session, organization_id: str) -> Dict[str, Any]:
        """Get a summary of quota usage and limits"""
        limits = self.get_organization_limits(organization_id)
        usage = self.get_current_usage(db, organization_id)
        
        return {
            "organization_id": organization_id,
            "plan": "free",  # Everyone gets the same plan now
            "limits": {
                "projects": limits.max_projects,
                "minutes_per_month": limits.max_minutes_per_month,
                "team_members": limits.max_team_members,
                "concurrent_deployments": limits.max_concurrent_deployments,
                "storage_gb": limits.max_storage_gb
            },
            "usage": {
                "projects": usage.projects_count,
                "minutes_this_month": usage.minutes_used_this_month,
                "team_members": usage.team_members_count,
                "concurrent_deployments": usage.concurrent_deployments,
                "storage_gb": usage.storage_used_gb
            },
            "percentage_used": {
                "projects": (usage.projects_count / limits.max_projects) * 100,
                "minutes": (usage.minutes_used_this_month / limits.max_minutes_per_month) * 100,
                "team_members": (usage.team_members_count / limits.max_team_members) * 100,
                "concurrent_deployments": (usage.concurrent_deployments / limits.max_concurrent_deployments) * 100,
                "storage": (usage.storage_used_gb / limits.max_storage_gb) * 100
            }
        }

# Global instance
quota_tracker = SimpleQuotaTracker()
