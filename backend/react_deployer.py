"""
Dedicated React Deployment Module with DirectReactBuilder
========================================================

Scalable React deployment pipeline using DirectReactBuilder + S3 + CloudFront.
Handles repository analysis, direct Python building, and AWS deployment.
No AWS CodeBuild required - faster and more reliable.
"""

import os
import json
import logging
import tempfile
import shutil
import uuid
import zipfile
from typing import Dict, Any, Optional, Tuple
import requests
import boto3
from botocore.exceptions import ClientError

# Import the existing CloudFront creation utility
from core.utils import create_cloudfront_distribution

# Import the DirectReactBuilder
from direct_react_builder import DirectReactBuilder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReactDeployer:
    """Dedicated React deployment handler using DirectReactBuilder"""
    
    def __init__(self):
        self.temp_dir = None
        self.last_analyzed_repo = None
        
    def analyze_react_repository(self, repository_url: str) -> Dict[str, Any]:
        """
        Analyze a GitHub repository to determine if it's a React project
        and extract build configuration.
        """
        logger.info(f"🔍 Analyzing React repository: {repository_url}")
        self.last_analyzed_repo = repository_url
        
        temp_dir = None
        try:
            # Use DirectReactBuilder to analyze the repository
            builder = DirectReactBuilder()
            
            # Clone temporarily for analysis
            temp_dir = tempfile.mkdtemp(prefix="react_analysis_")
            project_dir = os.path.join(temp_dir, 'repo')
            
            if not builder.clone_repository(repository_url, project_dir):
                return {
                    'status': 'error',
                    'error': 'Failed to clone repository for analysis'
                }
            
            # Detect package manager and build tool
            package_manager = builder.detect_package_manager(project_dir)
            build_info = builder.detect_build_tool(project_dir)
                
            # Check if it's a React project
            package_json_path = os.path.join(project_dir, 'package.json')
            is_react = False
            react_version = None
            
            if os.path.exists(package_json_path):
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    dependencies = package_data.get('dependencies', {})
                    dev_dependencies = package_data.get('devDependencies', {})
                    
                    # Check for React in dependencies
                    if 'react' in dependencies:
                        is_react = True
                        react_version = dependencies['react']
                    elif 'react' in dev_dependencies:
                        is_react = True
                        react_version = dev_dependencies['react']
            
            if not is_react:
                return {
                    'status': 'error',
                    'error': 'Repository does not appear to be a React project'
                }
            
            return {
                'status': 'success',
                'repository_url': repository_url,
                'package_manager': package_manager,
                'build_tool': build_info['build_tool'],
                'output_directory': build_info['output_dir'],
                'react_version': react_version,
                'build_script': build_info['build_script'],
                'scripts': build_info['scripts']
            }
                    
        except Exception as e:
            logger.error(f"❌ Repository analysis failed: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
        finally:
            # Cleanup analysis temp directory
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
    
    def deploy_react_app(self, deployment_id: str, aws_credentials: Dict[str, str], 
                        repository_url: str = None) -> Dict[str, Any]:
        """
        Deploy a React application using DirectReactBuilder + S3 + CloudFront
        """
        # Use repository_url from previous analysis if not provided
        if not repository_url:
            repository_url = self.last_analyzed_repo
            if not repository_url:
                return {
                    "status": "error",
                    "stage": "validation",
                    "error": "No repository URL provided and no previous analysis found"
                }
        
        logger.info(f"🚀 Starting DirectReactBuilder deployment")
        logger.info(f"📦 Repository: {repository_url}")
        logger.info(f"🆔 Deployment ID: {deployment_id}")
        
        try:
            # Generate S3 bucket name
            safe_name = repository_url.split('/')[-1].replace('.git', '').lower()
            s3_bucket_name = f"react-app-{safe_name[:10]}-{deployment_id[:8]}"
            
            # Ensure valid bucket name
            import re
            s3_bucket_name = re.sub(r'[^a-z0-9-]', '', s3_bucket_name)
            if not s3_bucket_name[0].isalnum():
                s3_bucket_name = f"app-{s3_bucket_name[1:]}"
            
            logger.info(f"🪣 S3 Bucket: {s3_bucket_name}")
            
            # Step 1: Build React app using DirectReactBuilder
            logger.info("🔨 Building React app with DirectReactBuilder...")
            builder = DirectReactBuilder()
            build_result = builder.build_react_from_repo(repository_url, deployment_id)
            
            if build_result['status'] != 'success':
                return {
                    "status": "error",
                    "stage": "react_build",
                    "error": f"React build failed: {build_result['error']}"
                }
            
            logger.info("✅ React build completed successfully!")
            archive_path = build_result['archive_path']
            build_output_path = build_result['build_output_path']
            
            # Step 2: Create S3 bucket for hosting
            logger.info(f"🪣 Creating S3 bucket: {s3_bucket_name}")
            s3_result = self._create_s3_bucket(s3_bucket_name, aws_credentials)
            if not s3_result["success"]:
                return {
                    "status": "error",
                    "stage": "s3_setup",
                    "error": s3_result["error"]
                }
            
            # Step 3: Upload build to S3
            logger.info("📤 Uploading build to S3...")
            upload_result = self._upload_build_to_s3(
                build_output_path, s3_bucket_name, aws_credentials
            )
            if not upload_result["success"]:
                return {
                    "status": "error",
                    "stage": "s3_upload",
                    "error": upload_result["error"]
            }
            
            # Step 4: Configure S3 for web hosting
            logger.info("🌐 Configuring S3 web hosting...")
            hosting_result = self._configure_s3_hosting(s3_bucket_name, aws_credentials)
            if not hosting_result["success"]:
                return {
                    "status": "error", 
                    "stage": "s3_hosting",
                    "error": hosting_result["error"]
                }
            
            # Step 5: Create CloudFront distribution
            logger.info("☁️ Creating CloudFront distribution...")
            cloudfront_result = self._create_cloudfront_distribution(s3_bucket_name, aws_credentials)
            
            # Final deployment result
            deployment_result = {
                "deployment_id": deployment_id,
                "status": "success", 
                "website_url": hosting_result["website_url"],
                "s3_bucket": s3_bucket_name,
                "cloudfront_url": cloudfront_result.get("cloudfront_url"),
                "distribution_id": cloudfront_result.get("distribution_id"),
                "build_method": "direct_react_builder",
                "package_manager": build_result.get("package_manager_used", "unknown"),
                "build_tool": build_result.get("build_tool", "unknown"),
                "repository_url": repository_url
            }
            
            logger.info("🎉 React deployment completed successfully!")
            return deployment_result
            
        except Exception as e:
            logger.error(f"❌ Deployment failed: {e}")
            return {
                "status": "error",
                "stage": "general",
                "error": str(e)
            }
    
    def _create_s3_bucket(self, bucket_name: str, aws_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Create S3 bucket for React app hosting"""
        try:
            region = aws_credentials.get('aws_region', 'us-east-1')
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_credentials['aws_access_key_id'],
                aws_secret_access_key=aws_credentials['aws_secret_access_key'],
                region_name=region
            )
            
            # Create bucket
            if region == 'us-east-1':
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': region}
                )
            
            # Disable public access block to allow public website
            s3_client.delete_public_access_block(Bucket=bucket_name)
            
            logger.info(f"✅ S3 bucket created: {bucket_name}")
            return {"success": True, "bucket_name": bucket_name}
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'BucketAlreadyExists':
                logger.warning(f"⚠️ Bucket {bucket_name} already exists, continuing...")
                return {"success": True, "bucket_name": bucket_name}
            else:
                logger.error(f"❌ S3 bucket creation failed: {e}")
                return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ S3 bucket creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _upload_build_to_s3(self, build_path: str, bucket_name: str, aws_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Upload React build files to S3"""
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_credentials['aws_access_key_id'],
                aws_secret_access_key=aws_credentials['aws_secret_access_key'],
                region_name=aws_credentials.get('aws_region', 'us-east-1')
            )
            
            uploaded_files = 0
            
            # Upload all files from build directory
            for root, dirs, files in os.walk(build_path):
                for file in files:
                    local_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_path, build_path)
                    s3_key = relative_path.replace('\\', '/')  # Ensure forward slashes for S3
                    
                    # Determine content type
                    content_type = 'text/html'
                    if file.endswith('.css'):
                        content_type = 'text/css'
                    elif file.endswith('.js'):
                        content_type = 'application/javascript'
                    elif file.endswith('.json'):
                        content_type = 'application/json'
                    elif file.endswith('.png'):
                        content_type = 'image/png'
                    elif file.endswith('.jpg') or file.endswith('.jpeg'):
                        content_type = 'image/jpeg'
                    elif file.endswith('.svg'):
                        content_type = 'image/svg+xml'
                    
                    # Upload file
                    s3_client.upload_file(
                        local_path, 
                        bucket_name, 
                        s3_key,
                        ExtraArgs={'ContentType': content_type}
                    )
                    uploaded_files += 1
            
            logger.info(f"✅ Uploaded {uploaded_files} files to S3")
            return {"success": True, "files_uploaded": uploaded_files}
            
        except Exception as e:
            logger.error(f"❌ S3 upload failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _configure_s3_hosting(self, bucket_name: str, aws_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Configure S3 bucket for static website hosting"""
        try:
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_credentials['aws_access_key_id'],
                aws_secret_access_key=aws_credentials['aws_secret_access_key'],
                region_name=aws_credentials.get('aws_region', 'us-east-1')
            )
            
            # Configure website hosting
            website_config = {
                'IndexDocument': {'Suffix': 'index.html'},
                'ErrorDocument': {'Key': 'index.html'}  # SPA support
            }
            
            s3_client.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration=website_config
            )
            
            # Set bucket policy for public read access
            bucket_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }
                ]
            }
            
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            
            # Generate website URL
            region = aws_credentials.get('aws_region', 'us-east-1')
            if region == 'us-east-1':
                website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
            else:
                website_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
            
            logger.info(f"✅ S3 website hosting configured: {website_url}")
            return {"success": True, "website_url": website_url}
            
        except Exception as e:
            logger.error(f"❌ S3 hosting configuration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_cloudfront_distribution(self, bucket_name: str, aws_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Create CloudFront distribution for the S3 bucket"""
        try:
            # Use the existing utility from core.utils
            result = create_cloudfront_distribution(bucket_name, aws_credentials)
            
            if result.get("success"):
                logger.info(f"✅ CloudFront distribution created: {result.get('cloudfront_url')}")
                return {
                    "cloudfront_url": result.get("cloudfront_url"),
                    "distribution_id": result.get("distribution_id")
                }
            else:
                logger.warning(f"⚠️ CloudFront creation failed: {result.get('error')}")
                return {
                    "cloudfront_error": result.get("error", "Unknown CloudFront error")
                }
                
        except Exception as e:
            logger.warning(f"⚠️ CloudFront creation failed: {e}")
            return {
                "cloudfront_error": str(e)
            }

# Standalone deployment function for API usage
def deploy_react_app(deployment_id: str, aws_credentials: Dict[str, str], repository_url: str) -> Dict[str, Any]:
    """
    Standalone function for deploying React apps
    """
    deployer = ReactDeployer()
    return deployer.deploy_react_app(deployment_id, aws_credentials, repository_url)

# Test function
def test_react_deployer(repo_url: str = None):
    """Test the ReactDeployer with a React repository"""
    deployer = ReactDeployer()
    
    test_repo = repo_url or "https://github.com/FahimFBA/react-crash"
    
    print("🧪 Testing ReactDeployer")
    print(f"📦 Repository: {test_repo}")
    print("=" * 50)
    
    # Test analysis
    print("🔍 Step 1: Repository Analysis...")
    analysis = deployer.analyze_react_repository(test_repo)
    
    if analysis['status'] == 'success':
        print("✅ Analysis successful!")
        print(f"   Package Manager: {analysis['package_manager']}")
        print(f"   Build Tool: {analysis['build_tool']}")
        print(f"   React Version: {analysis['react_version']}")
        
        # Test deployment (commented out to avoid AWS charges)
        # print("\n🚀 Step 2: Deployment...")
        # aws_creds = {...}  # Add your AWS credentials
        # deployment_id = str(uuid.uuid4())[:8]
        # result = deployer.deploy_react_app(deployment_id, aws_creds)
        # print(f"Deployment result: {result}")
        
        return True
    else:
        print(f"❌ Analysis failed: {analysis['error']}")
        return False

if __name__ == "__main__":
    test_react_deployer()
