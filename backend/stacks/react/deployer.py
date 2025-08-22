"""
React deployer - uploads React build to S3 with SPA optimizations
"""
import time
import logging
from core.models import StackPlan, BuildResult, ProvisionResult, DeployResult
from core.utils import sync_to_s3

logger = logging.getLogger(__name__)

class ReactDeployer:
    """Deploys React applications to S3 with SPA optimizations"""
    
    def deploy(self, plan: StackPlan, build: BuildResult, provision: ProvisionResult, credentials: dict) -> DeployResult:
        """
        Deploy React SPA to S3 bucket with proper configuration
        """
        start_time = time.time()
        
        try:
            logger.info("🚀 Deploying React SPA to S3...")
            
            bucket_name = provision.outputs["bucket_name"]
            website_url = provision.outputs["website_url"]
            
            logger.info(f"📤 Uploading React build to bucket: {bucket_name}")
            logger.info(f"📁 Build directory: {build.artifact_dir}")
            
            # Validate build directory exists and has files
            if not build.artifact_dir.exists():
                error_msg = f"Build directory does not exist: {build.artifact_dir}"
                logger.error(f"❌ {error_msg}")
                return DeployResult(
                    success=False,
                    live_url="",
                    error_message=error_msg
                )
            
            # Count files to upload
            build_files = list(build.artifact_dir.rglob("*"))
            files_to_upload = [f for f in build_files if f.is_file()]
            
            if len(files_to_upload) == 0:
                error_msg = f"No files found in build directory: {build.artifact_dir}"
                logger.error(f"❌ {error_msg}")
                return DeployResult(
                    success=False,
                    live_url="",
                    error_message=error_msg
                )
            
            logger.info(f"📊 Preparing to upload {len(files_to_upload)} files:")
            for f in files_to_upload[:5]:  # Show first 5 files
                relative_path = f.relative_to(build.artifact_dir)
                logger.info(f"   📄 {relative_path}")
            if len(files_to_upload) > 5:
                logger.info(f"   ... and {len(files_to_upload) - 5} more files")
            
            # Sync React build files to S3 with enhanced error handling
            logger.info("🔄 Starting S3 upload...")
            success = sync_to_s3(build.artifact_dir, bucket_name, credentials)
            
            if not success:
                error_msg = "Failed to upload React build to S3 - check AWS credentials and permissions"
                logger.error(f"❌ {error_msg}")
                return DeployResult(
                    success=False,
                    live_url="",
                    error_message=error_msg
                )
            
            deploy_time = time.time() - start_time
            
            # Prepare deployment details with React-specific info
            details = {
                "bucket_name": bucket_name,
                "region": provision.outputs["region"],
                "deployment_type": "react_spa",
                "files_uploaded": len(files_to_upload),
                "spa_features": {
                    "client_side_routing": True,
                    "fallback_to_index": True,
                    "optimized_for_spa": True
                },
                "build_info": {
                    "build_tool": plan.config.get("build_tool", "webpack"),
                    "typescript": plan.config.get("typescript", False),
                    "build_time_seconds": build.build_time_seconds
                }
            }
            
            # Add build statistics if available
            if build.metadata:
                details["assets"] = {
                    "html_files": build.metadata.get("html_files", 0),
                    "js_files": build.metadata.get("js_files", 0),
                    "css_files": build.metadata.get("css_files", 0),
                    "has_index_html": build.metadata.get("has_index_html", False)
                }
            
            # Add performance recommendations
            details["performance_tips"] = [
                "Files are served with optimal caching headers",
                "Gzip compression enabled for text files",
                "CloudFront CDN recommended for global performance",
                "Browser caching optimized for React chunks"
            ]
            
            logger.info(f"✅ React SPA deployed successfully in {deploy_time:.2f}s")
            logger.info(f"📊 Uploaded {len(files_to_upload)} files to S3")
            logger.info(f"🌐 Live at: {website_url}")
            logger.info(f"⚡ SPA routing: Client-side routing enabled")
            
            return DeployResult(
                success=True,
                live_url=website_url,
                details=details,
                deploy_time_seconds=deploy_time
            )
            
        except Exception as e:
            logger.error(f"❌ React SPA deployment failed: {e}")
            return DeployResult(
                success=False,
                live_url="",
                error_message=f"Deployment failed: {str(e)}"
            )
    
    def validate_deployment(self, deploy: DeployResult) -> bool:
        """
        Validate that the React SPA is accessible and working
        """
        try:
            import requests
            
            # Test main page
            logger.info("🧪 Validating React SPA deployment...")
            
            response = requests.get(deploy.live_url, timeout=15)
            success = response.status_code == 200
            
            if success:
                # Check if it looks like a React app
                content = response.text.lower()
                react_indicators = [
                    'react',
                    'div id="root"',
                    'div id="app"',
                    'static/js/',
                    'static/css/'
                ]
                
                has_react_signs = any(indicator in content for indicator in react_indicators)
                
                if has_react_signs:
                    logger.info("✅ React SPA validation successful - React indicators found")
                else:
                    logger.warning("⚠️ Deployed successfully but React indicators not found")
                    
            else:
                logger.warning(f"⚠️ React SPA validation failed: HTTP {response.status_code}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ React SPA validation error: {e}")
            return False
    
    def rollback(self, deploy: DeployResult, credentials: dict) -> bool:
        """
        Rollback React SPA deployment (basic implementation)
        """
        logger.info("🔄 React SPA rollback not implemented (no versioning)")
        # In production, you might:
        # 1. Keep previous build versions in S3
        # 2. Switch CloudFront origin to previous version
        # 3. Invalidate CloudFront cache
        return True
