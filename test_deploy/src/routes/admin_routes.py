"""
Admin Panel API Routes
Provides administrative functionality for CodeFlowOps operations team
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime, timedelta

from ..models.enhanced_models import User, Organization, Team, Project, DeploymentHistory, Usage
from ..utils.job_queue import job_queue, JobStatus
from ..utils.quota_tracking import quota_manager
from ..utils.session_resume import session_resume_manager
from dependencies.session import get_session_manager, SessionManager
from database.connection import get_database_manager
from auth.auth_manager import auth_manager
from sqlalchemy import desc, func, and_, or_

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_admin_access(current_user: dict = Depends(lambda: {"role": "admin", "user_id": "admin_user"})):
    """Verify user has admin access - TODO: Implement proper admin auth"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


@router.get("/admin/overview")
async def get_admin_overview(
    admin_user: dict = Depends(verify_admin_access),
    db_manager = Depends(lambda: None)  # TODO: Proper dependency injection
):
    """
    Get admin dashboard overview with system metrics
    
    Provides high-level statistics for operations monitoring.
    """
    try:
        db_manager = await get_database_manager()
        
        with db_manager.get_session() as session:
            # User statistics
            total_users = session.query(User).count()
            active_users = session.query(User).filter(User.is_active == True).count()
            new_users_today = session.query(User).filter(
                User.created_at >= datetime.utcnow().date()
            ).count()
            
            # Organization statistics
            total_orgs = session.query(Organization).count()
            orgs_by_plan = session.query(
                Organization.plan_type, func.count(Organization.id)
            ).group_by(Organization.plan_type).all()
            
            # Deployment statistics (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_deployments = session.query(DeploymentHistory).filter(
                DeploymentHistory.created_at >= thirty_days_ago
            )
            
            total_deployments = recent_deployments.count()
            successful_deployments = recent_deployments.filter(
                DeploymentHistory.status == 'completed'
            ).count()
            failed_deployments = recent_deployments.filter(
                DeploymentHistory.status == 'failed'
            ).count()
            active_deployments = recent_deployments.filter(
                DeploymentHistory.status.in_(['pending', 'building', 'deploying'])
            ).count()
            
            # Job queue statistics
            queue_stats = await job_queue.get_queue_stats()
            
            # Calculate success rate
            success_rate = (successful_deployments / total_deployments * 100) if total_deployments > 0 else 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "new_today": new_users_today,
                    "activation_rate": round((active_users / total_users * 100), 1) if total_users > 0 else 0
                },
                "organizations": {
                    "total": total_orgs,
                    "by_plan": dict(orgs_by_plan)
                },
                "deployments": {
                    "total_30_days": total_deployments,
                    "successful": successful_deployments,
                    "failed": failed_deployments,
                    "active": active_deployments,
                    "success_rate": round(success_rate, 1)
                },
                "job_queue": queue_stats,
                "system_health": "healthy"  # TODO: Add actual health checks
            }
            
    except Exception as e:
        logger.error(f"Failed to get admin overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin overview"
        )


@router.get("/admin/users")
async def list_all_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    organization_id: Optional[str] = None,
    status: Optional[str] = None,
    admin_user: dict = Depends(verify_admin_access)
):
    """
    List all users with filtering and pagination
    
    Allows searching and filtering users for admin management.
    """
    try:
        db_manager = await get_database_manager()
        
        with db_manager.get_session() as session:
            query = session.query(User).join(Organization, User.organization_id == Organization.id, isouter=True)
            
            # Apply filters
            if search:
                search_filter = or_(
                    User.email.contains(search),
                    User.full_name.contains(search),
                    User.username.contains(search)
                )
                query = query.filter(search_filter)
            
            if organization_id:
                query = query.filter(User.organization_id == organization_id)
            
            if status == "active":
                query = query.filter(User.is_active == True)
            elif status == "inactive":
                query = query.filter(User.is_active == False)
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            users = query.order_by(desc(User.created_at)).offset(offset).limit(limit).all()
            
            user_list = []
            for user in users:
                user_data = {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "is_email_verified": user.is_email_verified,
                    "auth_provider": user.auth_provider,
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "organization": {
                        "id": user.organization.id,
                        "name": user.organization.name,
                        "plan_type": user.organization.plan_type
                    } if user.organization else None,
                    "current_month_deployments": user.current_month_deployments or 0,
                    "storage_used_gb": user.storage_used_gb or 0
                }
                user_list.append(user_data)
            
            return {
                "users": user_list,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to list users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/admin/users/{user_id}")
async def get_user_details(
    user_id: str,
    admin_user: dict = Depends(verify_admin_access)
):
    """
    Get detailed information about a specific user
    
    Includes quota usage, deployment history, and account details.
    """
    try:
        db_manager = await get_database_manager()
        
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Get quota status
            quota_status = await quota_manager.get_user_quota_status(user_id)
            
            # Get recent deployments
            recent_deployments = session.query(DeploymentHistory).filter(
                DeploymentHistory.user_id == user_id
            ).order_by(desc(DeploymentHistory.created_at)).limit(10).all()
            
            deployment_list = []
            for deployment in recent_deployments:
                deployment_list.append({
                    "id": deployment.id,
                    "session_id": deployment.session_id,
                    "status": deployment.status,
                    "project_name": deployment.project.name if deployment.project else "Unknown",
                    "created_at": deployment.created_at.isoformat(),
                    "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None,
                    "deployment_url": deployment.deployment_url
                })
            
            # Get projects
            projects = session.query(Project).filter(Project.owner_id == user_id).all()
            project_list = []
            for project in projects:
                project_list.append({
                    "id": project.id,
                    "name": project.name,
                    "framework": project.framework,
                    "deployment_status": project.deployment_status,
                    "current_url": project.current_url,
                    "created_at": project.created_at.isoformat()
                })
            
            return {
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "full_name": user.full_name,
                    "role": user.role,
                    "permissions": user.permissions,
                    "is_active": user.is_active,
                    "is_email_verified": user.is_email_verified,
                    "auth_provider": user.auth_provider,
                    "external_id": user.external_id,
                    "created_at": user.created_at.isoformat(),
                    "updated_at": user.updated_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None
                },
                "organization": {
                    "id": user.organization.id,
                    "name": user.organization.name,
                    "plan_type": user.organization.plan_type,
                    "created_at": user.organization.created_at.isoformat()
                } if user.organization else None,
                "team": {
                    "id": user.team.id,
                    "name": user.team.name
                } if user.team else None,
                "quota_status": quota_status,
                "recent_deployments": deployment_list,
                "projects": project_list
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user details"
        )


@router.post("/admin/users/{user_id}/suspend")
async def suspend_user(
    user_id: str,
    reason: str,
    admin_user: dict = Depends(verify_admin_access)
):
    """
    Suspend a user account
    
    Prevents user from creating new deployments and marks account as inactive.
    """
    try:
        db_manager = await get_database_manager()
        
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Suspend user
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            # Cancel any pending jobs for this user
            jobs = await job_queue.list_jobs(limit=100)
            cancelled_jobs = 0
            
            for job in jobs:
                if (job.data.get("user_id") == user_id and 
                    job.status in [JobStatus.PENDING, JobStatus.RUNNING]):
                    await job_queue.update_job_status(job.id, JobStatus.CANCELLED)
                    cancelled_jobs += 1
            
            session.commit()
            
            logger.info(f"Admin {admin_user['user_id']} suspended user {user_id}: {reason}")
            
            return {
                "status": "success",
                "message": f"User suspended successfully",
                "user_id": user_id,
                "reason": reason,
                "cancelled_jobs": cancelled_jobs,
                "suspended_by": admin_user["user_id"],
                "suspended_at": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suspend user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend user"
        )


@router.post("/admin/users/{user_id}/unsuspend")
async def unsuspend_user(
    user_id: str,
    admin_user: dict = Depends(verify_admin_access)
):
    """Reactivate a suspended user account"""
    try:
        db_manager = await get_database_manager()
        
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            user.is_active = True
            user.updated_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Admin {admin_user['user_id']} unsuspended user {user_id}")
            
            return {
                "status": "success",
                "message": "User reactivated successfully",
                "user_id": user_id,
                "reactivated_by": admin_user["user_id"],
                "reactivated_at": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unsuspend user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reactivate user"
        )


@router.post("/admin/users/{user_id}/quota-override")
async def override_user_quota(
    user_id: str,
    quota_overrides: Dict[str, int],
    reason: str,
    expires_at: Optional[str] = None,
    admin_user: dict = Depends(verify_admin_access)
):
    """
    Override quota limits for a specific user (VIP support)
    
    Temporarily increases limits for enterprise trials or VIP customers.
    """
    try:
        db_manager = await get_database_manager()
        
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user or not user.organization:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User or organization not found"
                )
            
            # Apply quota overrides to organization
            org = user.organization
            
            if "monthly_deployment_limit" in quota_overrides:
                org.monthly_deployment_limit = quota_overrides["monthly_deployment_limit"]
            
            if "concurrent_deployment_limit" in quota_overrides:
                org.concurrent_deployment_limit = quota_overrides["concurrent_deployment_limit"]
            
            if "storage_limit_gb" in quota_overrides:
                org.storage_limit_gb = quota_overrides["storage_limit_gb"]
            
            if "build_minutes_limit" in quota_overrides:
                org.build_minutes_limit = quota_overrides["build_minutes_limit"]
            
            org.updated_at = datetime.utcnow()
            session.commit()
            
            logger.info(f"Admin {admin_user['user_id']} applied quota override for user {user_id}: {quota_overrides}")
            
            return {
                "status": "success",
                "message": "Quota override applied successfully",
                "user_id": user_id,
                "organization_id": org.id,
                "overrides": quota_overrides,
                "reason": reason,
                "expires_at": expires_at,
                "applied_by": admin_user["user_id"],
                "applied_at": datetime.utcnow().isoformat()
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply quota override: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply quota override"
        )


@router.get("/admin/deployments")
async def list_all_deployments(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    project_name: Optional[str] = None,
    admin_user: dict = Depends(verify_admin_access)
):
    """
    List all deployments across the platform
    
    Provides comprehensive deployment monitoring for operations.
    """
    try:
        db_manager = await get_database_manager()
        
        with db_manager.get_session() as session:
            query = session.query(DeploymentHistory).join(
                User, DeploymentHistory.user_id == User.id
            ).join(
                Project, DeploymentHistory.project_id == Project.id, isouter=True
            )
            
            # Apply filters
            if status:
                query = query.filter(DeploymentHistory.status == status)
            
            if user_id:
                query = query.filter(DeploymentHistory.user_id == user_id)
            
            if project_name:
                query = query.filter(Project.name.contains(project_name))
            
            # Get total count
            total_count = query.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            deployments = query.order_by(
                desc(DeploymentHistory.created_at)
            ).offset(offset).limit(limit).all()
            
            deployment_list = []
            for deployment in deployments:
                deployment_list.append({
                    "id": deployment.id,
                    "session_id": deployment.session_id,
                    "status": deployment.status,
                    "deployment_type": deployment.deployment_type,
                    "user": {
                        "id": deployment.user.id,
                        "email": deployment.user.email,
                        "organization": deployment.user.organization.name if deployment.user.organization else None
                    },
                    "project": {
                        "id": deployment.project.id,
                        "name": deployment.project.name,
                        "framework": deployment.project.framework
                    } if deployment.project else None,
                    "deployment_url": deployment.deployment_url,
                    "build_time_seconds": deployment.build_time_seconds,
                    "error_message": deployment.error_message,
                    "created_at": deployment.created_at.isoformat(),
                    "completed_at": deployment.completed_at.isoformat() if deployment.completed_at else None
                })
            
            return {
                "deployments": deployment_list,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total_count": total_count,
                    "total_pages": (total_count + limit - 1) // limit
                }
            }
            
    except Exception as e:
        logger.error(f"Failed to list deployments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve deployments"
        )


@router.get("/admin/job-queue")
async def get_job_queue_status(
    admin_user: dict = Depends(verify_admin_access)
):
    """
    Get comprehensive job queue status
    
    Provides real-time job queue monitoring for operations.
    """
    try:
        # Get queue statistics
        queue_stats = await job_queue.get_queue_stats()
        
        # Get recent jobs
        recent_jobs = await job_queue.list_jobs(limit=50)
        
        job_list = []
        for job in recent_jobs:
            job_list.append({
                "id": job.id,
                "job_type": job.job_type,
                "status": job.status.value,
                "priority": job.priority.value,
                "retry_count": job.retry_count,
                "max_retries": job.max_retries,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "session_id": job.data.get("session_id") if hasattr(job, 'data') else None,
                "user_id": job.data.get("user_id") if hasattr(job, 'data') else None
            })
        
        return {
            "queue_stats": queue_stats,
            "recent_jobs": job_list,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get job queue status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job queue status"
        )


@router.post("/admin/job-queue/retry-failed")
async def retry_failed_jobs(
    admin_user: dict = Depends(verify_admin_access)
):
    """
    Retry all failed jobs in the queue
    
    Useful for recovering from system-wide issues.
    """
    try:
        # Get failed jobs
        failed_jobs = await job_queue.list_jobs(status=JobStatus.FAILED, limit=100)
        
        retried_count = 0
        for job in failed_jobs:
            if job.retry_count < job.max_retries:
                await job_queue.retry_job(job.id)
                retried_count += 1
        
        logger.info(f"Admin {admin_user['user_id']} retried {retried_count} failed jobs")
        
        return {
            "status": "success",
            "message": f"Retried {retried_count} failed jobs",
            "retried_count": retried_count,
            "retried_by": admin_user["user_id"],
            "retried_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to retry failed jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retry failed jobs"
        )


@router.post("/admin/impersonate/{user_id}")
async def create_impersonation_token(
    user_id: str,
    reason: str,
    duration_minutes: int = Query(60, ge=5, le=480),  # 5 minutes to 8 hours
    admin_user: dict = Depends(verify_admin_access)
):
    """
    Create impersonation token for debugging user issues
    
    Allows admin to access the platform as if they were the user.
    """
    try:
        db_manager = await get_database_manager()
        
        with db_manager.get_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Create impersonation token (simplified - in production use proper JWT)
            import secrets
            impersonation_token = f"imp_{secrets.token_urlsafe(32)}"
            
            # In production, store this in Redis with expiration
            # For now, just return the token details
            
            logger.info(f"Admin {admin_user['user_id']} created impersonation token for user {user_id}: {reason}")
            
            return {
                "status": "success",
                "impersonation_token": impersonation_token,
                "user_id": user_id,
                "user_email": user.email,
                "reason": reason,
                "duration_minutes": duration_minutes,
                "expires_at": (datetime.utcnow() + timedelta(minutes=duration_minutes)).isoformat(),
                "created_by": admin_user["user_id"],
                "created_at": datetime.utcnow().isoformat(),
                "warning": "Use impersonation responsibly and only for legitimate debugging purposes"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create impersonation token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create impersonation token"
        )
