"""
Structured logging system for deployments
Provides structured logs with download capabilities
"""

import json
import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class StructuredLogger:
    """Structured logging system for deployment processes"""
    
    def __init__(self):
        self.s3_client = None
        self.logs_bucket = getattr(settings, 'DEPLOYMENT_LOGS_BUCKET', 'codeflowops-deployment-logs')
        self.local_logs_dir = Path(getattr(settings, 'LOCAL_LOGS_DIR', '/tmp/deployment_logs'))
        self.local_logs_dir.mkdir(exist_ok=True)
    
    def _get_s3_client(self):
        """Get S3 client for log storage"""
        if not self.s3_client:
            self.s3_client = boto3.client(
                's3',
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
        return self.s3_client
    
    def create_deployment_logger(self, session_id: str, user_id: str) -> 'DeploymentLogger':
        """Create a deployment-specific logger"""
        return DeploymentLogger(session_id, user_id, self)
    
    async def ensure_logs_bucket(self):
        """Ensure S3 bucket exists for log storage"""
        try:
            s3_client = self._get_s3_client()
            s3_client.head_bucket(Bucket=self.logs_bucket)
            logger.info(f"Logs bucket {self.logs_bucket} exists")
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    if settings.AWS_REGION == 'us-east-1':
                        s3_client.create_bucket(Bucket=self.logs_bucket)
                    else:
                        s3_client.create_bucket(
                            Bucket=self.logs_bucket,
                            CreateBucketConfiguration={'LocationConstraint': settings.AWS_REGION}
                        )
                    logger.info(f"Created logs bucket {self.logs_bucket}")
                except ClientError as create_error:
                    logger.error(f"Failed to create logs bucket: {create_error}")
                    raise
            else:
                logger.error(f"Failed to check logs bucket: {e}")
                raise
    
    async def upload_logs_to_s3(self, session_id: str, local_log_path: Path) -> str:
        """Upload log file to S3 and return URL"""
        try:
            s3_client = self._get_s3_client()
            
            # Generate S3 key
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            s3_key = f"deployments/{session_id}/{timestamp}_deployment.log"
            
            # Upload file
            s3_client.upload_file(
                str(local_log_path),
                self.logs_bucket,
                s3_key,
                ExtraArgs={'ContentType': 'text/plain'}
            )
            
            # Generate presigned URL for download (valid for 24 hours)
            download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.logs_bucket, 'Key': s3_key},
                ExpiresIn=86400  # 24 hours
            )
            
            logger.info(f"Uploaded deployment logs to S3: {s3_key}")
            return download_url
            
        except Exception as e:
            logger.error(f"Failed to upload logs to S3: {e}")
            raise
    
    async def get_logs_download_url(self, session_id: str) -> Optional[str]:
        """Get download URL for existing deployment logs"""
        try:
            s3_client = self._get_s3_client()
            
            # List objects with session_id prefix
            response = s3_client.list_objects_v2(
                Bucket=self.logs_bucket,
                Prefix=f"deployments/{session_id}/"
            )
            
            if 'Contents' in response and response['Contents']:
                # Get the most recent log file
                latest_log = sorted(response['Contents'], key=lambda x: x['LastModified'])[-1]
                
                # Generate download URL
                download_url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.logs_bucket, 'Key': latest_log['Key']},
                    ExpiresIn=86400
                )
                
                return download_url
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get logs download URL: {e}")
            return None


class DeploymentLogger:
    """Logger for individual deployment sessions"""
    
    def __init__(self, session_id: str, user_id: str, structured_logger: StructuredLogger):
        self.session_id = session_id
        self.user_id = user_id
        self.structured_logger = structured_logger
        self.start_time = datetime.utcnow()
        
        # Create log file
        self.log_file = self.structured_logger.local_logs_dir / f"{session_id}.log"
        self.log_entries: List[Dict[str, Any]] = []
        
        # Initialize log file
        self._write_header()
    
    def _write_header(self):
        """Write log file header"""
        header = {
            "type": "deployment_start",
            "timestamp": self.start_time.isoformat(),
            "session_id": self.session_id,
            "user_id": self.user_id,
            "version": "1.0"
        }
        self._write_entry(header)
    
    def _write_entry(self, entry: Dict[str, Any]):
        """Write a log entry to file and memory"""
        # Add to memory
        self.log_entries.append(entry)
        
        # Write to file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(entry) + '\n')
        except Exception as e:
            logger.error(f"Failed to write log entry: {e}")
    
    def log_step(self, step: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Log a deployment step"""
        entry = {
            "type": "step",
            "timestamp": datetime.utcnow().isoformat(),
            "step": step,
            "message": message,
            "details": details or {}
        }
        self._write_entry(entry)
    
    def log_command(self, command: str, output: str, exit_code: int, duration: float):
        """Log a command execution"""
        entry = {
            "type": "command",
            "timestamp": datetime.utcnow().isoformat(),
            "command": command,
            "output": output,
            "exit_code": exit_code,
            "duration_seconds": duration,
            "success": exit_code == 0
        }
        self._write_entry(entry)
    
    def log_progress(self, step: str, progress_percent: int, message: str):
        """Log progress update"""
        entry = {
            "type": "progress",
            "timestamp": datetime.utcnow().isoformat(),
            "step": step,
            "progress_percent": progress_percent,
            "message": message
        }
        self._write_entry(entry)
    
    def log_error(self, error: str, details: Optional[Dict[str, Any]] = None, exception: Optional[Exception] = None):
        """Log an error"""
        entry = {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "details": details or {},
            "exception": str(exception) if exception else None
        }
        self._write_entry(entry)
    
    def log_resource_created(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        """Log AWS resource creation"""
        entry = {
            "type": "resource_created",
            "timestamp": datetime.utcnow().isoformat(),
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {}
        }
        self._write_entry(entry)
    
    def log_deployment_complete(self, success: bool, deployment_url: Optional[str] = None, resources: Optional[List[Dict[str, Any]]] = None):
        """Log deployment completion"""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        entry = {
            "type": "deployment_complete",
            "timestamp": end_time.isoformat(),
            "success": success,
            "duration_seconds": duration,
            "deployment_url": deployment_url,
            "resources_created": resources or []
        }
        self._write_entry(entry)
    
    async def finalize_and_upload(self) -> str:
        """Finalize logging and upload to S3"""
        # Write footer
        footer = {
            "type": "log_end",
            "timestamp": datetime.utcnow().isoformat(),
            "total_entries": len(self.log_entries)
        }
        self._write_entry(footer)
        
        # Upload to S3
        download_url = await self.structured_logger.upload_logs_to_s3(
            self.session_id, 
            self.log_file
        )
        
        # Clean up local file
        try:
            self.log_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to clean up local log file: {e}")
        
        return download_url
    
    def get_log_summary(self) -> Dict[str, Any]:
        """Get summary of logs for quick review"""
        summary = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "total_entries": len(self.log_entries),
            "steps": [],
            "errors": [],
            "commands_executed": 0,
            "resources_created": []
        }
        
        for entry in self.log_entries:
            if entry["type"] == "step":
                summary["steps"].append(entry["step"])
            elif entry["type"] == "error":
                summary["errors"].append(entry["error"])
            elif entry["type"] == "command":
                summary["commands_executed"] += 1
            elif entry["type"] == "resource_created":
                summary["resources_created"].append({
                    "type": entry["resource_type"],
                    "id": entry["resource_id"]
                })
        
        return summary


# Global structured logger instance
structured_logger = StructuredLogger()
