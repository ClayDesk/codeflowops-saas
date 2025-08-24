"""
Unified provisioning facade
Wraps existing proven functions with type-safe contracts
"""
import logging
from typing import Dict, Any
from .contracts import AwsCredentials, S3WebsiteTarget, ProvisionResult
from .utils import create_s3_bucket, create_cloudfront_distribution

logger = logging.getLogger(__name__)

def create_s3_bucket_and_cf(creds: AwsCredentials, target: S3WebsiteTarget) -> ProvisionResult:
    """
    Unified S3 + CloudFront provisioning facade
    Uses proven infrastructure functions with type-safe contracts
    """
    try:
        logger.info(f"🚀 FACADE: Starting provisioning for {target.bucket_name}")
        
        # Convert typed credentials to existing format
        credentials = {
            "aws_access_key_id": creds.access_key_id,
            "aws_secret_access_key": creds.secret_access_key,
            "aws_region": creds.region
        }
        
        logger.info(f"🔐 FACADE: Credentials converted, region: {creds.region}")
        logger.info(f"📦 FACADE: Creating S3 bucket and CloudFront for: {target.bucket_name}")
        
        # Step 1: Create S3 bucket using proven function
        logger.info(f"📦 FACADE: Calling create_s3_bucket...")
        bucket_success = create_s3_bucket(
            bucket_name=target.bucket_name,
            region=target.region,
            credentials=credentials
        )
        
        logger.info(f"📦 FACADE: S3 bucket creation result: {bucket_success}")
        
        if not bucket_success:
            error_msg = f"S3 bucket creation failed for: {target.bucket_name}"
            logger.error(f"❌ FACADE: {error_msg}")
            raise Exception(error_msg)
            
        logger.info(f"✅ FACADE: S3 bucket created successfully: {target.bucket_name}")
        
        # Step 2: Create CloudFront distribution using proven function
        logger.info("🌐 FACADE: Creating CloudFront distribution...")
        cloudfront_result = create_cloudfront_distribution(
            bucket_name=target.bucket_name,
            region=target.region,
            credentials=credentials
        )
        
        logger.info(f"🌐 FACADE: CloudFront result: {cloudfront_result}")
        
        # Generate S3 website endpoint
        s3_website_endpoint = f"http://{target.bucket_name}.s3-website-{target.region}.amazonaws.com"
        
        # Extract CloudFront information if successful
        cloudfront_domain = None
        if cloudfront_result.get("success"):
            # Extract domain from URL (remove https://)
            cloudfront_url = cloudfront_result.get("cloudfront_url", "")
            if cloudfront_url.startswith("https://"):
                cloudfront_domain = cloudfront_url[8:]  # Remove "https://"
            logger.info(f"✅ FACADE: CloudFront distribution created: {cloudfront_domain}")
        else:
            logger.warning(f"⚠️ FACADE: CloudFront creation failed, using S3 website hosting: {cloudfront_result.get('error', 'Unknown error')}")
        
        logger.info(f"🎉 FACADE: Infrastructure provisioned successfully for {target.bucket_name}")
        
        result = ProvisionResult(
            bucket=target.bucket_name,
            cloudfront_domain=cloudfront_domain,
            s3_website_endpoint=s3_website_endpoint,
            region=target.region,
            status="success"
        )
        
        logger.info(f"✅ FACADE: Returning result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"❌ FACADE: Provisioning failed for {target.bucket_name}: {e}")
        logger.error(f"❌ FACADE: Exception type: {type(e).__name__}")
        raise Exception(f"FACADE_ERROR: Failed to create S3 bucket and CloudFront: {str(e)}")


def adapt_legacy_credentials(credentials: Dict[str, Any], region: str = "us-east-1") -> AwsCredentials:
    """
    Adapter to convert legacy credential formats to typed contracts
    Handles various input formats from API
    """
    # Handle different key names that might come from API
    access_key = (
        credentials.get("aws_access_key_id") or 
        credentials.get("access_key_id") or
        credentials.get("aws_access_key")
    )
    
    secret_key = (
        credentials.get("aws_secret_access_key") or
        credentials.get("secret_access_key") or
        credentials.get("aws_secret_key")
    )
    
    if not access_key or not secret_key:
        raise ValueError("Missing required AWS credentials")
    
    credential_region = (
        credentials.get("aws_region") or
        credentials.get("region") or
        region
    )
    
    return AwsCredentials(
        access_key_id=access_key,
        secret_access_key=secret_key,
        session_token=credentials.get("aws_session_token"),
        region=credential_region
    )
