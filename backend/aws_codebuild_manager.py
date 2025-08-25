"""
AWS CodeBuild Manager for React Deployments
==========================================

Handles dynamic CodeBuild project creation and management for React app builds.
Designed for thousands of concurrent users with no hardcoded values.
"""

import boto3
import json
import time
import uuid
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class CodeBuildManager:
    """Manages AWS CodeBuild projects for React deployments"""
    
    def __init__(self, aws_credentials: Dict[str, str]):
        """Initialize CodeBuild manager with user's AWS credentials"""
        self.aws_credentials = aws_credentials
        self.region = aws_credentials.get('aws_region', 'us-east-1')
        
        # Initialize AWS clients with user credentials
        try:
            self.codebuild = boto3.client(
                'codebuild',
                aws_access_key_id=aws_credentials['aws_access_key_id'],
                aws_secret_access_key=aws_credentials['aws_secret_access_key'],
                region_name=self.region
            )
            
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=aws_credentials['aws_access_key_id'],
                aws_secret_access_key=aws_credentials['aws_secret_access_key'],
                region_name=self.region
            )
            
            self.iam = boto3.client(
                'iam',
                aws_access_key_id=aws_credentials['aws_access_key_id'],
                aws_secret_access_key=aws_credentials['aws_secret_access_key'],
                region_name=self.region
            )
            
        except (NoCredentialsError, KeyError) as e:
            raise Exception(f"Invalid AWS credentials: {e}")
    
    def create_codebuild_service_role(self, deployment_id: str) -> str:
        """Create IAM role for CodeBuild with minimal required permissions"""
        role_name = f"CodeBuildRole-{deployment_id}"
        
        # Trust policy for CodeBuild
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "codebuild.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        # Permissions policy for CodeBuild
        permissions_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"arn:aws:logs:{self.region}:*:*"
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject"
                    ],
                    "Resource": f"arn:aws:s3:::*codebuild-{deployment_id}*/*"
                }
            ]
        }
        
        try:
            # Create the role
            self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"CodeBuild service role for deployment {deployment_id}"
            )
            
            # Attach the permissions policy
            self.iam.put_role_policy(
                RoleName=role_name,
                PolicyName=f"CodeBuildPolicy-{deployment_id}",
                PolicyDocument=json.dumps(permissions_policy)
            )
            
            # Return the role ARN
            role_arn = f"arn:aws:iam::{self.get_account_id()}:role/{role_name}"
            logger.info(f"✅ Created CodeBuild role: {role_arn}")
            return role_arn
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'EntityAlreadyExists':
                # Role already exists, return its ARN
                role_arn = f"arn:aws:iam::{self.get_account_id()}:role/{role_name}"
                logger.info(f"✅ Using existing CodeBuild role: {role_arn}")
                return role_arn
            else:
                raise Exception(f"Failed to create CodeBuild role: {e}")
    
    def get_account_id(self) -> str:
        """Get AWS account ID"""
        try:
            sts = boto3.client(
                'sts',
                aws_access_key_id=self.aws_credentials['aws_access_key_id'],
                aws_secret_access_key=self.aws_credentials['aws_secret_access_key'],
                region_name=self.region
            )
            return sts.get_caller_identity()['Account']
        except Exception as e:
            raise Exception(f"Failed to get AWS account ID: {e}")
    
    def create_buildspec(self, project_name: str, s3_bucket: str) -> str:
        """Generate dynamic buildspec.yml for React project"""
        buildspec = {
            "version": "0.2",
            "phases": {
                "pre_build": {
                    "commands": [
                        "echo Logging in to Amazon ECR...",
                        "echo Build started on `date`",
                        "echo Checking Node.js and yarn versions...",
                        "node --version",
                        "npm --version", 
                        "yarn --version"
                    ]
                },
                "build": {
                    "commands": [
                        "echo Build started on `date`",
                        "echo Installing dependencies...",
                        "if [ -f yarn.lock ]; then yarn install --frozen-lockfile; else npm ci; fi",
                        "echo Building React application...",
                        "if [ -f yarn.lock ]; then yarn build; else npm run build; fi",
                        "echo Build completed on `date`"
                    ]
                },
                "post_build": {
                    "commands": [
                        "echo Build completed on `date`",
                        "echo Uploading to S3...",
                        f"aws s3 sync build/ s3://{s3_bucket}/build/ --delete",
                        "echo Upload completed"
                    ]
                }
            },
            "artifacts": {
                "files": [
                    "**/*"
                ],
                "base-directory": "build",
                "name": f"{project_name}-build"
            }
        }
        
        return json.dumps(buildspec, indent=2)
    
    def create_codebuild_project(self, deployment_id: str, repository_url: str, 
                               project_name: str, s3_bucket: str) -> str:
        """Create a CodeBuild project for React deployment"""
        project_name_clean = f"react-build-{deployment_id}"
        
        try:
            # Create service role
            service_role = self.create_codebuild_service_role(deployment_id)
            
            # Wait for role to be available
            time.sleep(10)
            
            # Generate buildspec
            buildspec_content = self.create_buildspec(project_name, s3_bucket)
            
            # Create CodeBuild project
            project_config = {
                'name': project_name_clean,
                'description': f'React build for {project_name} - Deployment {deployment_id}',
                'source': {
                    'type': 'GITHUB',
                    'location': repository_url,
                    'buildspec': buildspec_content
                },
                'artifacts': {
                    'type': 'S3',
                    'location': f"{s3_bucket}/artifacts/{deployment_id}"
                },
                'environment': {
                    'type': 'LINUX_CONTAINER',
                    'image': 'aws/codebuild/amazonlinux2-x86_64-standard:5.0',  # Node.js 18+
                    'computeType': 'BUILD_GENERAL1_MEDIUM',
                    'environmentVariables': [
                        {
                            'name': 'AWS_DEFAULT_REGION',
                            'value': self.region
                        },
                        {
                            'name': 'PROJECT_NAME',
                            'value': project_name
                        },
                        {
                            'name': 'DEPLOYMENT_ID',
                            'value': deployment_id
                        }
                    ]
                },
                'serviceRole': service_role,
                'timeoutInMinutes': 60,
                'badgeEnabled': False,
                'logsConfig': {
                    'cloudWatchLogs': {
                        'status': 'ENABLED',
                        'groupName': f'/aws/codebuild/react-builds',
                        'streamName': f'{deployment_id}'
                    }
                }
            }
            
            response = self.codebuild.create_project(**project_config)
            logger.info(f"✅ Created CodeBuild project: {project_name_clean}")
            return project_name_clean
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceAlreadyExistsException':
                logger.info(f"✅ CodeBuild project already exists: {project_name_clean}")
                return project_name_clean
            else:
                raise Exception(f"Failed to create CodeBuild project: {e}")
    
    def start_build(self, project_name: str, deployment_id: str) -> str:
        """Start a CodeBuild build and return build ID"""
        try:
            response = self.codebuild.start_build(
                projectName=project_name,
                sourceVersion='HEAD'  # Build from main/master branch
            )
            
            build_id = response['build']['id']
            logger.info(f"✅ Started CodeBuild: {build_id}")
            return build_id
            
        except ClientError as e:
            raise Exception(f"Failed to start CodeBuild: {e}")
    
    def get_build_status(self, build_id: str) -> Dict[str, Any]:
        """Get current build status and logs"""
        try:
            response = self.codebuild.batch_get_builds(ids=[build_id])
            
            if not response['builds']:
                return {'status': 'NOT_FOUND', 'phase': 'UNKNOWN'}
            
            build = response['builds'][0]
            
            return {
                'status': build['buildStatus'],
                'phase': build['currentPhase'],
                'progress': self._calculate_progress(build['currentPhase']),
                'start_time': build.get('startTime'),
                'end_time': build.get('endTime'),
                'logs_location': build.get('logs', {}).get('deepLink'),
                'artifacts_location': build.get('artifacts', {}).get('location')
            }
            
        except ClientError as e:
            return {'status': 'ERROR', 'error': str(e)}
    
    def _calculate_progress(self, phase: str) -> int:
        """Calculate build progress percentage based on current phase"""
        phase_progress = {
            'SUBMITTED': 10,
            'QUEUED': 20, 
            'PROVISIONING': 30,
            'DOWNLOAD_SOURCE': 40,
            'INSTALL': 50,
            'PRE_BUILD': 60,
            'BUILD': 80,
            'POST_BUILD': 90,
            'UPLOAD_ARTIFACTS': 95,
            'FINALIZING': 100,
            'COMPLETED': 100
        }
        
        return phase_progress.get(phase, 0)
    
    def cleanup_build_resources(self, deployment_id: str, project_name: str):
        """Clean up CodeBuild project and IAM role after deployment"""
        try:
            # Delete CodeBuild project
            self.codebuild.delete_project(name=project_name)
            logger.info(f"🗑️ Deleted CodeBuild project: {project_name}")
            
            # Delete IAM role and policy
            role_name = f"CodeBuildRole-{deployment_id}"
            
            # Delete policy first
            try:
                self.iam.delete_role_policy(
                    RoleName=role_name,
                    PolicyName=f"CodeBuildPolicy-{deployment_id}"
                )
            except ClientError:
                pass  # Policy might not exist
            
            # Delete role
            try:
                self.iam.delete_role(RoleName=role_name)
                logger.info(f"🗑️ Deleted IAM role: {role_name}")
            except ClientError:
                pass  # Role might not exist
                
        except ClientError as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")
            # Don't fail the deployment if cleanup fails
    
    def wait_for_build_completion(self, build_id: str, timeout_minutes: int = 30) -> Dict[str, Any]:
        """Wait for build to complete with timeout"""
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while True:
            status_info = self.get_build_status(build_id)
            
            if status_info['status'] in ['SUCCEEDED', 'FAILED', 'FAULT', 'STOPPED', 'TIMED_OUT']:
                return status_info
            
            if time.time() - start_time > timeout_seconds:
                return {
                    'status': 'TIMED_OUT',
                    'error': f'Build timed out after {timeout_minutes} minutes'
                }
            
            time.sleep(30)  # Check every 30 seconds
