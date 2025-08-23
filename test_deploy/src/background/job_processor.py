"""
Job processor for Redis queue
Handles deployment and other background tasks
"""

import asyncio
import logging
from typing import Dict, Any
import json

from ..utils.job_queue import job_queue, JobStatus
from ..utils.deployment_locks import DeploymentLock
from background.deployment_tasks import start_deployment_task, start_destroy_task
from dependencies.session import get_session_manager

logger = logging.getLogger(__name__)


class JobProcessor:
    """Processes jobs from Redis queue"""
    
    def __init__(self):
        self.running = False
        self.session_manager = None
    
    async def start(self):
        """Start the job processor"""
        self.running = True
        self.session_manager = await get_session_manager()
        logger.info("Job processor started")
        
        # Start processing jobs
        await self._process_jobs()
    
    async def stop(self):
        """Stop the job processor"""
        self.running = False
        logger.info("Job processor stopped")
    
    async def _process_jobs(self):
        """Main job processing loop"""
        while self.running:
            try:
                # Get next job from queue
                job = await job_queue.get_next_job("deployment")
                
                if job:
                    logger.info(f"Processing job {job.id}: {job.job_type}")
                    await self._handle_job(job)
                else:
                    # No jobs available, wait before checking again
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in job processing loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _handle_job(self, job):
        """Handle a specific job"""
        try:
            # Update job status to running
            await job_queue.update_job_status(job.id, JobStatus.RUNNING)
            
            # Extract job data
            job_data = job.data
            session_id = job_data.get("session_id")
            task_type = job_data.get("task_type", "deploy")
            
            logger.info(f"Processing {task_type} job for session {session_id}")
            
            # Process based on task type
            if task_type == "deploy":
                await self._process_deployment_job(job_data)
            elif task_type == "destroy":
                await self._process_destroy_job(job_data)
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # Mark job as completed
            await job_queue.update_job_status(job.id, JobStatus.COMPLETED)
            logger.info(f"Job {job.id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job.id} failed: {e}")
            
            # Update job status to failed
            await job_queue.update_job_status(
                job.id, 
                JobStatus.FAILED, 
                error_message=str(e)
            )
            
            # Update session status if possible
            if hasattr(job, 'data') and 'session_id' in job.data:
                try:
                    await self.session_manager.update_session_status(
                        job.data['session_id'],
                        "failed",
                        error_details=str(e)
                    )
                except Exception as session_error:
                    logger.error(f"Failed to update session status: {session_error}")
            
            # Check if job should be retried
            if job.retry_count > 0:
                await job_queue.retry_job(job.id)
                logger.info(f"Job {job.id} queued for retry")
    
    async def _process_deployment_job(self, job_data: Dict[str, Any]):
        """Process a deployment job"""
        session_id = job_data["session_id"]
        deployment_config = job_data["deployment_config"]
        
        # Use deployment lock to ensure no concurrent operations
        async with DeploymentLock(session_id):
            logger.info(f"Starting deployment task for session {session_id}")
            
            # Call the existing deployment task
            await start_deployment_task(
                session_id,
                deployment_config,
                is_retry=job_data.get("is_retry", False),
                force_rebuild=job_data.get("force_rebuild", False)
            )
    
    async def _process_destroy_job(self, job_data: Dict[str, Any]):
        """Process a destroy job"""
        session_id = job_data["session_id"]
        
        # Use deployment lock to ensure no concurrent operations
        async with DeploymentLock(session_id):
            logger.info(f"Starting destroy task for session {session_id}")
            
            # Call the existing destroy task
            await start_destroy_task(session_id)


# Global job processor instance
job_processor = JobProcessor()


async def start_job_processor():
    """Start the global job processor"""
    await job_processor.start()


async def stop_job_processor():
    """Stop the global job processor"""
    await job_processor.stop()
