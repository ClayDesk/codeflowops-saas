"""
Repository Cleanup Service
Manages temporary repositories and deployment artifacts cleanup
"""

import os
import shutil
import threading
import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CleanupService:
    """
    Background service for cleaning up temporary repositories and deployment artifacts
    """
    
    def __init__(self):
        self.repositories: Dict[str, Dict[str, Any]] = {}
        self.cleanup_thread: Optional[threading.Thread] = None
        self.running = False
        self.cleanup_interval = 3600  # 1 hour
        self.max_age_hours = 24  # 24 hours
        self._lock = threading.RLock()
    
    def start_background_cleanup(self):
        """Start the background cleanup thread"""
        if not self.running:
            self.running = True
            self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
            self.cleanup_thread.start()
            logger.info("✅ Background cleanup service started")
    
    def stop_background_cleanup(self):
        """Stop the background cleanup thread"""
        self.running = False
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5.0)
        logger.info("🛑 Background cleanup service stopped")
    
    def register_repository(self, deployment_id: str, repo_path: str, metadata: Dict[str, Any]):
        """Register a repository for cleanup tracking"""
        with self._lock:
            self.repositories[deployment_id] = {
                "repo_path": repo_path,
                "created_at": datetime.utcnow(),
                "last_activity": datetime.utcnow(),
                "metadata": metadata.copy()
            }
            logger.debug(f"📝 Registered repository for cleanup: {deployment_id} -> {repo_path}")
    
    def update_activity(self, deployment_id: str, status: str):
        """Update the last activity time for a deployment"""
        with self._lock:
            if deployment_id in self.repositories:
                self.repositories[deployment_id]["last_activity"] = datetime.utcnow()
                self.repositories[deployment_id]["metadata"]["status"] = status
                logger.debug(f"🔄 Updated activity for {deployment_id}: {status}")
    
    async def cleanup_user_cancellation(self, deployment_id: str):
        """Clean up resources when user cancels a deployment"""
        with self._lock:
            if deployment_id in self.repositories:
                repo_info = self.repositories[deployment_id]
                repo_path = repo_info["repo_path"]
                
                try:
                    if os.path.exists(repo_path):
                        shutil.rmtree(repo_path)
                        logger.info(f"🗑️ Cleaned up cancelled deployment: {repo_path}")
                    
                    # Remove from tracking
                    del self.repositories[deployment_id]
                    logger.info(f"✅ Removed {deployment_id} from cleanup tracking")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to cleanup {deployment_id}: {e}")
    
    def get_cleanup_stats(self) -> Dict[str, Any]:
        """Get cleanup service statistics"""
        with self._lock:
            now = datetime.utcnow()
            active_count = 0
            old_count = 0
            
            for repo_info in self.repositories.values():
                age = now - repo_info["created_at"]
                if age.total_seconds() > (self.max_age_hours * 3600):
                    old_count += 1
                else:
                    active_count += 1
            
            return {
                "service_running": self.running,
                "total_tracked": len(self.repositories),
                "active_repositories": active_count,
                "old_repositories": old_count,
                "cleanup_interval_minutes": self.cleanup_interval // 60,
                "max_age_hours": self.max_age_hours
            }
    
    def _cleanup_loop(self):
        """Main cleanup loop running in background thread"""
        logger.info(f"🔄 Cleanup loop started (interval: {self.cleanup_interval}s)")
        
        while self.running:
            try:
                self._perform_cleanup()
                time.sleep(self.cleanup_interval)
            except Exception as e:
                logger.error(f"❌ Cleanup loop error: {e}")
                time.sleep(60)  # Wait 1 minute on error
    
    def _perform_cleanup(self):
        """Perform the actual cleanup of old repositories"""
        now = datetime.utcnow()
        to_remove = []
        
        with self._lock:
            for deployment_id, repo_info in self.repositories.items():
                age = now - repo_info["last_activity"]
                
                if age.total_seconds() > (self.max_age_hours * 3600):
                    repo_path = repo_info["repo_path"]
                    
                    try:
                        if os.path.exists(repo_path):
                            shutil.rmtree(repo_path)
                            logger.info(f"🗑️ Cleaned up old repository: {repo_path}")
                        
                        to_remove.append(deployment_id)
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to cleanup {repo_path}: {e}")
            
            # Remove cleaned up repositories from tracking
            for deployment_id in to_remove:
                del self.repositories[deployment_id]
            
            if to_remove:
                logger.info(f"✅ Cleaned up {len(to_remove)} old repositories")
    
    def force_cleanup_all(self):
        """Force cleanup of all tracked repositories (for shutdown)"""
        with self._lock:
            cleaned = 0
            for deployment_id, repo_info in list(self.repositories.items()):
                repo_path = repo_info["repo_path"]
                
                try:
                    if os.path.exists(repo_path):
                        shutil.rmtree(repo_path)
                        cleaned += 1
                    
                    del self.repositories[deployment_id]
                    
                except Exception as e:
                    logger.error(f"❌ Failed to force cleanup {repo_path}: {e}")
            
            logger.info(f"🗑️ Force cleaned {cleaned} repositories")

# Global cleanup service instance
cleanup_service = CleanupService()

# Cleanup on module shutdown
import atexit
atexit.register(lambda: cleanup_service.force_cleanup_all())
