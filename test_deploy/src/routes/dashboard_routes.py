"""
Dashboard API endpoints
Provides aggregated data for frontend dashboard
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from ..utils.job_queue import job_queue, JobStatus
from dependencies.session import get_session_manager, SessionManager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard/overview")
async def get_dashboard_overview(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get dashboard overview with key metrics
    
    Returns summary data for the main dashboard view.
    """
    try:
        # Get job queue stats
        queue_stats = await job_queue.get_queue_stats()
        
        # Get recent sessions (last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        recent_sessions = await session_manager.get_recent_sessions(
            since=cutoff_date,
            limit=100
        )
        
        # Calculate session statistics
        session_stats = {
            "total_sessions": len(recent_sessions),
            "completed_deployments": 0,
            "failed_deployments": 0,
            "active_deployments": 0,
            "total_projects": 0
        }
        
        projects = set()
        for session in recent_sessions:
            if session.status == "completed":
                session_stats["completed_deployments"] += 1
            elif session.status == "failed":
                session_stats["failed_deployments"] += 1
            elif session.status in ["building", "deploying"]:
                session_stats["active_deployments"] += 1
            
            if hasattr(session, 'project_name') and session.project_name:
                projects.add(session.project_name)
        
        session_stats["total_projects"] = len(projects)
        
        # Calculate success rate
        total_completed = session_stats["completed_deployments"] + session_stats["failed_deployments"]
        success_rate = (session_stats["completed_deployments"] / total_completed * 100) if total_completed > 0 else 0
        
        # Get recent deployments for activity feed
        recent_activity = []
        for session in recent_sessions[:10]:  # Last 10 sessions
            recent_activity.append({
                "session_id": session.session_id,
                "project_name": getattr(session, 'project_name', 'Unknown'),
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "framework": session.analysis_result.get("framework") if session.analysis_result else None,
                "deployment_url": session.deployment_result.get("primary_url") if session.deployment_result else None
            })
        
        return {
            "queue_stats": queue_stats,
            "session_stats": session_stats,
            "success_rate": round(success_rate, 1),
            "recent_activity": recent_activity,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/dashboard/projects")
async def get_project_dashboard(
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get project-focused dashboard data
    
    Returns project list with deployment status and metrics.
    """
    try:
        # Get all sessions grouped by project
        all_sessions = await session_manager.get_recent_sessions(limit=500)
        
        projects = {}
        for session in all_sessions:
            project_name = getattr(session, 'project_name', session.session_id[:8])
            
            if project_name not in projects:
                projects[project_name] = {
                    "project_name": project_name,
                    "total_deployments": 0,
                    "successful_deployments": 0,
                    "failed_deployments": 0,
                    "last_deployment": None,
                    "last_deployment_status": None,
                    "last_deployment_url": None,
                    "framework": None,
                    "created_at": session.created_at,
                    "updated_at": session.created_at
                }
            
            project = projects[project_name]
            project["total_deployments"] += 1
            
            if session.status == "completed":
                project["successful_deployments"] += 1
            elif session.status == "failed":
                project["failed_deployments"] += 1
            
            # Update latest deployment info
            if not project["last_deployment"] or session.created_at > project["updated_at"]:
                project["last_deployment"] = session.created_at.isoformat()
                project["last_deployment_status"] = session.status
                project["updated_at"] = session.created_at
                
                if session.deployment_result:
                    project["last_deployment_url"] = session.deployment_result.get("primary_url")
                
                if session.analysis_result:
                    project["framework"] = session.analysis_result.get("framework")
        
        # Calculate success rates
        project_list = []
        for project in projects.values():
            total = project["successful_deployments"] + project["failed_deployments"]
            success_rate = (project["successful_deployments"] / total * 100) if total > 0 else 0
            
            project_list.append({
                **project,
                "success_rate": round(success_rate, 1)
            })
        
        # Sort by last deployment (most recent first)
        project_list.sort(key=lambda x: x["updated_at"], reverse=True)
        
        return {
            "projects": project_list,
            "total_projects": len(project_list),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get project dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve project dashboard data"
        )


@router.get("/dashboard/activity")
async def get_activity_feed(
    limit: int = 50,
    session_manager: SessionManager = Depends(get_session_manager)
):
    """
    Get recent activity feed for dashboard
    
    Returns chronological list of recent deployments and events.
    """
    try:
        recent_sessions = await session_manager.get_recent_sessions(limit=limit)
        
        activity_feed = []
        for session in recent_sessions:
            # Determine activity type and message
            activity_type = "deployment"
            message = f"Deployment {session.status}"
            
            if session.status == "completed":
                message = "Deployment completed successfully"
            elif session.status == "failed":
                message = f"Deployment failed: {session.error_details or 'Unknown error'}"
            elif session.status in ["building", "deploying"]:
                message = f"Deployment in progress ({session.status})"
                activity_type = "in_progress"
            
            activity_feed.append({
                "id": session.session_id,
                "type": activity_type,
                "project_name": getattr(session, 'project_name', 'Unknown'),
                "message": message,
                "status": session.status,
                "timestamp": session.created_at.isoformat(),
                "framework": session.analysis_result.get("framework") if session.analysis_result else None,
                "deployment_url": session.deployment_result.get("primary_url") if session.deployment_result else None
            })
        
        return {
            "activity": activity_feed,
            "total_count": len(activity_feed),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get activity feed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity feed"
        )
