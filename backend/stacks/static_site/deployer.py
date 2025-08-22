"""
Static site deployer - uploads files to S3
"""
import time
import logging
from core.models import StackPlan, BuildResult, ProvisionResult, DeployResult
from core.utils import sync_to_s3

logger = logging.getLogger(__name__)

class StaticSiteDeployer:
    """Deploys static sites to S3"""
    
    def deploy(self, plan: StackPlan, build: BuildResult, provision: ProvisionResult, credentials: dict) -> DeployResult:
        """
        Deploy static site files to S3 bucket
        """
        start_time = time.time()
        
        try:
            logger.info("🚀 Deploying static site to S3...")
            
            bucket_name = provision.outputs["bucket_name"]
            website_url = provision.outputs["website_url"]
            
            logger.info(f"📤 Uploading files to bucket: {bucket_name}")
            
            # Sync files to S3
            success = sync_to_s3(build.artifact_dir, bucket_name, credentials)
            
            if not success:
                return DeployResult(
                    success=False,
                    live_url="",
                    error_message="Failed to upload files to S3"
                )
            
            deploy_time = time.time() - start_time
            
            # Prepare deployment details
            details = {
                "bucket_name": bucket_name,
                "region": provision.outputs["region"],
                "files_uploaded": True,
                "entry_point": plan.config.get("entry_point", "index.html"),
                "deployment_type": "s3_static_hosting"
            }
            
            # Add build metadata if available
            if build.metadata:
                details.update({
                    "total_assets": build.metadata.get("total_assets", 0),
                    "html_files": build.metadata.get("html_files", 0),
                    "css_files": build.metadata.get("css_files", 0),
                    "js_files": build.metadata.get("js_files", 0)
                })
            
            logger.info(f"✅ Static site deployed successfully in {deploy_time:.2f}s")
            logger.info(f"🌐 Live at: {website_url}")
            
            return DeployResult(
                success=True,
                live_url=website_url,
                details=details,
                deploy_time_seconds=deploy_time
            )
            
        except Exception as e:
            logger.error(f"❌ Static site deployment failed: {e}")
            return DeployResult(
                success=False,
                live_url="",
                error_message=f"Deployment failed: {str(e)}"
            )
    
    def validate_deployment(self, deploy: DeployResult) -> bool:
        """
        Validate that the static site is accessible
        """
        try:
            import requests
            
            # Try to access the website
            response = requests.get(deploy.live_url, timeout=10)
            success = response.status_code == 200
            
            if success:
                logger.info(f"✅ Deployment validation successful: {deploy.live_url}")
            else:
                logger.warning(f"⚠️ Deployment validation failed: HTTP {response.status_code}")
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Deployment validation error: {e}")
            return False
    
    def rollback(self, deploy: DeployResult, credentials: dict) -> bool:
        """
        Rollback static site deployment (not really applicable for static sites)
        """
        logger.info("🔄 Static site rollback not implemented (no versioning)")
        return True
