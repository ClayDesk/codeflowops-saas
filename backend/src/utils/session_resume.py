"""
Session resume functionality
Handles recovery of interrupted deployments
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

from ..models.enhanced_models import DeploymentHistory, User
from ..utils.job_queue import job_queue, JobStatus
from ..utils.deployment_locks import DeploymentLock
from dependencies.session import get_session_manager
from database.connection import get_database_manager

logger = logging.getLogger(__name__)


class ResumeStrategy(Enum):
    """Strategies for resuming failed deployments"""
    RESTART = "restart"  # Start from beginning
    CONTINUE = "continue"  # Continue from where it left off
    SKIP_TO_DEPLOY = "skip_to_deploy"  # Skip build, go to deployment


class SessionResumeManager:
    """Manages session resume functionality"""
    
    def __init__(self):
        self.db_manager = None
        self.session_manager = None
    
    async def initialize(self):
        """Initialize dependencies"""
        if not self.db_manager:
            self.db_manager = await get_database_manager()
        if not self.session_manager:
            self.session_manager = await get_session_manager()
    
    async def find_resumable_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Find sessions that can be resumed for a user"""
        await self.initialize()
        
        try:
            with self.db_manager.get_session() as session:
                # Find deployments that are stuck or failed within last 24 hours
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                
                stuck_deployments = session.query(DeploymentHistory).filter(
                    DeploymentHistory.user_id == user_id,
                    DeploymentHistory.status.in_(['pending', 'building', 'deploying', 'failed']),
                    DeploymentHistory.created_at >= cutoff_time
                ).all()
                
                resumable_sessions = []
                
                for deployment in stuck_deployments:
                    # Get session info
                    session_info = await self.session_manager.get_session(deployment.session_id)
                    if not session_info:
                        continue
                    
                    # Determine resume strategy
                    strategy = await self._determine_resume_strategy(deployment, session_info)
                    
                    resumable_sessions.append({
                        "session_id": deployment.session_id,
                        "project_name": deployment.project.name if deployment.project else "Unknown",
                        "status": deployment.status,
                        "created_at": deployment.created_at.isoformat(),
                        "last_step": session_info.current_step,
                        "progress_percentage": getattr(session_info, 'progress_percentage', 0),
                        "resume_strategy": strategy.value,
                        "can_resume": True,
                        "error_message": deployment.error_message
                    })
                
                return resumable_sessions
                
        except Exception as e:
            logger.error(f"Failed to find resumable sessions: {e}")
            return []
    
    async def resume_session(
        self, 
        session_id: str, 
        user_id: str, 
        strategy: ResumeStrategy = ResumeStrategy.CONTINUE
    ) -> Tuple[bool, str]:
        """
        Resume a failed or stuck session
        
        Returns:
            (success: bool, message: str)
        """
        await self.initialize()
        
        try:
            # Verify user owns this session
            with self.db_manager.get_session() as db_session:
                deployment = db_session.query(DeploymentHistory).filter(
                    DeploymentHistory.session_id == session_id,
                    DeploymentHistory.user_id == user_id
                ).first()
                
                if not deployment:
                    return False, "Session not found or access denied"
                
                # Check if session is actually resumable
                if deployment.status in ['completed', 'destroyed']:
                    return False, "Session already completed"
                
                # Get session info
                session_info = await self.session_manager.get_session(session_id)
                if not session_info:
                    return False, "Session data not found"
                
                # Use deployment lock to prevent conflicts
                async with DeploymentLock(session_id):
                    # Check for existing jobs
                    existing_job = await self._find_existing_job(session_id)
                    if existing_job:
                        if existing_job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                            return False, "Session already has a running job"
                        
                        # Cancel failed job
                        await job_queue.update_job_status(existing_job.id, JobStatus.CANCELLED)
                    
                    # Update session status
                    await self.session_manager.update_session_status(
                        session_id,
                        "resuming",
                        current_step="preparing_resume",
                        progress_percentage=0
                    )
                    
                    # Create resume job based on strategy
                    job_data = await self._create_resume_job_data(
                        session_id, deployment, session_info, strategy
                    )
                    
                    # Queue resume job
                    from ..utils.job_queue import JobPriority
                    job_id = await job_queue.add_job(
                        "deployment",
                        job_data,
                        priority=JobPriority.HIGH,
                        retry_count=2
                    )
                    
                    # Update session with new job ID
                    await self.session_manager.update_session_metadata(
                        session_id,
                        {"resume_job_id": job_id, "resume_strategy": strategy.value}
                    )
                    
                    logger.info(f"Resume job queued for session {session_id} with strategy {strategy.value}")
                    return True, f"Session resume started with {strategy.value} strategy"
                
        except Exception as e:
            logger.error(f"Failed to resume session {session_id}: {e}")
            return False, f"Failed to resume session: {str(e)}"
    
    async def _determine_resume_strategy(
        self, 
        deployment: DeploymentHistory, 
        session_info: Any
    ) -> ResumeStrategy:
        """Determine the best resume strategy based on session state"""
        
        current_step = getattr(session_info, 'current_step', '')
        progress = getattr(session_info, 'progress_percentage', 0)
        
        # If we haven't started building yet, restart from beginning
        if progress < 20 or current_step in ['initializing', 'analyzing']:
            return ResumeStrategy.RESTART
        
        # If build completed but deployment failed, skip to deployment
        if progress >= 70 or current_step in ['deploying', 'finalizing']:
            return ResumeStrategy.SKIP_TO_DEPLOY
        
        # If in middle of process, try to continue
        return ResumeStrategy.CONTINUE
    
    async def _find_existing_job(self, session_id: str) -> Optional[Any]:
        """Find existing job for this session"""
        try:
            # Get recent jobs and check for this session
            jobs = await job_queue.list_jobs(job_type="deployment", limit=100)
            
            for job in jobs:
                if (job.data.get("session_id") == session_id and 
                    job.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.FAILED]):
                    return job
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to find existing job: {e}")
            return None
    
    async def _create_resume_job_data(
        self, 
        session_id: str, 
        deployment: DeploymentHistory, 
        session_info: Any, 
        strategy: ResumeStrategy
    ) -> Dict[str, Any]:
        """Create job data for resume operation"""
        
        # Get original deployment config from session
        original_config = getattr(session_info, 'deployment_config', {})
        
        job_data = {
            "session_id": session_id,
            "task_type": "deploy",
            "is_resume": True,
            "resume_strategy": strategy.value,
            "original_deployment_id": deployment.id,
            "deployment_config": original_config
        }
        
        # Add strategy-specific data
        if strategy == ResumeStrategy.CONTINUE:
            job_data["resume_from_step"] = getattr(session_info, 'current_step', 'initializing')
            job_data["resume_progress"] = getattr(session_info, 'progress_percentage', 0)
        
        elif strategy == ResumeStrategy.SKIP_TO_DEPLOY:
            job_data["skip_build"] = True
            job_data["resume_from_step"] = "deploying"
            job_data["resume_progress"] = 70
        
        elif strategy == ResumeStrategy.RESTART:
            job_data["force_restart"] = True
            job_data["resume_from_step"] = "initializing"
            job_data["resume_progress"] = 0
        
        return job_data
    
    async def cleanup_abandoned_sessions(self, max_age_hours: int = 48):
        """Clean up sessions that have been abandoned for too long"""
        await self.initialize()
        
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            with self.db_manager.get_session() as session:
                # Find old stuck deployments
                abandoned_deployments = session.query(DeploymentHistory).filter(
                    DeploymentHistory.status.in_(['pending', 'building', 'deploying']),
                    DeploymentHistory.created_at < cutoff_time
                ).all()
                
                cleanup_count = 0
                for deployment in abandoned_deployments:
                    try:
                        # Update deployment status to failed
                        deployment.status = 'failed'
                        deployment.error_message = 'Session abandoned - exceeded maximum time limit'
                        deployment.completed_at = datetime.utcnow()
                        
                        # Update session status
                        await self.session_manager.update_session_status(
                            deployment.session_id,
                            "failed",
                            error_details="Session abandoned - exceeded maximum time limit"
                        )
                        
                        # Cancel any pending jobs
                        existing_job = await self._find_existing_job(deployment.session_id)
                        if existing_job and existing_job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
                            await job_queue.update_job_status(existing_job.id, JobStatus.CANCELLED)
                        
                        cleanup_count += 1
                        
                    except Exception as e:
                        logger.error(f"Failed to cleanup session {deployment.session_id}: {e}")
                
                session.commit()
                logger.info(f"Cleaned up {cleanup_count} abandoned sessions")
                
        except Exception as e:
            logger.error(f"Failed to cleanup abandoned sessions: {e}")
    
    async def get_session_recovery_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed recovery information for a session"""
        await self.initialize()
        
        try:
            session_info = await self.session_manager.get_session(session_id)
            if not session_info:
                return None
            
            with self.db_manager.get_session() as db_session:
                deployment = db_session.query(DeploymentHistory).filter(
                    DeploymentHistory.session_id == session_id
                ).first()
                
                if not deployment:
                    return None
                
                return {
                    "session_id": session_id,
                    "status": deployment.status,
                    "current_step": getattr(session_info, 'current_step', 'unknown'),
                    "progress_percentage": getattr(session_info, 'progress_percentage', 0),
                    "created_at": deployment.created_at.isoformat(),
                    "last_activity": getattr(session_info, 'updated_at', deployment.created_at).isoformat(),
                    "error_message": deployment.error_message,
                    "can_resume": deployment.status in ['pending', 'building', 'deploying', 'failed'],
                    "recommended_strategy": (await self._determine_resume_strategy(deployment, session_info)).value,
                    "project_name": deployment.project.name if deployment.project else "Unknown",
                    "github_repo": f"{deployment.project.github_owner}/{deployment.project.github_repo}" if deployment.project else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get recovery info for session {session_id}: {e}")
            return None


# Global session resume manager
session_resume_manager = SessionResumeManager()
