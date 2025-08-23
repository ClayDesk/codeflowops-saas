"""
Job queue management for CodeFlowOps
Handles async task queuing with Redis and retry logic
"""

import redis
import json
import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class JobPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4

class Job:
    """Job model for queue management"""
    
    def __init__(
        self,
        job_id: str,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: int = 60,
        timeout: int = 3600
    ):
        self.job_id = job_id
        self.job_type = job_type
        self.payload = payload
        self.priority = priority
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.status = JobStatus.PENDING
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.retry_count = 0
        self.progress_percentage = 0
        self.current_step = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for storage"""
        return {
            "job_id": self.job_id,
            "job_type": self.job_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "progress_percentage": self.progress_percentage,
            "current_step": self.current_step
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary"""
        job = cls(
            job_id=data["job_id"],
            job_type=data["job_type"],
            payload=data["payload"],
            priority=JobPriority(data["priority"]),
            max_retries=data["max_retries"],
            retry_delay=data["retry_delay"],
            timeout=data["timeout"]
        )
        job.status = JobStatus(data["status"])
        job.created_at = datetime.fromisoformat(data["created_at"])
        if data["started_at"]:
            job.started_at = datetime.fromisoformat(data["started_at"])
        if data["completed_at"]:
            job.completed_at = datetime.fromisoformat(data["completed_at"])
        job.error_message = data["error_message"]
        job.retry_count = data["retry_count"]
        job.progress_percentage = data["progress_percentage"]
        job.current_step = data["current_step"]
        return job

class JobQueue:
    """Redis-based job queue with retry logic"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
        self.queue_name = "codeflowops:jobs"
        self.processing_set = "codeflowops:processing"
        self.job_data_key = "codeflowops:job_data"
        self.retry_queue = "codeflowops:retry"
    
    async def enqueue(
        self,
        job_type: str,
        payload: Dict[str, Any],
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        session_id: Optional[str] = None
    ) -> str:
        """Enqueue a new job"""
        
        job_id = session_id or str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            job_type=job_type,
            payload=payload,
            priority=priority,
            max_retries=max_retries
        )
        
        # Store job data
        self.redis_client.hset(
            self.job_data_key,
            job_id,
            json.dumps(job.to_dict())
        )
        
        # Add to priority queue (higher priority = higher score)
        self.redis_client.zadd(
            self.queue_name,
            {job_id: priority.value}
        )
        
        logger.info(f"Enqueued job {job_id} of type {job_type}")
        return job_id
    
    async def dequeue(self) -> Optional[Job]:
        """Dequeue the highest priority job"""
        
        # Get highest priority job
        result = self.redis_client.zpopmax(self.queue_name)
        
        if not result:
            return None
        
        job_id, priority = result[0]
        
        # Move to processing set
        self.redis_client.sadd(self.processing_set, job_id)
        
        # Get job data
        job_data = self.redis_client.hget(self.job_data_key, job_id)
        if not job_data:
            logger.error(f"Job data not found for job {job_id}")
            return None
        
        job = Job.from_dict(json.loads(job_data))
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        
        # Update job status
        await self.update_job(job)
        
        return job
    
    async def complete_job(self, job_id: str, result: Optional[Dict[str, Any]] = None):
        """Mark job as completed"""
        
        job = await self.get_job(job_id)
        if not job:
            return
        
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.progress_percentage = 100
        
        if result:
            job.payload["result"] = result
        
        await self.update_job(job)
        
        # Remove from processing
        self.redis_client.srem(self.processing_set, job_id)
        
        logger.info(f"Job {job_id} completed successfully")
    
    async def fail_job(self, job_id: str, error_message: str):
        """Mark job as failed and handle retries"""
        
        job = await self.get_job(job_id)
        if not job:
            return
        
        job.retry_count += 1
        job.error_message = error_message
        
        if job.retry_count <= job.max_retries:
            # Schedule retry
            job.status = JobStatus.RETRYING
            
            # Add to retry queue with delay
            retry_time = datetime.utcnow() + timedelta(seconds=job.retry_delay)
            self.redis_client.zadd(
                self.retry_queue,
                {job_id: retry_time.timestamp()}
            )
            
            logger.info(f"Job {job_id} scheduled for retry {job.retry_count}/{job.max_retries}")
        else:
            # Mark as permanently failed
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            
            logger.error(f"Job {job_id} failed permanently after {job.retry_count} retries")
        
        await self.update_job(job)
        
        # Remove from processing
        self.redis_client.srem(self.processing_set, job_id)
    
    async def update_job_progress(self, job_id: str, progress: int, current_step: str):
        """Update job progress"""
        
        job = await self.get_job(job_id)
        if not job:
            return
        
        job.progress_percentage = progress
        job.current_step = current_step
        
        await self.update_job(job)
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        
        job_data = self.redis_client.hget(self.job_data_key, job_id)
        if not job_data:
            return None
        
        return Job.from_dict(json.loads(job_data))
    
    async def update_job(self, job: Job):
        """Update job data in Redis"""
        
        self.redis_client.hset(
            self.job_data_key,
            job.job_id,
            json.dumps(job.to_dict())
        )
    
    async def get_ready_retries(self) -> List[str]:
        """Get jobs ready for retry"""
        
        current_time = datetime.utcnow().timestamp()
        
        # Get jobs ready for retry
        ready_jobs = self.redis_client.zrangebyscore(
            self.retry_queue,
            0,
            current_time
        )
        
        # Remove from retry queue and add back to main queue
        for job_id in ready_jobs:
            self.redis_client.zrem(self.retry_queue, job_id)
            
            job = await self.get_job(job_id)
            if job:
                job.status = JobStatus.PENDING
                await self.update_job(job)
                
                self.redis_client.zadd(
                    self.queue_name,
                    {job_id: job.priority.value}
                )
        
        return ready_jobs
    
    async def cancel_job(self, job_id: str):
        """Cancel a job"""
        
        job = await self.get_job(job_id)
        if not job:
            return False
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            return False
        
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        
        await self.update_job(job)
        
        # Remove from all queues
        self.redis_client.zrem(self.queue_name, job_id)
        self.redis_client.zrem(self.retry_queue, job_id)
        self.redis_client.srem(self.processing_set, job_id)
        
        logger.info(f"Job {job_id} cancelled")
        return True
    
    async def list_jobs(
        self, 
        job_type: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Job]:
        """List jobs with optional filtering"""
        try:
            jobs = []
            
            # Get all job IDs from Redis
            all_job_ids = self.redis_client.hkeys(self.job_data_key)
            
            # Fetch and filter jobs
            for job_id in all_job_ids:
                job = await self.get_job(job_id.decode() if isinstance(job_id, bytes) else job_id)
                if job:
                    # Apply filters
                    if job_type and job.job_type != job_type:
                        continue
                    if status and job.status != status:
                        continue
                    jobs.append(job)
            
            # Sort by created_at desc
            jobs.sort(key=lambda x: x.created_at, reverse=True)
            
            # Apply pagination
            return jobs[offset:offset + limit]
            
        except Exception as e:
            logger.error(f"Failed to list jobs: {e}")
            return []
    
    async def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics"""
        
        return {
            "pending": self.redis_client.zcard(self.queue_name),
            "processing": self.redis_client.scard(self.processing_set),
            "retrying": self.redis_client.zcard(self.retry_queue),
            "total_jobs": self.redis_client.hlen(self.job_data_key)
        }

# Global job queue instance
job_queue = JobQueue()
