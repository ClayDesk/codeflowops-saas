"""
User Sync Monitoring Service
Detects and reports Cognito-Database synchronization issues
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio

from ..utils.database import get_db_context
from ..models.enhanced_models import User, Customer, Subscription
from ..auth.providers.cognito import CognitoAuthProvider

logger = logging.getLogger(__name__)

class UserSyncMonitor:
    """Monitor and detect user synchronization issues"""
    
    def __init__(self):
        self.cognito_provider = None
        try:
            self.cognito_provider = CognitoAuthProvider()
        except Exception as e:
            logger.warning(f"Could not initialize Cognito provider for monitoring: {e}")
    
    async def check_sync_health(self) -> Dict[str, Any]:
        """
        Comprehensive health check for user synchronization.
        
        Returns:
            Dict: Health status and statistics
        """
        try:
            health_report = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "healthy",
                "issues": [],
                "statistics": {},
                "recommendations": []
            }
            
            # 1. Database connectivity check
            try:
                with get_db_context() as db:
                    db.execute("SELECT 1").fetchone()
                health_report["statistics"]["database_connected"] = True
            except Exception as e:
                health_report["overall_status"] = "unhealthy"
                health_report["issues"].append({
                    "type": "database_connectivity",
                    "severity": "critical",
                    "message": f"Database connection failed: {str(e)}"
                })
                return health_report
            
            # 2. User statistics
            user_stats = await self._get_user_statistics()
            health_report["statistics"].update(user_stats)
            
            # 3. Check for orphaned authentication (users who can login but no DB record)
            # This would require Cognito access which may not be available in monitoring
            
            # 4. Check for missing customer records
            missing_customers = await self._check_missing_customer_records()
            if missing_customers:
                health_report["issues"].append({
                    "type": "missing_customer_records",
                    "severity": "medium",
                    "count": len(missing_customers),
                    "message": f"{len(missing_customers)} users missing customer records",
                    "affected_users": missing_customers[:5]  # Show first 5
                })
                
                health_report["recommendations"].append(
                    "Create customer records for users missing them to enable subscription features"
                )
            
            # 5. Check for subscription inconsistencies
            subscription_issues = await self._check_subscription_consistency()
            if subscription_issues:
                health_report["issues"].extend(subscription_issues)
            
            # 6. Check recent sync failures from logs
            recent_failures = await self._check_recent_sync_failures()
            if recent_failures:
                health_report["issues"].append({
                    "type": "recent_sync_failures",
                    "severity": "medium",
                    "count": len(recent_failures),
                    "message": f"{len(recent_failures)} sync failures in last 24 hours"
                })
            
            # Set overall status based on issues
            if any(issue["severity"] == "critical" for issue in health_report["issues"]):
                health_report["overall_status"] = "critical"
            elif health_report["issues"]:
                health_report["overall_status"] = "degraded"
            
            return health_report
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "overall_status": "error",
                "error": str(e)
            }
    
    async def _get_user_statistics(self) -> Dict[str, Any]:
        """Get user-related statistics"""
        try:
            with get_db_context() as db:
                # Basic user counts
                total_users = db.query(User).count()
                active_users = db.query(User).filter(User.is_active == True).count()
                
                # Customer counts
                total_customers = db.query(Customer).count()
                
                # Subscription counts
                total_subscriptions = db.query(Subscription).count()
                active_subscriptions = db.query(Subscription).filter(
                    Subscription.status.in_(["ACTIVE", "TRIALING"])
                ).count()
                
                # Recent activity (last 7 days)
                week_ago = datetime.utcnow() - timedelta(days=7)
                recent_users = db.query(User).filter(
                    User.created_at >= week_ago
                ).count()
                
                return {
                    "total_users": total_users,
                    "active_users": active_users,
                    "total_customers": total_customers,
                    "total_subscriptions": total_subscriptions,
                    "active_subscriptions": active_subscriptions,
                    "recent_users": recent_users,
                    "user_to_customer_ratio": round(total_customers / total_users * 100, 2) if total_users > 0 else 0,
                    "customer_to_subscription_ratio": round(total_subscriptions / total_customers * 100, 2) if total_customers > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return {"error": str(e)}
    
    async def _check_missing_customer_records(self) -> List[Dict[str, str]]:
        """Find users without customer records"""
        try:
            with get_db_context() as db:
                # Find users who don't have customer records
                users_without_customers = db.query(User).outerjoin(Customer).filter(
                    Customer.id.is_(None)
                ).all()
                
                return [
                    {
                        "user_id": user.user_id,
                        "email": user.email,
                        "created_at": user.created_at.isoformat() if user.created_at else None
                    }
                    for user in users_without_customers
                ]
                
        except Exception as e:
            logger.error(f"Error checking missing customer records: {str(e)}")
            return []
    
    async def _check_subscription_consistency(self) -> List[Dict[str, Any]]:
        """Check for subscription-related inconsistencies"""
        issues = []
        
        try:
            with get_db_context() as db:
                # Check for subscriptions without valid customers
                invalid_subscriptions = db.query(Subscription).outerjoin(Customer).filter(
                    Customer.id.is_(None)
                ).count()
                
                if invalid_subscriptions > 0:
                    issues.append({
                        "type": "orphaned_subscriptions",
                        "severity": "high",
                        "count": invalid_subscriptions,
                        "message": f"{invalid_subscriptions} subscriptions without valid customer records"
                    })
                
                # Check for expired trials that haven't been cleaned up
                expired_trials = db.query(Subscription).filter(
                    Subscription.status == "TRIALING",
                    Subscription.trial_end < datetime.utcnow()
                ).count()
                
                if expired_trials > 0:
                    issues.append({
                        "type": "expired_trials",
                        "severity": "low",
                        "count": expired_trials,
                        "message": f"{expired_trials} expired trial subscriptions need cleanup"
                    })
                
        except Exception as e:
            logger.error(f"Error checking subscription consistency: {str(e)}")
            issues.append({
                "type": "subscription_check_error",
                "severity": "medium",
                "message": f"Could not check subscription consistency: {str(e)}"
            })
        
        return issues
    
    async def _check_recent_sync_failures(self) -> List[Dict[str, str]]:
        """Check for recent synchronization failures from logs"""
        # This would typically check log files or a logging database
        # For now, return empty list as we don't have centralized logging
        return []
    
    async def fix_sync_issues(self, issue_types: List[str] = None) -> Dict[str, Any]:
        """
        Attempt to fix common synchronization issues.
        
        Args:
            issue_types: List of issue types to fix (if None, fix all)
            
        Returns:
            Dict: Results of fix attempts
        """
        fix_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "fixes_attempted": [],
            "fixes_successful": [],
            "fixes_failed": []
        }
        
        try:
            # Fix missing customer records
            if not issue_types or "missing_customer_records" in issue_types:
                result = await self._fix_missing_customer_records()
                fix_results["fixes_attempted"].append("missing_customer_records")
                
                if result["success"]:
                    fix_results["fixes_successful"].append({
                        "type": "missing_customer_records",
                        "count": result["fixed_count"],
                        "message": f"Created {result['fixed_count']} missing customer records"
                    })
                else:
                    fix_results["fixes_failed"].append({
                        "type": "missing_customer_records",
                        "error": result["error"]
                    })
            
            return fix_results
            
        except Exception as e:
            logger.error(f"Error during sync issue fixes: {str(e)}")
            fix_results["error"] = str(e)
            return fix_results
    
    async def _fix_missing_customer_records(self) -> Dict[str, Any]:
        """Create customer records for users who are missing them"""
        try:
            from ..services.enhanced_subscription_flow import EnhancedSubscriptionFlow
            
            missing_customers = await self._check_missing_customer_records()
            fixed_count = 0
            
            for user_info in missing_customers:
                try:
                    customer = await EnhancedSubscriptionFlow.ensure_customer_record(
                        user_id=user_info["user_id"],
                        email=user_info["email"]
                    )
                    
                    if customer:
                        fixed_count += 1
                        logger.info(f"Created customer record for user {user_info['email']}")
                    
                except Exception as e:
                    logger.error(f"Failed to create customer record for {user_info['email']}: {e}")
            
            return {
                "success": True,
                "fixed_count": fixed_count,
                "total_missing": len(missing_customers)
            }
            
        except Exception as e:
            logger.error(f"Error fixing missing customer records: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


# Global monitor instance
sync_monitor = UserSyncMonitor()