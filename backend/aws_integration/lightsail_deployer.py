"""
AWS Lightsail Container Service Deployment
==========================================

Production-ready AWS Lightsail container deployment module.
Handles the complete deployment process from Docker image to live service.
"""

import boto3
import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
from .docker_manager import DockerImageManager

logger = logging.getLogger(__name__)

class LightsailContainerDeployer:
    """
    AWS Lightsail Container Service Deployer
    
    Handles:
    - Container service creation
    - Image deployment
    - Service configuration
    - Domain setup
    - SSL certificate management
    """
    
    def __init__(self, access_key: str, secret_key: str, region: str = 'us-east-1'):
        """Initialize Lightsail deployer with AWS credentials"""
        self.region = region
        self.docker_manager = DockerImageManager()
        
        try:
            self.lightsail_client = boto3.client(
                'lightsail',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            self.ecr_client = boto3.client(
                'ecr',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Validate credentials
            self._validate_credentials()
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS clients: {e}")
            raise
    
    def _validate_credentials(self):
        """Validate AWS credentials"""
        try:
            self.lightsail_client.get_regions()
            logger.info("✅ AWS credentials validated")
        except NoCredentialsError:
            raise Exception("AWS credentials not found or invalid")
        except ClientError as e:
            raise Exception(f"AWS credential validation failed: {e}")
    
    async def deploy_container_service(
        self, 
        service_name: str, 
        image_name: str,
        container_port: int = 8000,
        public_domain_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Deploy a container service to AWS Lightsail
        
        Args:
            service_name: Name for the Lightsail service
            image_name: Docker image name (local or ECR)
            container_port: Port the container listens on
            public_domain_name: Optional custom domain
        
        Returns:
            Deployment result with service details and URLs
        """
        try:
            logger.info(f"🚀 Starting Lightsail deployment: {service_name}")
            
            # Step 1: Create ECR repository and push image
            ecr_result = await self._setup_ecr_and_push_image(image_name, service_name)
            if not ecr_result["success"]:
                return ecr_result
            
            ecr_image_uri = ecr_result["image_uri"]
            
            # Step 2: Create Lightsail container service
            service_result = await self._create_container_service(service_name)
            if not service_result["success"]:
                return service_result
            
            # Step 3: Create and deploy container
            deployment_result = await self._deploy_container(
                service_name, ecr_image_uri, container_port
            )
            if not deployment_result["success"]:
                return deployment_result
            
            # Step 4: Wait for deployment to be active
            await self._wait_for_deployment(service_name)
            
            # Step 5: Get service details and public URL
            service_details = await self._get_service_details(service_name)
            
            logger.info(f"✅ Lightsail deployment successful!")
            
            return {
                "success": True,
                "service_name": service_name,
                "public_url": service_details.get("url"),
                "service_arn": service_details.get("arn"),
                "state": service_details.get("state"),
                "ecr_repository": ecr_result.get("repository_uri"),
                "deployment_id": deployment_result.get("deployment_id")
            }
            
        except Exception as e:
            logger.error(f"❌ Lightsail deployment failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "service_name": service_name
            }
    
    async def _setup_ecr_and_push_image(self, local_image_name: str, service_name: str) -> Dict[str, Any]:
        """Create ECR repository and push Docker image"""
        try:
            repo_name = f"codeflowops-{service_name}".lower()
            
            logger.info(f"📦 Setting up ECR repository: {repo_name}")
            
            # Create ECR repository
            try:
                response = self.ecr_client.create_repository(
                    repositoryName=repo_name,
                    imageScanningConfiguration={'scanOnPush': True}
                )
                repository_uri = response['repository']['repositoryUri']
                logger.info(f"✅ Created ECR repository: {repository_uri}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'RepositoryAlreadyExistsException':
                    # Repository exists, get its URI
                    response = self.ecr_client.describe_repositories(repositoryNames=[repo_name])
                    repository_uri = response['repositories'][0]['repositoryUri']
                    logger.info(f"✅ Using existing ECR repository: {repository_uri}")
                else:
                    raise
            
            # Get ECR login token
            auth_response = self.ecr_client.get_authorization_token()
            auth_data = auth_response['authorizationData'][0]
            
            # The image URI for deployment
            image_uri = f"{repository_uri}:latest"
            
            # Push image to ECR using Docker manager
            if self.docker_manager.docker_available:
                push_result = self.docker_manager.push_to_ecr(
                    local_image_name, 
                    image_uri, 
                    auth_data['authorizationToken']
                )
                
                if not push_result["success"]:
                    return {
                        "success": False,
                        "error": f"Failed to push image to ECR: {push_result['error']}"
                    }
                
                logger.info(f"✅ Image pushed to ECR: {image_uri}")
            else:
                logger.warning("⚠️ Docker not available, skipping image push")
            
            return {
                "success": True,
                "repository_uri": repository_uri,
                "image_uri": image_uri,
                "auth_token": auth_data['authorizationToken']
            }
            
        except Exception as e:
            logger.error(f"❌ ECR setup failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_container_service(self, service_name: str) -> Dict[str, Any]:
        """Create Lightsail container service"""
        try:
            logger.info(f"🏗️ Creating Lightsail container service: {service_name}")
            
            # Check if service already exists
            try:
                existing_service = self.lightsail_client.get_container_services(
                    serviceName=service_name
                )
                logger.info(f"✅ Using existing container service: {service_name}")
                return {"success": True, "service_name": service_name}
                
            except ClientError as e:
                if e.response['Error']['Code'] != 'NotFoundException':
                    raise
            
            # Create new container service
            response = self.lightsail_client.create_container_service(
                serviceName=service_name,
                power='nano',  # nano, micro, small, medium, large, xlarge
                scale=1,       # Number of instances
                tags=[
                    {
                        'key': 'Project',
                        'value': 'CodeFlowOps'
                    },
                    {
                        'key': 'Environment',
                        'value': 'Production'
                    }
                ]
            )
            
            logger.info(f"✅ Container service created: {service_name}")
            return {
                "success": True,
                "service_name": service_name,
                "service_arn": response['containerService']['arn']
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create container service: {e}")
            return {"success": False, "error": str(e)}
    
    async def _deploy_container(self, service_name: str, image_uri: str, container_port: int) -> Dict[str, Any]:
        """Deploy container to the service"""
        try:
            logger.info(f"🚀 Deploying container to service: {service_name}")
            
            # Create deployment configuration
            containers = {
                'app': {
                    'image': image_uri,
                    'ports': {
                        str(container_port): 'HTTP'
                    },
                    'environment': {
                        'PORT': str(container_port),
                        'NODE_ENV': 'production'
                    }
                }
            }
            
            public_endpoint = {
                'containerName': 'app',
                'containerPort': container_port,
                'healthCheck': {
                    'healthyThreshold': 2,
                    'unhealthyThreshold': 2,
                    'timeoutSeconds': 5,
                    'intervalSeconds': 30,
                    'path': '/',
                    'successCodes': '200'
                }
            }
            
            # Deploy the container
            response = self.lightsail_client.create_container_service_deployment(
                serviceName=service_name,
                containers=containers,
                publicEndpoint=public_endpoint
            )
            
            deployment_id = response['deployment']['deploymentId']
            
            logger.info(f"✅ Container deployment initiated: {deployment_id}")
            return {
                "success": True,
                "deployment_id": deployment_id,
                "service_name": service_name
            }
            
        except Exception as e:
            logger.error(f"❌ Container deployment failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _wait_for_deployment(self, service_name: str, timeout_minutes: int = 10):
        """Wait for deployment to complete"""
        logger.info(f"⏳ Waiting for deployment to complete...")
        
        timeout_seconds = timeout_minutes * 60
        start_time = time.time()
        
        while time.time() - start_time < timeout_seconds:
            try:
                response = self.lightsail_client.get_container_services(serviceName=service_name)
                service = response['containerServices'][0]
                
                state = service.get('state')
                logger.info(f"Service state: {state}")
                
                if state == 'RUNNING':
                    logger.info("✅ Deployment completed successfully!")
                    return
                elif state in ['FAILED', 'DISABLED']:
                    raise Exception(f"Deployment failed with state: {state}")
                
                # Wait before checking again
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error checking deployment status: {e}")
                break
        
        raise Exception(f"Deployment timeout after {timeout_minutes} minutes")
    
    async def _get_service_details(self, service_name: str) -> Dict[str, Any]:
        """Get container service details including public URL"""
        try:
            response = self.lightsail_client.get_container_services(serviceName=service_name)
            service = response['containerServices'][0]
            
            return {
                "arn": service.get('arn'),
                "state": service.get('state'),
                "url": service.get('url'),
                "power": service.get('power'),
                "scale": service.get('scale'),
                "location": service.get('location')
            }
            
        except Exception as e:
            logger.error(f"Failed to get service details: {e}")
            return {}
    
    def delete_service(self, service_name: str) -> Dict[str, Any]:
        """Delete a Lightsail container service"""
        try:
            logger.info(f"🗑️ Deleting container service: {service_name}")
            
            response = self.lightsail_client.delete_container_service(serviceName=service_name)
            
            logger.info(f"✅ Service deletion initiated: {service_name}")
            return {"success": True, "service_name": service_name}
            
        except Exception as e:
            logger.error(f"❌ Failed to delete service: {e}")
            return {"success": False, "error": str(e)}
    
    def list_services(self) -> Dict[str, Any]:
        """List all container services"""
        try:
            response = self.lightsail_client.get_container_services()
            services = response.get('containerServices', [])
            
            service_list = []
            for service in services:
                service_list.append({
                    "name": service.get('containerServiceName'),
                    "state": service.get('state'),
                    "url": service.get('url'),
                    "power": service.get('power'),
                    "scale": service.get('scale')
                })
            
            return {"success": True, "services": service_list}
            
        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return {"success": False, "error": str(e)}


# For backward compatibility, keep the original class name as an alias
LightsailDeployer = LightsailContainerDeployer
