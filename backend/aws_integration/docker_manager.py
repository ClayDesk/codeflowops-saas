"""
Docker Image Management Utilities
=================================

Utilities for building, tagging, and pushing Docker images to AWS ECR
"""

import subprocess
import logging
import json
import base64
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class DockerImageManager:
    """Manage Docker images for AWS deployment"""
    
    def __init__(self):
        self.docker_available = self._check_docker_availability()
    
    def _check_docker_availability(self) -> bool:
        """Check if Docker is available and running"""
        try:
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ Docker is available")
                return True
            else:
                logger.warning("⚠️ Docker command failed")
                return False
        except FileNotFoundError:
            logger.warning("⚠️ Docker not found in PATH")
            return False
    
    def build_image(self, dockerfile_path: str, image_name: str, build_context: str = ".") -> Dict[str, Any]:
        """Build Docker image"""
        if not self.docker_available:
            return {"success": False, "error": "Docker not available"}
        
        try:
            logger.info(f"🔨 Building Docker image: {image_name}")
            
            cmd = ['docker', 'build', '-t', image_name, '-f', dockerfile_path, build_context]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=build_context)
            
            if result.returncode == 0:
                logger.info(f"✅ Image built successfully: {image_name}")
                return {
                    "success": True,
                    "image_name": image_name,
                    "build_output": result.stdout
                }
            else:
                logger.error(f"❌ Image build failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr,
                    "build_output": result.stdout
                }
        
        except Exception as e:
            logger.error(f"❌ Build exception: {e}")
            return {"success": False, "error": str(e)}
    
    def tag_image(self, source_image: str, target_image: str) -> Dict[str, Any]:
        """Tag Docker image"""
        if not self.docker_available:
            return {"success": False, "error": "Docker not available"}
        
        try:
            logger.info(f"🏷️ Tagging image: {source_image} -> {target_image}")
            
            cmd = ['docker', 'tag', source_image, target_image]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Image tagged successfully")
                return {"success": True, "target_image": target_image}
            else:
                logger.error(f"❌ Image tagging failed: {result.stderr}")
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            logger.error(f"❌ Tagging exception: {e}")
            return {"success": False, "error": str(e)}
    
    def push_to_ecr(self, local_image: str, ecr_uri: str, auth_token: str) -> Dict[str, Any]:
        """Push Docker image to AWS ECR"""
        if not self.docker_available:
            return {"success": False, "error": "Docker not available"}
        
        try:
            # Decode auth token
            username, password = base64.b64decode(auth_token).decode().split(':')
            ecr_registry = ecr_uri.split('/')[0]
            
            # Login to ECR
            logger.info(f"🔐 Logging into ECR: {ecr_registry}")
            login_cmd = ['docker', 'login', '--username', username, '--password-stdin', ecr_registry]
            login_result = subprocess.run(login_cmd, input=password, text=True, capture_output=True)
            
            if login_result.returncode != 0:
                return {"success": False, "error": f"ECR login failed: {login_result.stderr}"}
            
            # Tag image for ECR
            tag_result = self.tag_image(local_image, ecr_uri)
            if not tag_result["success"]:
                return tag_result
            
            # Push image
            logger.info(f"📤 Pushing image to ECR: {ecr_uri}")
            push_cmd = ['docker', 'push', ecr_uri]
            push_result = subprocess.run(push_cmd, capture_output=True, text=True)
            
            if push_result.returncode == 0:
                logger.info(f"✅ Image pushed successfully to ECR")
                return {
                    "success": True,
                    "ecr_uri": ecr_uri,
                    "push_output": push_result.stdout
                }
            else:
                logger.error(f"❌ Image push failed: {push_result.stderr}")
                return {
                    "success": False,
                    "error": push_result.stderr,
                    "push_output": push_result.stdout
                }
        
        except Exception as e:
            logger.error(f"❌ ECR push exception: {e}")
            return {"success": False, "error": str(e)}
    
    def get_image_info(self, image_name: str) -> Dict[str, Any]:
        """Get Docker image information"""
        if not self.docker_available:
            return {"success": False, "error": "Docker not available"}
        
        try:
            cmd = ['docker', 'inspect', image_name]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                image_data = json.loads(result.stdout)[0]
                return {
                    "success": True,
                    "size": image_data.get("Size", 0),
                    "created": image_data.get("Created"),
                    "architecture": image_data.get("Architecture"),
                    "os": image_data.get("Os")
                }
            else:
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cleanup_image(self, image_name: str) -> Dict[str, Any]:
        """Remove Docker image"""
        if not self.docker_available:
            return {"success": False, "error": "Docker not available"}
        
        try:
            cmd = ['docker', 'rmi', image_name, '--force']
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"🗑️ Removed image: {image_name}")
                return {"success": True}
            else:
                # Don't treat as error if image doesn't exist
                if "No such image" in result.stderr:
                    return {"success": True}
                return {"success": False, "error": result.stderr}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
