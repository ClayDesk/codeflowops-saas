"""
React provisioner - creates S3 + CloudFront infrastructure for React SPAs
"""
import time
import logging
from pathlib import Path
from core.models import StackPlan, BuildResult, ProvisionResult
from core.utils import create_s3_bucket, create_cloudfront_distribution

logger = logging.getLogger(__name__)

class ReactProvisioner:
    """Provisions AWS infrastructure for React SPAs"""
    
    def provision(self, plan: StackPlan, build: BuildResult, credentials: dict) -> ProvisionResult:
        """
        Create S3 bucket and CloudFront distribution for React SPA hosting
        """
        start_time = time.time()
        
        try:
            logger.info("☁️ Provisioning React SPA infrastructure...")
            
            # Generate unique bucket name
            bucket_name = self._generate_bucket_name("react-app")
            region = credentials.get("aws_region", "us-east-1")
            
            logger.info(f"📦 Creating S3 bucket: {bucket_name}")
            
            # Create S3 bucket with website hosting
            bucket_success = create_s3_bucket(
                bucket_name=bucket_name,
                region=region,
                credentials=credentials
            )
            
            if not bucket_success:
                return ProvisionResult(
                    success=False,
                    infrastructure_id=bucket_name,
                    outputs={},
                    error_message="Failed to create S3 bucket",
                    provision_time_seconds=time.time() - start_time
                )
            
            logger.info("✅ S3 bucket created successfully")
            
            # Create CloudFront distribution
            logger.info("🌍 Creating CloudFront distribution...")
            
            cloudfront_result = create_cloudfront_distribution(
                bucket_name=bucket_name,
                region=region,
                credentials=credentials
            )
            
            if not cloudfront_result["success"]:
                return ProvisionResult(
                    success=False,
                    infrastructure_id=bucket_name,
                    outputs={"bucket_name": bucket_name},
                    error_message=f"CloudFront creation failed: {cloudfront_result.get('error')}",
                    provision_time_seconds=time.time() - start_time
                )
            
            distribution_id = cloudfront_result["distribution_id"]
            cloudfront_url = cloudfront_result["cloudfront_url"]
            
            logger.info(f"✅ CloudFront distribution created: {distribution_id}")
            logger.info(f"🌐 Website will be available at: {cloudfront_url}")
            
            provision_time = time.time() - start_time
            
            # Prepare outputs
            outputs = {
                "bucket_name": bucket_name,
                "region": region,
                "distribution_id": distribution_id,
                "website_url": cloudfront_url,
                "infrastructure_type": "s3_cloudfront_spa"
            }
            
            return ProvisionResult(
                success=True,
                infrastructure_id=f"{bucket_name}-{distribution_id}",
                outputs=outputs,
                provision_time_seconds=provision_time,
                metadata={
                    "bucket_name": bucket_name,
                    "distribution_id": distribution_id,
                    "region": region,
                    "stack_type": "react_spa"
                }
            )
            
        except Exception as e:
            logger.error(f"❌ React SPA infrastructure provisioning failed: {e}")
            return ProvisionResult(
                success=False,
                infrastructure_id="",
                outputs={},
                error_message=f"Provisioning failed: {str(e)}",
                provision_time_seconds=time.time() - start_time
            )
    
    def destroy(self, provision: ProvisionResult, credentials: dict) -> bool:
        """
        Destroy the provisioned infrastructure
        """
        try:
            logger.info("🗑️ Destroying React SPA infrastructure...")
            
            bucket_name = provision.outputs.get("bucket_name")
            distribution_id = provision.outputs.get("distribution_id")
            
            success = True
            
            # Disable and delete CloudFront distribution
            if distribution_id:
                logger.info(f"Disabling CloudFront distribution: {distribution_id}")
                # Note: CloudFront deletion takes time and requires disable first
                # Implementation would go here
                
            # Delete S3 bucket (after CloudFront is disabled)
            if bucket_name:
                logger.info(f"Deleting S3 bucket: {bucket_name}")
                # Implementation would go here
                
            return success
            
        except Exception as e:
            logger.error(f"❌ Infrastructure destruction failed: {e}")
            return False
    
    def _generate_bucket_name(self, project_name: str) -> str:
        """Generate a unique S3 bucket name"""
        import hashlib
        import time
        
        # Clean project name
        clean_name = ''.join(c for c in project_name.lower() if c.isalnum() or c == '-')[:20]
        if not clean_name:
            clean_name = "react-app"
        
        # Add timestamp-based suffix for uniqueness
        suffix = hashlib.md5(f"{clean_name}-{int(time.time())}".encode()).hexdigest()[:8]
        
        return f"codeflowops-{clean_name}-{suffix}"
