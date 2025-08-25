"""
Dedicated React Deployment Module with AWS CodeBuild
====================================================

Scalable React deployment pipeline using AWS CodeBuild for builds.
Handles repository analysis, AWS CodeBuild orchestration, and deployment.
Designed for thousands of concurrent users.
"""

import os
import json
import logging
import subprocess
import tempfile
import shutil
import uuid
import time
from typing import Dict, Any, Optional, Tuple
import requests
import boto3
from botocore.exceptions import ClientError

# Import the existing CloudFront creation utility
from core.utils import create_cloudfront_distribution

# Import the new CodeBuild manager
from aws_codebuild_manager import CodeBuildManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ReactDeployer:
    """Dedicated React deployment handler"""
    
    def __init__(self):
        self.temp_dir = None
        self.repo_path = None
        self.build_output_path = None
        
    def analyze_react_repository(self, repository_url: str) -> Dict[str, Any]:
        """
        Analyze a GitHub repository to determine if it's a React project
        and extract build configuration.
        """
        logger.info(f"🔍 Analyzing React repository: {repository_url}")
        
        try:
            # Create temporary directory for analysis
            self.temp_dir = tempfile.mkdtemp(prefix="react_deploy_")
            self.repo_path = os.path.join(self.temp_dir, "repo")
            
            # Clone repository
            logger.info("📥 Cloning repository...")
            
            # Determine if we're on Windows and use shell=True for commands
            import platform
            is_windows = platform.system() == 'Windows'
            
            clone_result = subprocess.run([
                "git", "clone", "--depth", "1", repository_url, self.repo_path
            ], capture_output=True, text=True, timeout=120, shell=is_windows)
            
            if clone_result.returncode != 0:
                raise Exception(f"Git clone failed: {clone_result.stderr}")
            
            # Check for package.json
            package_json_path = os.path.join(self.repo_path, "package.json")
            if not os.path.exists(package_json_path):
                raise Exception("No package.json found - not a Node.js/React project")
            
            # Parse package.json
            with open(package_json_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Check for React dependencies
            dependencies = package_data.get("dependencies", {})
            dev_dependencies = package_data.get("devDependencies", {})
            all_deps = {**dependencies, **dev_dependencies}
            
            react_indicators = ["react", "react-dom", "react-scripts", "@types/react"]
            found_react_deps = [dep for dep in react_indicators if dep in all_deps]
            
            if not found_react_deps:
                raise Exception("No React dependencies found - not a React project")
            
            # Get build configuration
            scripts = package_data.get("scripts", {})
            build_script = scripts.get("build", "npm run build")
            
            analysis = {
                "analysis_id": str(uuid.uuid4()),
                "repository_url": repository_url,
                "framework": "React",
                "language": "JavaScript",
                "build_tool": "npm",
                "build_script": build_script,
                "dependencies": list(all_deps.keys())[:20],  # Limit for display
                "react_dependencies": found_react_deps,
                "status": "success"
            }
            
            logger.info(f"✅ React project confirmed! Found: {', '.join(found_react_deps)}")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Repository analysis failed: {e}")
            self._cleanup()
            return {
                "status": "error",
                "error": str(e)
            }
    
    def deploy_react_app(self, analysis_id: str, aws_credentials: Dict[str, str], 
                        repository_url: str, project_name: str) -> Dict[str, Any]:
        """
        Deploy a React application using AWS CodeBuild + S3 + CloudFront
        """
        logger.info(f"🚀 Starting scalable React deployment for: {project_name}")
        
        try:
            # Generate unique identifiers
            deployment_id = analysis_id
            s3_bucket_name = f"{project_name.lower().replace('_', '-')}-{deployment_id[:8]}"
            
            # Step 1: Initialize CodeBuild manager
            logger.info("🏗️ Initializing AWS CodeBuild...")
            codebuild_manager = CodeBuildManager(aws_credentials)
            
            # Step 2: Create S3 bucket for build artifacts and hosting
            logger.info(f"🪣 Creating S3 bucket: {s3_bucket_name}")
            s3_result = self._create_s3_bucket(s3_bucket_name, aws_credentials)
            if not s3_result["success"]:
                return {
                    "status": "error",
                    "stage": "s3_setup",
                    "error": s3_result["error"]
                }
            
            # Step 3: Create CodeBuild project
            logger.info("📋 Creating CodeBuild project...")
            project_name_cb = codebuild_manager.create_codebuild_project(
                deployment_id=deployment_id,
                repository_url=repository_url,
                project_name=project_name,
                s3_bucket=s3_bucket_name
            )
            
            # Step 4: Start build
            logger.info("🔨 Starting React build in AWS...")
            build_id = codebuild_manager.start_build(project_name_cb, deployment_id)
            
            # Step 5: Wait for build completion
            logger.info("⏳ Waiting for build completion...")
            build_result = codebuild_manager.wait_for_build_completion(build_id, timeout_minutes=30)
            
            if build_result['status'] != 'SUCCEEDED':
                # Cleanup resources on build failure
                codebuild_manager.cleanup_build_resources(deployment_id, project_name_cb)
                return {
                    "status": "error",
                    "stage": "codebuild",
                    "error": f"Build failed: {build_result.get('error', build_result['status'])}"
                }
            
            logger.info("✅ React build completed successfully!")
            
            # Step 6: Configure S3 for web hosting
            logger.info("🌐 Configuring S3 web hosting...")
            hosting_result = self._configure_s3_hosting(s3_bucket_name, aws_credentials)
            if not hosting_result["success"]:
                codebuild_manager.cleanup_build_resources(deployment_id, project_name_cb)
                return {
                    "status": "error", 
                    "stage": "s3_hosting",
                    "error": hosting_result["error"]
                }
            
            # Step 7: Create CloudFront distribution
            logger.info("☁️ Creating CloudFront distribution...")
            cloudfront_result = self._create_cloudfront_distribution(s3_bucket_name, aws_credentials)
            
            # Step 8: Cleanup CodeBuild resources
            logger.info("🧹 Cleaning up build resources...")
            codebuild_manager.cleanup_build_resources(deployment_id, project_name_cb)
            
            # Final deployment result
            deployment_result = {
                "deployment_id": deployment_id,
                "status": "success", 
                "website_url": hosting_result["website_url"],
                "s3_bucket": s3_bucket_name,
                "cloudfront_url": cloudfront_result.get("cloudfront_url"),
                "distribution_id": cloudfront_result.get("distribution_id"),
                "build_method": "aws_codebuild",
                "build_id": build_id
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
            
            logger.info(f"✅ S3 bucket created: {bucket_name}")
            return {"success": True, "bucket_name": bucket_name}
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                logger.info(f"✅ S3 bucket already exists: {bucket_name}")
                return {"success": True, "bucket_name": bucket_name}
            else:
                logger.error(f"❌ S3 bucket creation failed: {e}")
                return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ S3 bucket creation failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _configure_s3_hosting(self, bucket_name: str, aws_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Configure S3 bucket for static website hosting"""
        try:
            region = aws_credentials.get('aws_region', 'us-east-1')
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_credentials['aws_access_key_id'],
                aws_secret_access_key=aws_credentials['aws_secret_access_key'],
                region_name=region
            )
            
            # Configure public access
            s3_client.delete_public_access_block(Bucket=bucket_name)
            
            # Configure website hosting
            s3_client.put_bucket_website(
                Bucket=bucket_name,
                WebsiteConfiguration={
                    'IndexDocument': {'Suffix': 'index.html'},
                    'ErrorDocument': {'Key': 'index.html'}  # For SPA routing
                }
            )
            
            # Set bucket policy for public read
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
            website_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
            
            logger.info(f"✅ S3 hosting configured: {website_url}")
            return {
                "success": True,
                "website_url": website_url,
                "bucket_name": bucket_name
            }
            
        except ClientError as e:
            logger.error(f"❌ S3 hosting configuration failed: {e}")
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"❌ S3 hosting configuration failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_cloudfront_distribution(self, bucket_name: str, aws_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Create CloudFront distribution for the S3 bucket"""
        try:
            region = aws_credentials.get('aws_region', 'us-east-1')
            origin_domain = f"{bucket_name}.s3-website-{region}.amazonaws.com"
            
            # Use existing CloudFront utility
            distribution_result = create_cloudfront_distribution(
                origin_domain=origin_domain,
                aws_credentials=aws_credentials
            )
            
            if distribution_result.get("success"):
                logger.info(f"✅ CloudFront created: {distribution_result.get('cloudfront_url')}")
                return {
                    "cloudfront_url": distribution_result.get("cloudfront_url"),
                    "distribution_id": distribution_result.get("distribution_id")
                }
            else:
                logger.warning(f"⚠️ CloudFront creation failed: {distribution_result.get('error')}")
                return {"cloudfront_error": distribution_result.get("error")}
                
        except Exception as e:
            logger.warning(f"⚠️ CloudFront creation failed: {e}")
            return {"cloudfront_error": str(e)}
            
            logger.info(f"✅ React deployment successful!")
            logger.info(f"🌐 Website URL: {deployment_result['website_url']}")
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"❌ React deployment failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            self._cleanup()
    
    def _build_react_app(self) -> Dict[str, Any]:
        """Build the React application using yarn (more reliable than npm)"""
        logger.info("🔨 Building React application with yarn...")
        
        try:
            # Set up enhanced environment for React builds
            env = os.environ.copy()
            env.update({
                'NODE_OPTIONS': '--max-old-space-size=4096',  # 4GB memory
                'GENERATE_SOURCEMAP': 'false',               # Skip source maps
                'CI': 'true',                                # CI mode
                'FORCE_COLOR': '0',                          # No colors
                'YARN_SILENT': '1',                          # Reduce yarn noise
                'YARN_PROGRESS': 'false'                     # No progress bars
            })
            
            # Determine if we're on Windows and use shell=True for commands
            import platform
            is_windows = platform.system() == 'Windows'
            
            # Step 1: Install dependencies with yarn
            logger.info("📦 Installing dependencies with yarn...")
            install_result = subprocess.run([
                "yarn", "install", "--frozen-lockfile", "--non-interactive"
            ], cwd=self.repo_path, capture_output=True, text=True, 
               timeout=600, env=env, shell=is_windows)  # 10 minute timeout
            
            if install_result.returncode != 0:
                # Fallback to npm if yarn fails
                logger.warning("⚠️ Yarn install failed, falling back to npm...")
                install_result = subprocess.run([
                    "npm", "install"
                ], cwd=self.repo_path, capture_output=True, text=True, 
                   timeout=600, env=env, shell=is_windows)
                
                if install_result.returncode != 0:
                    raise Exception(f"Both yarn and npm install failed: {install_result.stderr}")
                
                # Use npm for build too
                build_tool = "npm"
                build_cmd = ["npm", "run", "build"]
            else:
                build_tool = "yarn"
                build_cmd = ["yarn", "build"]
            
            logger.info(f"✅ Dependencies installed successfully with {build_tool}")
            
            # Step 2: Build the application
            logger.info(f"🏗️ Building React application with {build_tool}...")
            build_result = subprocess.run(
                build_cmd, cwd=self.repo_path, capture_output=True, text=True,
                timeout=900, env=env, shell=is_windows  # 15 minute timeout
            )
            
            if build_result.returncode != 0:
                raise Exception(f"{build_tool} build failed: {build_result.stderr}")
            
            # Step 3: Locate build output
            possible_build_dirs = ["build", "dist", "out"]
            build_path = None
            
            for build_dir in possible_build_dirs:
                potential_path = os.path.join(self.repo_path, build_dir)
                if os.path.exists(potential_path) and os.path.isdir(potential_path):
                    # Check if it has index.html or other web files
                    if (os.path.exists(os.path.join(potential_path, "index.html")) or
                        any(f.endswith(('.html', '.js', '.css')) for f in os.listdir(potential_path))):
                        build_path = potential_path
                        break
            
            if not build_path:
                raise Exception("Build output directory not found")
            
            self.build_output_path = build_path
            logger.info(f"✅ Build completed successfully: {os.path.basename(build_path)}")
            
            return {
                "success": True,
                "build_path": build_path,
                "build_dir": os.path.basename(build_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Build failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _deploy_to_aws(self, aws_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Deploy built React app to AWS S3 + CloudFront"""
        logger.info("☁️ Deploying to AWS...")
        
        try:
            # Generate unique bucket name
            bucket_name = f"react-app-{str(uuid.uuid4())[:8]}"
            region = aws_credentials.get("aws_region", "us-east-1")
            
            # Set AWS credentials in environment
            aws_env = os.environ.copy()
            aws_env.update({
                "AWS_ACCESS_KEY_ID": aws_credentials["aws_access_key_id"],
                "AWS_SECRET_ACCESS_KEY": aws_credentials["aws_secret_access_key"],
                "AWS_DEFAULT_REGION": region
            })
            
            # Step 1: Create S3 bucket
            logger.info(f"📦 Creating S3 bucket: {bucket_name}")
            create_bucket_cmd = [
                "aws", "s3", "mb", f"s3://{bucket_name}",
                "--region", region
            ]
            
            bucket_result = subprocess.run(
                create_bucket_cmd, capture_output=True, text=True,
                env=aws_env, timeout=60
            )
            
            if bucket_result.returncode != 0:
                raise Exception(f"S3 bucket creation failed: {bucket_result.stderr}")
            
            # Step 1.5: Disable Block Public Access to allow public bucket policy
            logger.info("🔓 Disabling Block Public Access settings...")
            public_access_result = subprocess.run([
                "aws", "s3api", "delete-public-access-block",
                "--bucket", bucket_name
            ], capture_output=True, text=True, env=aws_env, timeout=60)
            
            if public_access_result.returncode != 0:
                logger.warning(f"Public access warning: {public_access_result.stderr}")
            
            # Step 2: Configure bucket for static website hosting
            logger.info("🌐 Configuring static website hosting...")
            website_config = {
                "IndexDocument": {"Suffix": "index.html"},
                "ErrorDocument": {"Key": "index.html"}  # SPA fallback
            }
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(website_config, f)
                config_file = f.name
            
            try:
                website_result = subprocess.run([
                    "aws", "s3api", "put-bucket-website",
                    "--bucket", bucket_name,
                    "--website-configuration", f"file://{config_file}"
                ], capture_output=True, text=True, env=aws_env, timeout=60)
                
                if website_result.returncode != 0:
                    logger.warning(f"Website configuration warning: {website_result.stderr}")
            finally:
                os.unlink(config_file)
            
            # Step 3: Upload files to S3 - ENHANCED
            logger.info("📤 Uploading files to S3...")
            
            # Count files before upload for verification
            all_files = []
            for root, dirs, files in os.walk(self.build_output_path):
                for file in files:
                    all_files.append(os.path.join(root, file))
            
            logger.info(f"📊 Found {len(all_files)} files to upload:")
            for f in all_files[:5]:  # Show first 5 files
                rel_path = os.path.relpath(f, self.build_output_path)
                logger.info(f"   📄 {rel_path}")
            if len(all_files) > 5:
                logger.info(f"   ... and {len(all_files) - 5} more files")
            
            # Simplified S3 sync command - removing potential timeout issues  
            sync_result = subprocess.run([
                "aws", "s3", "sync", self.build_output_path, f"s3://{bucket_name}",
                "--delete"
            ], capture_output=True, text=True, env=aws_env, timeout=300)  # 5 minute timeout
            
            if sync_result.returncode != 0:
                logger.error(f"❌ S3 sync failed: {sync_result.stderr}")
                logger.error(f"   Standard output: {sync_result.stdout}")
                raise Exception(f"S3 sync failed: {sync_result.stderr}")
            
            logger.info("✅ S3 sync completed successfully!")
            logger.info(f"📝 Sync output: {sync_result.stdout}")
            
            # Verify upload by listing S3 bucket contents
            logger.info("🔍 Verifying S3 upload...")
            verify_result = subprocess.run([
                "aws", "s3", "ls", f"s3://{bucket_name}/", "--recursive"
            ], capture_output=True, text=True, env=aws_env, timeout=60)
            
            if verify_result.returncode == 0:
                s3_lines = [line for line in verify_result.stdout.split('\n') if line.strip()]
                logger.info(f"✅ Verification: {len(s3_lines)} files confirmed in S3:")
                
                for line in s3_lines[:5]:
                    if line.strip():
                        filename = line.split()[-1] if line.split() else 'unknown'
                        logger.info(f"   📄 {filename}")
                if len(s3_lines) > 5:
                    logger.info(f"   ... and {len(s3_lines) - 5} more files in S3")
                    
                # Check if we uploaded the expected number of files
                if len(s3_lines) >= len(all_files) * 0.9:  # Allow 10% tolerance
                    logger.info("✅ File count verification passed!")
                else:
                    logger.warning(f"⚠️ File count mismatch: Expected ~{len(all_files)}, found {len(s3_lines)} in S3")
            else:
                logger.warning(f"⚠️ Could not verify S3 upload: {verify_result.stderr}")
            
            # Step 4: Make bucket public
            logger.info("🔓 Configuring public access...")
            public_policy = {
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
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(public_policy, f)
                policy_file = f.name
            
            try:
                policy_result = subprocess.run([
                    "aws", "s3api", "put-bucket-policy",
                    "--bucket", bucket_name,
                    "--policy", f"file://{policy_file}"
                ], capture_output=True, text=True, env=aws_env, timeout=60)
                
                if policy_result.returncode != 0:
                    logger.warning(f"Bucket policy warning: {policy_result.stderr}")
            finally:
                os.unlink(policy_file)
            
            # Generate website URL
            website_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
            
            logger.info(f"✅ AWS S3 deployment successful!")
            logger.info(f"🌐 S3 Website URL: {website_url}")
            
            # Create CloudFront distribution for global CDN
            logger.info("🌍 Creating CloudFront distribution...")
            cloudfront_result = create_cloudfront_distribution(
                bucket_name=bucket_name,
                region=region,
                credentials=aws_credentials
            )
            
            if cloudfront_result.get("success"):
                cloudfront_url = cloudfront_result.get("cloudfront_url")
                distribution_id = cloudfront_result.get("distribution_id")
                logger.info(f"✅ CloudFront distribution created: {distribution_id}")
                logger.info(f"🌐 CloudFront URL: {cloudfront_url}")
                
                return {
                    "success": True,
                    "s3_bucket": bucket_name,
                    "website_url": website_url,
                    "cloudfront_url": cloudfront_url,
                    "distribution_id": distribution_id,
                    "region": region
                }
            else:
                # CloudFront failed, but S3 deployment succeeded
                error = cloudfront_result.get("error", "Unknown CloudFront error")
                logger.warning(f"⚠️ CloudFront creation failed: {error}")
                logger.info("✅ Deployment successful with S3 only (no CDN)")
                
                return {
                    "success": True,
                    "s3_bucket": bucket_name,
                    "website_url": website_url,
                    "cloudfront_url": None,
                    "cloudfront_error": error,
                    "region": region
                }
            
        except Exception as e:
            logger.error(f"❌ AWS deployment failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _cleanup(self):
        """Clean up temporary directories"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info("🧹 Temporary files cleaned up")
            except Exception as e:
                logger.warning(f"Cleanup warning: {e}")
    
    def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get the status of a React deployment"""
        # This would typically check a database or cache
        # For now, return a simple status
        return {
            "deployment_id": deployment_id,
            "status": "completed",
            "type": "react"
        }

# Convenience functions for direct use
def analyze_react_repo(repository_url: str) -> Dict[str, Any]:
    """Analyze a React repository"""
    deployer = ReactDeployer()
    return deployer.analyze_react_repository(repository_url)

def deploy_react_app(analysis_id: str, aws_credentials: Dict[str, str]) -> Dict[str, Any]:
    """Deploy a React application"""
    deployer = ReactDeployer()
    # Note: In a real implementation, you'd retrieve the analysis from storage
    # For now, we'll need to re-analyze or pass the repo URL
    return deployer.deploy_react_app(analysis_id, aws_credentials)
