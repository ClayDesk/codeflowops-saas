"""
Deployment Run Quota Manager for CodeFlowOps
Implements monthly deployment run limits based on subscription plan
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class PlanLimits:
    """Plan limits based on subscription tier"""
    monthly_runs: int
    concurrent_runs: int
    plan_name: str

class DeploymentQuotaManager:
    """Manages deployment run quotas and enforcement"""
    
    def __init__(self):
        # Plan limits aligned with user pricing model
        self.plan_limits = {
            'free': PlanLimits(
                monthly_runs=3,
                concurrent_runs=1,
                plan_name='Free'
            ),
            'starter': PlanLimits(
                monthly_runs=50,  # Generous limit for $19/month
                concurrent_runs=2,
                plan_name='Starter'
            ),
            'pro': PlanLimits(
                monthly_runs=200,  # Generous limit for $49/month
                concurrent_runs=5,
                plan_name='Pro'
            ),
            'enterprise': PlanLimits(
                monthly_runs=-1,  # Unlimited
                concurrent_runs=10,
                plan_name='Enterprise'
            )
        }
    
    def get_plan_limits(self, plan_tier: str) -> PlanLimits:
        """Get limits for a specific plan"""
        return self.plan_limits.get(plan_tier.lower(), self.plan_limits['free'])
    
    def check_monthly_quota(self, user_id: str, plan_tier: str, current_runs: int) -> Tuple[bool, str]:
        """
        Check if user can create another deployment this month
        
        Args:
            user_id: User identifier
            plan_tier: Current subscription plan (free, starter, pro, enterprise)
            current_runs: Number of runs this month
        
        Returns:
            (can_deploy: bool, reason: str)
        """
        limits = self.get_plan_limits(plan_tier)
        
        # Unlimited plans
        if limits.monthly_runs == -1:
            return True, "Unlimited runs available"
        
        # Check if under limit
        if current_runs < limits.monthly_runs:
            remaining = limits.monthly_runs - current_runs
            return True, f"{remaining} runs remaining this month"
        
        # Over limit
        return False, f"Monthly limit reached ({limits.monthly_runs} runs). Upgrade for more runs."
    
    def check_concurrent_quota(self, user_id: str, plan_tier: str, active_runs: int) -> Tuple[bool, str]:
        """
        Check if user can start a concurrent deployment
        
        Args:
            user_id: User identifier
            plan_tier: Current subscription plan
            active_runs: Number of currently active deployments
        
        Returns:
            (can_deploy: bool, reason: str)
        """
        limits = self.get_plan_limits(plan_tier)
        
        if active_runs < limits.concurrent_runs:
            return True, f"Can run {limits.concurrent_runs - active_runs} more concurrent deployments"
        
        return False, f"Concurrent limit reached ({limits.concurrent_runs}). Wait for deployments to complete."
    
    def get_quota_status(self, user_id: str, plan_tier: str, current_runs: int, active_runs: int) -> Dict:
        """
        Get comprehensive quota status for user
        
        Returns detailed quota information for frontend display
        """
        limits = self.get_plan_limits(plan_tier)
        
        # Monthly runs status
        monthly_unlimited = limits.monthly_runs == -1
        monthly_percentage = 0 if monthly_unlimited else round((current_runs / limits.monthly_runs) * 100, 1)
        monthly_remaining = "unlimited" if monthly_unlimited else max(0, limits.monthly_runs - current_runs)
        
        # Concurrent runs status
        concurrent_percentage = round((active_runs / limits.concurrent_runs) * 100, 1)
        concurrent_remaining = max(0, limits.concurrent_runs - active_runs)
        
        # Overall deployment availability
        can_deploy_monthly, monthly_reason = self.check_monthly_quota(user_id, plan_tier, current_runs)
        can_deploy_concurrent, concurrent_reason = self.check_concurrent_quota(user_id, plan_tier, active_runs)
        can_deploy = can_deploy_monthly and can_deploy_concurrent
        
        return {
            "plan": {
                "tier": plan_tier,
                "name": limits.plan_name
            },
            "monthly_runs": {
                "used": current_runs,
                "limit": limits.monthly_runs if not monthly_unlimited else "unlimited",
                "remaining": monthly_remaining,
                "percentage": monthly_percentage,
                "unlimited": monthly_unlimited
            },
            "concurrent_runs": {
                "active": active_runs,
                "limit": limits.concurrent_runs,
                "remaining": concurrent_remaining,
                "percentage": concurrent_percentage
            },
            "deployment_allowed": {
                "can_deploy": can_deploy,
                "monthly_check": {
                    "passed": can_deploy_monthly,
                    "reason": monthly_reason
                },
                "concurrent_check": {
                    "passed": can_deploy_concurrent,
                    "reason": concurrent_reason
                }
            },
            "upgrade_suggestion": self._get_upgrade_suggestion(plan_tier, current_runs, monthly_percentage)
        }
    
    def _get_upgrade_suggestion(self, current_plan: str, current_runs: int, usage_percentage: float) -> Optional[str]:
        """Generate upgrade suggestions based on usage"""
        if current_plan == 'free':
            if usage_percentage >= 80:
                return "Consider upgrading to Starter for 50 runs/month"
        elif current_plan == 'starter':
            if usage_percentage >= 80:
                return "Consider upgrading to Pro for 200 runs/month"
        elif current_plan == 'pro':
            if usage_percentage >= 80:
                return "Consider Enterprise for unlimited deployments"
        
        return None

# Global instance
deployment_quota_manager = DeploymentQuotaManager()
