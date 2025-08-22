"""
Dedicated React Deployment Module
=================================

Simplified React deployment pipeline specifically for React applications.
Handles repository analysis, build process, and AWS deployment for React projects.
"""

import os
import json
import logging
import subprocess
import tempfile
import shutil
import uuid
from typing import Dict, Any, Optional, Tuple
import requests

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
            clone_result = subprocess.run([
                "git", "clone", "--depth", "1", repository_url, self.repo_path
            ], capture_output=True, text=True, timeout=120)
            
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
    
    def deploy_react_app(self, analysis_id: str, aws_credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Deploy a React application to AWS S3 + CloudFront
        """
        logger.info(f"🚀 Starting React deployment for analysis: {analysis_id}")
        
        try:
            if not self.repo_path or not os.path.exists(self.repo_path):
                raise Exception("Repository not found - run analysis first")
            
            # Step 1: Build the React application
            build_result = self._build_react_app()
            if not build_result["success"]:
                return {
                    "status": "error",
                    "stage": "build",
                    "error": build_result["error"]
                }
            
            # Step 2: Create AWS infrastructure
            aws_result = self._deploy_to_aws(aws_credentials)
            if not aws_result["success"]:
                return {
                    "status": "error",
                    "stage": "aws_deployment",
                    "error": aws_result["error"]
                }
            
            deployment_result = {
                "deployment_id": str(uuid.uuid4()),
                "status": "success",
                "website_url": aws_result["website_url"],
                "s3_bucket": aws_result["s3_bucket"],
                "cloudfront_url": aws_result.get("cloudfront_url"),
                "build_output": build_result["build_path"]
            }
            
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
        """Build the React application using npm"""
        logger.info("🔨 Building React application...")
        
        try:
            # Set up enhanced environment for React builds
            env = os.environ.copy()
            env.update({
                'NODE_OPTIONS': '--max-old-space-size=4096',  # 4GB memory
                'GENERATE_SOURCEMAP': 'false',               # Skip source maps
                'CI': 'true',                                # CI mode
                'FORCE_COLOR': '0',                          # No colors
                'NPM_CONFIG_PROGRESS': 'false',              # No progress bars
                'NPM_CONFIG_LOGLEVEL': 'warn'                # Reduce noise
            })
            
            # Step 1: Install dependencies
            logger.info("📦 Installing dependencies...")
            install_result = subprocess.run([
                "npm", "install"
            ], cwd=self.repo_path, capture_output=True, text=True, 
               timeout=600, env=env)  # 10 minute timeout
            
            if install_result.returncode != 0:
                raise Exception(f"npm install failed: {install_result.stderr}")
            
            logger.info("✅ Dependencies installed successfully")
            
            # Step 2: Build the application
            logger.info("🏗️ Building React application...")
            build_result = subprocess.run([
                "npm", "run", "build"
            ], cwd=self.repo_path, capture_output=True, text=True,
               timeout=900, env=env)  # 15 minute timeout
            
            if build_result.returncode != 0:
                raise Exception(f"npm run build failed: {build_result.stderr}")
            
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
            
            logger.info(f"✅ AWS deployment successful!")
            logger.info(f"🌐 Website URL: {website_url}")
            
            return {
                "success": True,
                "s3_bucket": bucket_name,
                "website_url": website_url,
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
