"""
Static site provisioner - creates S3 + CloudFront infrastructure for static sites
Uses SAME approach as React plugin: public S3 bucket with website configuration + CloudFront
"""
import time
import logging
from pathlib import Path
from core.models import StackPlan, BuildResult, ProvisionResult
from core.utils import create_s3_bucket, create_cloudfront_distribution, ensure_static_website_ready

logger = logging.getLogger(__name__)

class StaticSiteProvisioner:
    """Provisions AWS infrastructure for static sites using S3 + CloudFront (same as React plugin)"""
    
    def _generate_bucket_name(self, prefix: str) -> str:
        """Generate a unique bucket name"""
        import uuid
        return f"{prefix}-{str(uuid.uuid4())[:8]}"
    
    def provision(self, plan: StackPlan, build: BuildResult, credentials: dict) -> ProvisionResult:
        """
        Create S3 bucket and CloudFront distribution for static site hosting
        Uses SAME approach as React plugin: public S3 + website configuration + CloudFront
        """
        start_time = time.time()
        
        try:
            logger.info("☁️ Provisioning static site infrastructure (same as React approach)...")
            
            # Generate unique bucket name
            bucket_name = self._generate_bucket_name("static-site")
            region = credentials.get("aws_region", "us-east-1")
            
            logger.info(f"📦 Creating S3 bucket with website hosting: {bucket_name}")
            
            # Create S3 bucket with website hosting (SAME AS REACT PLUGIN)
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
            
            # CRITICAL: Configure bucket for static website hosting
            logger.info("🔧 Configuring S3 bucket for static website hosting...")
            try:
                ensure_static_website_ready(
                    bucket_name=bucket_name,
                    region=region, 
                    credentials=credentials
                )
                logger.info("✅ S3 bucket configured for static website hosting")
            except Exception as e:
                logger.error(f"❌ Failed to configure bucket for website hosting: {e}")
                return ProvisionResult(
                    success=False,
                    infrastructure_id=bucket_name,
                    outputs={"bucket_name": bucket_name},
                    error_message=f"Failed to configure bucket for website hosting: {str(e)}",
                    provision_time_seconds=time.time() - start_time
                )
            
            # Create CloudFront distribution (SAME AS REACT PLUGIN)
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
            
            # Prepare outputs (same structure as React plugin)
            outputs = {
                "bucket_name": bucket_name,
                "region": region,
                "distribution_id": distribution_id,
                "website_url": cloudfront_url,
                "infrastructure_type": "s3_cloudfront_static"
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
                    "stack_type": "static_site"
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Static site infrastructure provisioning failed: {e}")
            return ProvisionResult(
                success=False,
                infrastructure_id="",
                outputs={},
                error_message=f"Provisioning failed: {str(e)}",
                provision_time_seconds=time.time() - start_time
            )
    
    def destroy(self, provision: ProvisionResult, credentials: dict) -> bool:
        """
        Clean up static site infrastructure
        """
        try:
            # TODO: Implement S3 bucket cleanup
            # For now, just log - in production you'd want to:
            # 1. Empty S3 bucket
            # 2. Delete S3 bucket
            # 3. Clean up any CloudFront distributions
            
            bucket_name = provision.outputs.get("bucket_name")
            logger.info(f"🧹 Would clean up bucket: {bucket_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Static site cleanup failed: {e}")
            return False
