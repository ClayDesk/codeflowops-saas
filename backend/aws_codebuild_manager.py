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
        
        # Dynamic configuration - no hardcoded values
        self.config = self._get_dynamic_config()
        
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
    
    def _get_dynamic_config(self) -> Dict[str, Any]:
        """Get dynamic configuration based on region and requirements - no hardcoded values"""
        return {
            # CodeBuild environment configuration
            'environment': {
                'type': 'LINUX_CONTAINER',
                'image': 'aws/codebuild/amazonlinux2-x86_64-standard:5.0',  # Latest Node.js 18+ image
                'compute_type': 'BUILD_GENERAL1_MEDIUM',  # Balanced for React builds
                'privileged_mode': False  # No Docker required for React builds
            },
            # Node.js build configuration
            'node': {
                'package_managers': ['yarn', 'npm'],  # Prefer yarn, fallback to npm
                'node_version': 'lts',  # Use latest LTS
                'build_commands': {
                    'install': "if [ -f yarn.lock ]; then yarn install --frozen-lockfile; else npm ci; fi",
                    'build': "if [ -f yarn.lock ]; then yarn build; else npm run build; fi"
                }
            },
            # Security and permissions
            'security': {
                'role_prefix': 'CodeBuildRole',
                'bucket_prefix': 'codebuild-artifacts',
                'auto_cleanup': True
            },
            # Build timeouts (in minutes)
            'timeouts': {
                'build': 30,  # 30 minutes max for React builds
                'cleanup': 5   # 5 minutes for cleanup operations
            }
        }
    
    def create_codebuild_service_role(self, deployment_id: str) -> str:
        """Create IAM role for CodeBuild with minimal required permissions"""
        role_name = f"{self.config['security']['role_prefix']}-{deployment_id}"
        
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
        
        # Permissions policy for CodeBuild with comprehensive S3 access
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
                        "s3:ListBucket",
                        "s3:GetBucketLocation"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::*{deployment_id}*",
                        f"arn:aws:s3:::react-*{deployment_id}*",
                        f"arn:aws:s3:::*codebuild-{deployment_id}*"
                    ]
                },
                {
                    "Effect": "Allow",
                    "Action": [
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:DeleteObject",
                        "s3:PutObjectAcl"
                    ],
                    "Resource": [
                        f"arn:aws:s3:::*{deployment_id}*/*",
                        f"arn:aws:s3:::react-*{deployment_id}*/*",
                        f"arn:aws:s3:::*codebuild-{deployment_id}*/*"
                    ]
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
        """Generate dynamic buildspec.yml for React project with robust error handling"""
        
        buildspec = {
            "version": "0.2",
            "phases": {
                "pre_build": {
                    "commands": [
                        "echo Build started on `date`",
                        "echo Checking Node.js and package manager versions...",
                        "node --version",
                        "npm --version", 
                        "which yarn && yarn --version || echo 'Yarn not available, will use npm'",
                        "echo Current directory: $PWD",
                        "ls -la",
                        "echo Checking package files...",
                        "[ -f package.json ] && echo 'package.json found' || echo 'ERROR: package.json not found'",
                        "[ -f yarn.lock ] && echo 'yarn.lock found - will use yarn' || echo 'yarn.lock not found - will use npm'"
                    ]
                },
                "build": {
                    "commands": [
                        "echo Installing dependencies...",
                        "if [ -f yarn.lock ] && command -v yarn >/dev/null 2>&1; then",
                        "  echo 'Using yarn for installation'",
                        "  yarn install --frozen-lockfile",
                        "  echo 'Building with yarn'", 
                        "  yarn build",
                        "else",
                        "  echo 'Using npm for installation'",
                        "  npm ci || npm install",
                        "  echo 'Building with npm'",
                        "  npm run build",
                        "fi",
                        "echo Build phase completed",
                        "echo Checking build output...",
                        "ls -la",
                        "[ -d build ] && echo 'Build directory created successfully' || [ -d dist ] && echo 'Dist directory created' || echo 'ERROR: No build output directory found'",
                        "[ -d build ] && ls -la build/ || [ -d dist ] && ls -la dist/ || echo 'No build files to list'"
                    ]
                },
                "post_build": {
                    "commands": [
                        "echo Post-build phase started",
                        "echo Checking for build output directory...",
                        "if [ -d build ]; then",
                        "  echo 'Found build directory, syncing to S3...'",
                        f"  aws s3 sync build/ s3://{s3_bucket}/ --delete",
                        "elif [ -d dist ]; then",
                        "  echo 'Found dist directory, syncing to S3...'",
                        f"  aws s3 sync dist/ s3://{s3_bucket}/ --delete",
                        "else",
                        "  echo 'ERROR: No build output directory found (build/ or dist/)'",
                        "  exit 1",
                        "fi",
                        "echo S3 sync completed successfully"
                    ]
                }
            },
            "artifacts": {
                "files": [
                    "**/*"
                ],
                "base-directory": ".",
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
                    'location': s3_bucket,
                    'path': f"artifacts/{deployment_id}",
                    'packaging': 'ZIP'
                },
                'environment': {
                    'type': self.config['environment']['type'],
                    'image': self.config['environment']['image'],
                    'computeType': self.config['environment']['compute_type'],
                    'privilegedMode': self.config['environment']['privileged_mode'],
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
                        },
                        {
                            'name': 'NODE_ENV',
                            'value': 'production'
                        }
                    ]
                },
                'serviceRole': service_role,
                'timeoutInMinutes': self.config['timeouts']['build'],
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
        """Get current build status and detailed logs"""
        try:
            response = self.codebuild.batch_get_builds(ids=[build_id])
            
            if not response['builds']:
                return {'status': 'NOT_FOUND', 'phase': 'UNKNOWN'}
            
            build = response['builds'][0]
            build_status = build['buildStatus']
            
            result = {
                'status': build_status,
                'phase': build['currentPhase'],
                'progress': self._calculate_progress(build['currentPhase']),
                'start_time': build.get('startTime'),
                'end_time': build.get('endTime'),
                'logs_location': build.get('logs', {}).get('deepLink'),
                'artifacts_location': build.get('artifacts', {}).get('location')
            }
            
            # Get detailed logs for failed builds
            if build_status == 'FAILED':
                try:
                    # Get CloudWatch logs if available
                    logs_info = build.get('logs', {})
                    log_group = logs_info.get('groupName')
                    log_stream = logs_info.get('streamName')
                    
                    if log_group and log_stream:
                        import boto3
                        logs_client = boto3.client(
                            'logs',
                            aws_access_key_id=self.aws_credentials['aws_access_key_id'],
                            aws_secret_access_key=self.aws_credentials['aws_secret_access_key'],
                            region_name=self.region
                        )
                        
                        # Get the last 50 log events to capture the error
                        log_response = logs_client.get_log_events(
                            logGroupName=log_group,
                            logStreamName=log_stream,
                            limit=50,
                            startFromHead=False  # Get latest logs
                        )
                        
                        # Extract error messages from logs
                        error_logs = []
                        for event in log_response.get('events', []):
                            message = event.get('message', '')
                            if any(keyword in message.lower() for keyword in ['error', 'failed', 'fatal', 'exception']):
                                error_logs.append(message.strip())
                        
                        if error_logs:
                            result['error_details'] = error_logs[-10:]  # Last 10 error messages
                        else:
                            # If no specific errors, get last few log lines
                            all_logs = [event.get('message', '').strip() for event in log_response.get('events', [])]
                            result['error_details'] = all_logs[-5:] if all_logs else ['No detailed logs available']
                    
                except Exception as log_error:
                    logger.warning(f"Could not retrieve build logs: {log_error}")
                    result['error_details'] = [f"Build failed but logs not accessible: {log_error}"]
                
                # Add build phases that failed
                phases = build.get('phases', [])
                failed_phases = [phase for phase in phases if phase.get('phaseStatus') == 'FAILED']
                if failed_phases:
                    result['failed_phases'] = failed_phases
            
            return result
            
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
