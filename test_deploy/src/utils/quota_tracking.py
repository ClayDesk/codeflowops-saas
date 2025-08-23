"""
Quota tracking and enforcement system
Monitors usage against plan limits
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.enhanced_models import User, Organization, Usage, DeploymentHistory
from database.connection import get_database_manager

logger = logging.getLogger(__name__)


class QuotaManager:
    """Manages user quotas and usage tracking"""
    
    def __init__(self):
        self.db_manager = None
    
    async def initialize(self):
        """Initialize database connection"""
        if not self.db_manager:
            self.db_manager = await get_database_manager()
    
    async def check_deployment_quota(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user can create a new deployment
        
        Returns:
            (can_deploy: bool, reason: str)
        """
        await self.initialize()
        
        try:
            with self.db_manager.get_session() as session:
                # Get user with organization
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    return False, "User not found"
                
                if not user.organization:
                    return False, "User not associated with an organization"
                
                # Check monthly deployment limit
                current_month_deployments = await self._get_current_month_usage(
                    session, user_id, "deployments"
                )
                
                if current_month_deployments >= user.organization.monthly_deployment_limit:
                    return False, f"Monthly deployment limit reached ({user.organization.monthly_deployment_limit})"
                
                # Check concurrent deployment limit
                active_deployments = await self._get_active_deployments_count(session, user_id)
                
                if active_deployments >= user.organization.concurrent_deployment_limit:
                    return False, f"Concurrent deployment limit reached ({user.organization.concurrent_deployment_limit})"
                
                return True, "Quota available"
                
        except Exception as e:
            logger.error(f"Failed to check deployment quota: {e}")
            return False, "Failed to check quota"
    
    async def check_build_minutes_quota(self, user_id: str, estimated_minutes: int) -> Tuple[bool, str]:
        """Check if user has enough build minutes remaining"""
        await self.initialize()
        
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user or not user.organization:
                    return False, "User or organization not found"
                
                current_usage = await self._get_current_month_usage(
                    session, user_id, "build_minutes"
                )
                
                if (current_usage + estimated_minutes) > user.organization.build_minutes_limit:
                    remaining = user.organization.build_minutes_limit - current_usage
                    return False, f"Insufficient build minutes. Need {estimated_minutes}, have {remaining} remaining"
                
                return True, "Build minutes available"
                
        except Exception as e:
            logger.error(f"Failed to check build minutes quota: {e}")
            return False, "Failed to check quota"
    
    async def check_storage_quota(self, user_id: str, additional_gb: float) -> Tuple[bool, str]:
        """Check if user has enough storage quota"""
        await self.initialize()
        
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user or not user.organization:
                    return False, "User or organization not found"
                
                current_storage = user.storage_used_gb or 0
                
                if (current_storage + additional_gb) > user.organization.storage_limit_gb:
                    remaining = user.organization.storage_limit_gb - current_storage
                    return False, f"Insufficient storage. Need {additional_gb}GB, have {remaining}GB remaining"
                
                return True, "Storage available"
                
        except Exception as e:
            logger.error(f"Failed to check storage quota: {e}")
            return False, "Failed to check quota"
    
    async def record_deployment_usage(
        self, 
        user_id: str, 
        deployment_id: str,
        build_minutes: int = 0,
        storage_gb: float = 0.0
    ):
        """Record usage when deployment starts"""
        await self.initialize()
        
        try:
            with self.db_manager.get_session() as session:
                # Update user's current month counters
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.current_month_deployments = (user.current_month_deployments or 0) + 1
                    user.current_month_build_minutes = (user.current_month_build_minutes or 0) + build_minutes
                    user.storage_used_gb = (user.storage_used_gb or 0) + storage_gb
                
                # Update or create usage record
                await self._update_usage_record(session, user_id, {
                    'deployments_count': 1,
                    'build_minutes_used': build_minutes,
                    'storage_gb_hours': storage_gb  # Will be calculated properly later
                })
                
                session.commit()
                logger.info(f"Recorded deployment usage for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to record deployment usage: {e}")
            raise
    
    async def record_destroy_usage(self, user_id: str, storage_gb_freed: float):
        """Record usage when deployment is destroyed"""
        await self.initialize()
        
        try:
            with self.db_manager.get_session() as session:
                # Update user's storage counter
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.storage_used_gb = max(0, (user.storage_used_gb or 0) - storage_gb_freed)
                
                session.commit()
                logger.info(f"Updated storage usage after destroy for user {user_id}")
                
        except Exception as e:
            logger.error(f"Failed to record destroy usage: {e}")
            raise
    
    async def get_user_quota_status(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive quota status for a user"""
        await self.initialize()
        
        try:
            with self.db_manager.get_session() as session:
                user = session.query(User).filter(User.id == user_id).first()
                if not user or not user.organization:
                    return {"error": "User or organization not found"}
                
                org = user.organization
                
                # Get current month usage
                deployments_used = await self._get_current_month_usage(session, user_id, "deployments")
                build_minutes_used = await self._get_current_month_usage(session, user_id, "build_minutes")
                storage_used = user.storage_used_gb or 0
                active_deployments = await self._get_active_deployments_count(session, user_id)
                
                return {
                    "user_id": user_id,
                    "organization": {
                        "name": org.name,
                        "plan_type": org.plan_type
                    },
                    "quotas": {
                        "deployments": {
                            "used": deployments_used,
                            "limit": org.monthly_deployment_limit,
                            "percentage": round((deployments_used / org.monthly_deployment_limit * 100), 1) if org.monthly_deployment_limit > 0 else 0,
                            "can_deploy": deployments_used < org.monthly_deployment_limit
                        },
                        "concurrent_deployments": {
                            "used": active_deployments,
                            "limit": org.concurrent_deployment_limit,
                            "percentage": round((active_deployments / org.concurrent_deployment_limit * 100), 1) if org.concurrent_deployment_limit > 0 else 0,
                            "can_deploy": active_deployments < org.concurrent_deployment_limit
                        },
                        "build_minutes": {
                            "used": build_minutes_used,
                            "limit": org.build_minutes_limit,
                            "percentage": round((build_minutes_used / org.build_minutes_limit * 100), 1) if org.build_minutes_limit > 0 else 0,
                            "remaining": max(0, org.build_minutes_limit - build_minutes_used)
                        },
                        "storage": {
                            "used_gb": storage_used,
                            "limit_gb": org.storage_limit_gb,
                            "percentage": round((storage_used / org.storage_limit_gb * 100), 1) if org.storage_limit_gb > 0 else 0,
                            "remaining_gb": max(0, org.storage_limit_gb - storage_used)
                        }
                    },
                    "can_deploy": (
                        deployments_used < org.monthly_deployment_limit and
                        active_deployments < org.concurrent_deployment_limit
                    ),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get quota status: {e}")
            return {"error": "Failed to retrieve quota status"}
    
    async def reset_monthly_quotas(self):
        """Reset monthly quotas for all users (run via cron)"""
        await self.initialize()
        
        try:
            with self.db_manager.get_session() as session:
                # Reset all users' monthly counters
                session.query(User).update({
                    User.current_month_deployments: 0,
                    User.current_month_build_minutes: 0
                })
                
                session.commit()
                logger.info("Reset monthly quotas for all users")
                
        except Exception as e:
            logger.error(f"Failed to reset monthly quotas: {e}")
            raise
    
    async def _get_current_month_usage(
        self, 
        session: Session, 
        user_id: str, 
        metric: str
    ) -> int:
        """Get current month usage for a specific metric"""
        current_date = datetime.utcnow()
        
        usage_record = session.query(Usage).filter(
            Usage.user_id == user_id,
            Usage.year == current_date.year,
            Usage.month == current_date.month
        ).first()
        
        if not usage_record:
            return 0
        
        if metric == "deployments":
            return usage_record.deployments_count or 0
        elif metric == "build_minutes":
            return usage_record.build_minutes_used or 0
        
        return 0
    
    async def _get_active_deployments_count(self, session: Session, user_id: str) -> int:
        """Get count of currently active deployments"""
        return session.query(DeploymentHistory).filter(
            DeploymentHistory.user_id == user_id,
            DeploymentHistory.status.in_(['pending', 'building', 'deploying'])
        ).count()
    
    async def _update_usage_record(
        self, 
        session: Session, 
        user_id: str, 
        usage_data: Dict[str, Any]
    ):
        """Update or create usage record for current month"""
        current_date = datetime.utcnow()
        
        # Get user's organization
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        usage_record = session.query(Usage).filter(
            Usage.user_id == user_id,
            Usage.year == current_date.year,
            Usage.month == current_date.month
        ).first()
        
        if not usage_record:
            usage_record = Usage(
                user_id=user_id,
                organization_id=user.organization_id,
                year=current_date.year,
                month=current_date.month
            )
            session.add(usage_record)
        
        # Update usage data
        for key, value in usage_data.items():
            if hasattr(usage_record, key):
                current_value = getattr(usage_record, key) or 0
                setattr(usage_record, key, current_value + value)


# Global quota manager instance
quota_manager = QuotaManager()
