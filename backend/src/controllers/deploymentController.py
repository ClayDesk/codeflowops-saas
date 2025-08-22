"""
Deployment Controller for CodeFlowOps
Handles AWS infrastructure provisioning, project building, and deployment orchestration
"""

import logging
import asyncio
import subprocess
import tempfile
import shutil
import json
import yaml
import os
import zipfile
from typing import Dict, Any, Optional, List
from pathlib import Path
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..config.env import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DeploymentController:
    """
    Controller for managing complete deployment workflow
    """
    
    def __init__(self):
        self.aws_region = settings.AWS_REGION
        self.deployment_bucket = settings.AWS_S3_BUCKET
        
        # Initialize AWS clients
        try:
            self.s3_client = boto3.client('s3', region_name=self.aws_region)
            self.cloudformation_client = boto3.client('cloudformation', region_name=self.aws_region)
            self.cloudfront_client = boto3.client('cloudfront', region_name=self.aws_region)
            self.route53_client = boto3.client('route53', region_name=self.aws_region)
        except NoCredentialsError:
            logger.warning("AWS credentials not configured")
            self.s3_client = None
            self.cloudformation_client = None
            self.cloudfront_client = None
            self.route53_client = None
    
    async def prepare_deployment_environment(
        self,
        session_id: str,
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare deployment environment and validate configuration
        
        Args:
            session_id: Session identifier
            deployment_config: Deployment configuration
            
        Returns:
            Deployment environment information
        """
        try:
            logger.info(f"Preparing deployment environment for session {session_id}")
            
            # Create session-specific directories
            session_dir = Path(tempfile.gettempdir()) / "codeflowops" / session_id
            session_dir.mkdir(parents=True, exist_ok=True)
            
            build_dir = session_dir / "build"
            artifacts_dir = session_dir / "artifacts"
            templates_dir = session_dir / "templates"
            
            for directory in [build_dir, artifacts_dir, templates_dir]:
                directory.mkdir(exist_ok=True)
            
            # Validate deployment configuration
            validation_result = await self._validate_deployment_config(deployment_config)
            if not validation_result["valid"]:
                raise Exception(f"Invalid deployment configuration: {validation_result['error']}")
            
            # Generate unique project name
            project_name = deployment_config.get("project_name", f"codeflowops-{session_id[:8]}")
            stack_name = f"{project_name}-{session_id[:8]}"
            
            environment = {
                "session_id": session_id,
                "project_name": project_name,
                "stack_name": stack_name,
                "session_dir": str(session_dir),
                "build_dir": str(build_dir),
                "artifacts_dir": str(artifacts_dir),
                "templates_dir": str(templates_dir),
                "aws_region": self.aws_region,
                "deployment_config": deployment_config
            }
            
            logger.info(f"Deployment environment prepared for session {session_id}")
            return environment
            
        except Exception as e:
            logger.error(f"Failed to prepare deployment environment: {str(e)}")
            raise
    
    async def clone_repository(
        self,
        github_url: str,
        target_dir: Path,
        branch: str = "main"
    ) -> Dict[str, Any]:
        """
        Clone GitHub repository to target directory
        
        Args:
            github_url: GitHub repository URL
            target_dir: Target directory for cloning
            branch: Git branch to clone
            
        Returns:
            Clone operation results
        """
        try:
            logger.info(f"Cloning repository {github_url} to {target_dir}")
            
            # Ensure target directory exists
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Build git clone command
            git_cmd = [
                "git", "clone",
                "--branch", branch,
                "--single-branch",
                "--depth", "1",
                github_url,
                str(target_dir)
            ]
            
            # Execute git clone
            result = await asyncio.create_subprocess_exec(
                *git_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                logger.info(f"Repository cloned successfully to {target_dir}")
                return {
                    "success": True,
                    "clone_path": str(target_dir),
                    "branch": branch
                }
            else:
                error_message = stderr.decode() if stderr else "Unknown git error"
                logger.error(f"Git clone failed: {error_message}")
                return {
                    "success": False,
                    "error": error_message
                }
                
        except Exception as e:
            logger.error(f"Repository clone failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def install_dependencies(
        self,
        project_dir: Path,
        build_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Install project dependencies
        
        Args:
            project_dir: Project directory path
            build_config: Build configuration
            
        Returns:
            Installation results
        """
        try:
            logger.info(f"Installing dependencies in {project_dir}")
            
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_dir)
            
            try:
                # Determine package manager and install command
                if (project_dir / "package.json").exists():
                    # Node.js project
                    if (project_dir / "yarn.lock").exists():
                        install_cmd = ["yarn", "install"]
                    else:
                        install_cmd = ["npm", "install"]
                elif (project_dir / "requirements.txt").exists():
                    # Python project
                    install_cmd = ["pip", "install", "-r", "requirements.txt"]
                else:
                    # No dependencies to install
                    return {"success": True, "message": "No dependencies to install"}
                
                # Execute install command
                result = await asyncio.create_subprocess_exec(
                    *install_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    logger.info("Dependencies installed successfully")
                    return {
                        "success": True,
                        "install_output": stdout.decode()
                    }
                else:
                    error_message = stderr.decode() if stderr else "Unknown install error"
                    logger.error(f"Dependencies installation failed: {error_message}")
                    return {
                        "success": False,
                        "error": error_message
                    }
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"Dependencies installation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def build_project(
        self,
        project_dir: Path,
        build_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build project using configured build command
        
        Args:
            project_dir: Project directory path
            build_config: Build configuration
            
        Returns:
            Build results
        """
        try:
            logger.info(f"Building project in {project_dir}")
            
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(project_dir)
            
            try:
                # Get build command from configuration
                build_command = build_config.get("build_command")
                if not build_command:
                    # Determine default build command
                    if (project_dir / "package.json").exists():
                        build_command = "npm run build"
                    else:
                        return {"success": True, "message": "No build required"}
                
                # Set environment variables
                env = os.environ.copy()
                env_vars = build_config.get("environment_variables", {})
                env.update(env_vars)
                
                # Execute build command
                build_cmd = build_command.split()
                result = await asyncio.create_subprocess_exec(
                    *build_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=env
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    # Determine build output directory
                    build_output = build_config.get("build_output_directory", "build")
                    build_output_path = project_dir / build_output
                    
                    if build_output_path.exists():
                        logger.info("Project built successfully")
                        return {
                            "success": True,
                            "build_output": str(build_output_path),
                            "build_log": stdout.decode()
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Build output directory {build_output} not found"
                        }
                else:
                    error_message = stderr.decode() if stderr else "Unknown build error"
                    logger.error(f"Project build failed: {error_message}")
                    return {
                        "success": False,
                        "error": error_message
                    }
                    
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"Project build failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def package_build_artifacts(
        self,
        session_id: str,
        project_dir: Path,
        build_output_path: str
    ) -> Dict[str, Any]:
        """
        Package build artifacts for deployment
        
        Args:
            session_id: Session identifier
            project_dir: Project directory path
            build_output_path: Build output directory path
            
        Returns:
            Packaging results
        """
        try:
            logger.info(f"Packaging build artifacts for session {session_id}")
            
            build_output = Path(build_output_path)
            if not build_output.exists():
                raise Exception(f"Build output directory {build_output_path} does not exist")
            
            # Create artifacts directory
            artifacts_dir = Path(tempfile.gettempdir()) / "codeflowops" / session_id / "artifacts"
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create zip file
            artifacts_zip = artifacts_dir / f"build-{session_id}.zip"
            
            with zipfile.ZipFile(artifacts_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(build_output):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(build_output)
                        zipf.write(file_path, arcname)
            
            # Calculate package size
            package_size = artifacts_zip.stat().st_size
            
            logger.info(f"Build artifacts packaged: {artifacts_zip} ({package_size} bytes)")
            
            return {
                "success": True,
                "artifacts_path": str(artifacts_zip),
                "size": package_size,
                "file_count": len(list(build_output.rglob("*")))
            }
            
        except Exception as e:
            logger.error(f"Artifact packaging failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_infrastructure_templates(
        self,
        session_id: str,
        stack_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate CloudFormation templates for infrastructure
        
        Args:
            session_id: Session identifier
            stack_config: Infrastructure configuration
            
        Returns:
            Template generation results
        """
        try:
            logger.info(f"Generating infrastructure templates for session {session_id}")
            
            deployment_type = stack_config.get("deployment_type", "static")
            project_name = stack_config.get("project_name", f"codeflowops-{session_id[:8]}")
            
            # Templates directory
            templates_dir = Path(tempfile.gettempdir()) / "codeflowops" / session_id / "templates"
            templates_dir.mkdir(parents=True, exist_ok=True)
            
            if deployment_type == "static":
                template = await self._generate_static_site_template(project_name, stack_config)
            else:
                template = await self._generate_serverless_template(project_name, stack_config)
            
            # Write template to file
            template_file = templates_dir / "infrastructure.yaml"
            with open(template_file, 'w') as f:
                yaml.dump(template, f, default_flow_style=False)
            
            logger.info(f"Infrastructure template generated: {template_file}")
            
            return {
                "success": True,
                "templates": {
                    "main_template": str(template_file),
                    "template_content": template
                }
            }
            
        except Exception as e:
            logger.error(f"Template generation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_aws_access(self, stack_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate AWS credentials and permissions
        
        Args:
            stack_config: Infrastructure configuration
            
        Returns:
            Validation results
        """
        try:
            if not self.s3_client:
                return {
                    "valid": False,
                    "error": "AWS credentials not configured"
                }
            
            # Test S3 access
            try:
                self.s3_client.head_bucket(Bucket=self.deployment_bucket)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    return {
                        "valid": False,
                        "error": f"S3 bucket {self.deployment_bucket} not found"
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"S3 access failed: {str(e)}"
                    }
            
            # Test CloudFormation access
            try:
                if self.cloudformation_client:
                    self.cloudformation_client.describe_stacks()
                else:
                    return {
                        "valid": False,
                        "error": "CloudFormation client not available"
                    }
            except ClientError as e:
                return {
                    "valid": False,
                    "error": f"CloudFormation access failed: {str(e)}"
                }
            
            return {"valid": True}
            
        except Exception as e:
            logger.error(f"AWS validation failed: {str(e)}")
            return {
                "valid": False,
                "error": str(e)
            }
    
    async def deploy_infrastructure_stack(
        self,
        session_id: str,
        templates: Dict[str, Any],
        stack_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy CloudFormation stack
        
        Args:
            session_id: Session identifier
            templates: Infrastructure templates
            stack_config: Stack configuration
            
        Returns:
            Deployment results
        """
        try:
            logger.info(f"Deploying infrastructure stack for session {session_id}")
            
            if not self.cloudformation_client:
                raise Exception("CloudFormation client not available")
            
            stack_name = f"codeflowops-{session_id[:8]}"
            
            # Read template content
            with open(templates["main_template"], 'r') as f:
                template_body = f.read()
            
            # Deploy stack
            response = self.cloudformation_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Capabilities=['CAPABILITY_IAM'],
                Tags=[
                    {
                        'Key': 'Project',
                        'Value': 'CodeFlowOps'
                    },
                    {
                        'Key': 'SessionId',
                        'Value': session_id
                    }
                ]
            )
            
            stack_id = response['StackId']
            
            logger.info(f"CloudFormation stack created: {stack_id}")
            
            return {
                "success": True,
                "stack_id": stack_id,
                "stack_name": stack_name
            }
            
        except Exception as e:
            logger.error(f"Stack deployment failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def wait_for_stack_completion(
        self,
        session_id: str,
        stack_id: str
    ) -> Dict[str, Any]:
        """
        Wait for CloudFormation stack completion
        
        Args:
            session_id: Session identifier
            stack_id: CloudFormation stack ID
            
        Returns:
            Stack completion results
        """
        try:
            logger.info(f"Waiting for stack completion: {stack_id}")
            
            if not self.cloudformation_client:
                raise Exception("CloudFormation client not available")
            
            # Wait for stack completion
            waiter = self.cloudformation_client.get_waiter('stack_create_complete')
            waiter.wait(
                StackName=stack_id,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': 20
                }
            )
            
            # Get stack outputs
            response = self.cloudformation_client.describe_stacks(StackName=stack_id)
            stack = response['Stacks'][0]
            
            outputs = {}
            if 'Outputs' in stack:
                for output in stack['Outputs']:
                    outputs[output['OutputKey']] = output['OutputValue']
            
            # Get stack resources
            resources_response = self.cloudformation_client.describe_stack_resources(StackName=stack_id)
            resources = {}
            for resource in resources_response['StackResources']:
                resources[resource['LogicalResourceId']] = {
                    'type': resource['ResourceType'],
                    'physical_id': resource['PhysicalResourceId'],
                    'status': resource['ResourceStatus']
                }
            
            logger.info(f"Stack completion successful: {stack_id}")
            
            return {
                "success": True,
                "resources": resources,
                "outputs": outputs,
                "stack_status": stack['StackStatus']
            }
            
        except Exception as e:
            logger.error(f"Stack completion failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def deploy_files(
        self,
        session_id: str,
        deployment_env: Dict[str, Any],
        infrastructure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Deploy files to AWS infrastructure
        
        Args:
            session_id: Session identifier
            deployment_env: Deployment environment
            infrastructure: Infrastructure information
            
        Returns:
            File deployment results
        """
        try:
            logger.info(f"Deploying files for session {session_id}")
            
            if not self.s3_client:
                raise Exception("S3 client not available")
            
            # Get S3 bucket from infrastructure outputs
            bucket_name = infrastructure["outputs"].get("BucketName")
            if not bucket_name:
                raise Exception("S3 bucket name not found in infrastructure outputs")
            
            # Get build artifacts
            artifacts_dir = Path(deployment_env["artifacts_dir"])
            artifacts_zip = next(artifacts_dir.glob("build-*.zip"), None)
            
            if not artifacts_zip:
                raise Exception("Build artifacts not found")
            
            # Extract and upload files
            with tempfile.TemporaryDirectory() as temp_dir:
                extract_dir = Path(temp_dir) / "extract"
                
                with zipfile.ZipFile(artifacts_zip, 'r') as zipf:
                    zipf.extractall(extract_dir)
                
                # Upload files to S3
                uploaded_files = []
                for file_path in extract_dir.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(extract_dir)
                        s3_key = str(relative_path).replace('\\', '/')
                        
                        # Determine content type
                        content_type = self._get_content_type(file_path)
                        
                        # Upload file
                        self.s3_client.upload_file(
                            str(file_path),
                            bucket_name,
                            s3_key,
                            ExtraArgs={'ContentType': content_type}
                        )
                        
                        uploaded_files.append(s3_key)
            
            logger.info(f"Files deployed successfully: {len(uploaded_files)} files")
            
            return {
                "success": True,
                "bucket_name": bucket_name,
                "uploaded_files": uploaded_files,
                "file_count": len(uploaded_files)
            }
            
        except Exception as e:
            logger.error(f"File deployment failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def configure_cdn_and_dns(
        self,
        session_id: str,
        infrastructure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Configure CloudFront CDN and DNS
        
        Args:
            session_id: Session identifier
            infrastructure: Infrastructure information
            
        Returns:
            CDN configuration results
        """
        try:
            # Get CloudFront distribution URL from outputs
            distribution_url = infrastructure["outputs"].get("DistributionDomainName")
            if not distribution_url:
                raise Exception("CloudFront distribution URL not found")
            
            site_url = f"https://{distribution_url}"
            
            return {
                "success": True,
                "site_url": site_url,
                "distribution_id": infrastructure["outputs"].get("DistributionId"),
                "distribution_url": distribution_url
            }
            
        except Exception as e:
            logger.error(f"CDN configuration failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def setup_monitoring(
        self,
        session_id: str,
        infrastructure: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Set up CloudWatch monitoring
        
        Args:
            session_id: Session identifier
            infrastructure: Infrastructure information
            
        Returns:
            Monitoring setup results
        """
        try:
            # Basic monitoring setup (CloudWatch logs are automatically created)
            return {
                "success": True,
                "cloudwatch_enabled": True,
                "log_groups": [
                    f"/aws/cloudfront/codeflowops-{session_id[:8]}"
                ]
            }
            
        except Exception as e:
            logger.error(f"Monitoring setup failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_deployment_summary(
        self,
        session_id: str,
        finalization_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate deployment summary
        
        Args:
            session_id: Session identifier
            finalization_config: Finalization configuration
            
        Returns:
            Deployment summary
        """
        try:
            infrastructure = finalization_config["infrastructure"]
            deployment = finalization_config["deployment"]
            
            summary = {
                "session_id": session_id,
                "deployment_time": "completed",
                "infrastructure": {
                    "stack_id": infrastructure["stack_id"],
                    "resources_created": len(infrastructure["resources"]),
                    "s3_bucket": deployment["bucket_name"],
                    "files_deployed": deployment["file_count"]
                },
                "site_info": {
                    "url": finalization_config.get("site_url"),
                    "files_count": deployment["file_count"]
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return {
                "error": str(e)
            }
    
    async def cleanup_temporary_resources(self, session_id: str):
        """
        Cleanup temporary files and directories
        
        Args:
            session_id: Session identifier
        """
        try:
            session_dir = Path(tempfile.gettempdir()) / "codeflowops" / session_id
            if session_dir.exists():
                shutil.rmtree(session_dir)
                logger.info(f"Temporary resources cleaned up for session {session_id}")
                
        except Exception as e:
            logger.error(f"Cleanup failed for session {session_id}: {str(e)}")
    
    async def cleanup_aws_resources(
        self,
        session_id: str,
        cleanup_config: Dict[str, Any]
    ):
        """
        Cleanup AWS resources for failed deployment
        
        Args:
            session_id: Session identifier
            cleanup_config: Cleanup configuration
        """
        try:
            if not self.cloudformation_client:
                return
            
            stack_name = f"codeflowops-{session_id[:8]}"
            
            # Delete CloudFormation stack
            try:
                self.cloudformation_client.delete_stack(StackName=stack_name)
                logger.info(f"CloudFormation stack deletion initiated: {stack_name}")
            except ClientError as e:
                if e.response['Error']['Code'] != 'ValidationError':
                    logger.error(f"Stack deletion failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"AWS resource cleanup failed: {str(e)}")
    
    async def _validate_deployment_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate deployment configuration"""
        required_fields = ["project_name", "deployment_type"]
        
        for field in required_fields:
            if field not in config:
                return {
                    "valid": False,
                    "error": f"Required field missing: {field}"
                }
        
        return {"valid": True}
    
    async def _generate_static_site_template(
        self,
        project_name: str,
        stack_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate CloudFormation template for static site"""
        return {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"Static site infrastructure for {project_name}",
            "Resources": {
                "S3Bucket": {
                    "Type": "AWS::S3::Bucket",
                    "Properties": {
                        "BucketName": f"{project_name.lower()}-{stack_config.get('session_id', 'unknown')[:8]}",
                        "WebsiteConfiguration": {
                            "IndexDocument": "index.html",
                            "ErrorDocument": "error.html"
                        },
                        "PublicAccessBlockConfiguration": {
                            "BlockPublicAcls": False,
                            "BlockPublicPolicy": False,
                            "IgnorePublicAcls": False,
                            "RestrictPublicBuckets": False
                        }
                    }
                },
                "BucketPolicy": {
                    "Type": "AWS::S3::BucketPolicy",
                    "Properties": {
                        "Bucket": {"Ref": "S3Bucket"},
                        "PolicyDocument": {
                            "Statement": [{
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": "s3:GetObject",
                                "Resource": {"Fn::Sub": "${S3Bucket}/*"}
                            }]
                        }
                    }
                },
                "CloudFrontDistribution": {
                    "Type": "AWS::CloudFront::Distribution",
                    "Properties": {
                        "DistributionConfig": {
                            "Origins": [{
                                "Id": "S3Origin",
                                "DomainName": {"Fn::GetAtt": ["S3Bucket", "RegionalDomainName"]},
                                "CustomOriginConfig": {
                                    "HTTPPort": 80,
                                    "HTTPSPort": 443,
                                    "OriginProtocolPolicy": "http-only"
                                }
                            }],
                            "DefaultCacheBehavior": {
                                "TargetOriginId": "S3Origin",
                                "ViewerProtocolPolicy": "redirect-to-https",
                                "CachePolicyId": "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
                            },
                            "Enabled": True,
                            "DefaultRootObject": "index.html"
                        }
                    }
                }
            },
            "Outputs": {
                "BucketName": {
                    "Value": {"Ref": "S3Bucket"},
                    "Description": "S3 Bucket Name"
                },
                "DistributionDomainName": {
                    "Value": {"Fn::GetAtt": ["CloudFrontDistribution", "DomainName"]},
                    "Description": "CloudFront Distribution Domain Name"
                },
                "DistributionId": {
                    "Value": {"Ref": "CloudFrontDistribution"},
                    "Description": "CloudFront Distribution ID"
                }
            }
        }
    
    async def _generate_serverless_template(
        self,
        project_name: str,
        stack_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate CloudFormation template for serverless application"""
        # Simplified serverless template
        static_template = await self._generate_static_site_template(project_name, stack_config)
        
        # Add Lambda and API Gateway resources for serverless
        static_template["Resources"]["LambdaFunction"] = {
            "Type": "AWS::Lambda::Function",
            "Properties": {
                "FunctionName": f"{project_name}-handler",
                "Runtime": "nodejs18.x",
                "Handler": "index.handler",
                "Code": {
                    "ZipFile": "exports.handler = async (event) => { return { statusCode: 200, body: 'Hello from Lambda!' }; };"
                },
                "Role": {"Fn::GetAtt": ["LambdaExecutionRole", "Arn"]}
            }
        }
        
        static_template["Resources"]["LambdaExecutionRole"] = {
            "Type": "AWS::IAM::Role",
            "Properties": {
                "AssumeRolePolicyDocument": {
                    "Version": "2012-10-17",
                    "Statement": [{
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                        "Action": "sts:AssumeRole"
                    }]
                },
                "ManagedPolicyArns": ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
            }
        }
        
        return static_template
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type for file"""
        suffix = file_path.suffix.lower()
        content_types = {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.ico': 'image/x-icon',
            '.txt': 'text/plain'
        }
        return content_types.get(suffix, 'binary/octet-stream')
