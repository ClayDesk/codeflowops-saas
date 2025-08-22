"""
Core contracts for unified provisioning
Provides typed interfaces to prevent parameter mismatches
"""
from pydantic import BaseModel
from typing import Dict, Optional

class AwsCredentials(BaseModel):
    """Standardized AWS credentials structure"""
    access_key_id: str
    secret_access_key: str
    session_token: Optional[str] = None
    region: str

class S3WebsiteTarget(BaseModel):
    """S3 website configuration target"""
    bucket_name: str
    region: str
    website_index: str = "index.html"
    website_error: str = "index.html"
    tags: Dict[str, str] = {}
    public_read: bool = True
    encryption: Optional[str] = "AES256"

class ProvisionResult(BaseModel):
    """Standardized provisioning result"""
    bucket: str
    cloudfront_domain: Optional[str] = None
    s3_website_endpoint: str
    region: str
    status: str = "success"
