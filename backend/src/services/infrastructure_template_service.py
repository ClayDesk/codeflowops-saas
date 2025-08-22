# Infrastructure Template System - Multi-cloud template generation for Smart Deployments
import json
import yaml
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass
from pathlib import Path

class CloudProvider(Enum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    DIGITALOCEAN = "digitalocean"

class ProjectType(Enum):
    STATIC_SITE = "static_site"
    SPA = "spa"
    FULLSTACK_APP = "fullstack_app"
    API_SERVICE = "api_service"
    MICROSERVICES = "microservices"
    CONTAINER_APP = "container_app"

@dataclass
class InfrastructureRequirement:
    """
    Represents infrastructure requirements for a project
    """
    storage: bool = False
    cdn: bool = False
    compute: bool = False
    database: bool = False
    load_balancer: bool = False
    container_registry: bool = False
    monitoring: bool = True
    ssl_certificate: bool = True
    custom_domain: bool = False
    auto_scaling: bool = False
    backup: bool = False

# Alias for backward compatibility
InfrastructureRequirements = InfrastructureRequirement

class InfrastructureTemplateEngine:
    """
    Multi-cloud infrastructure template generation engine
    """
    
    def __init__(self):
        self.templates = {
            CloudProvider.AWS: AWSTemplateGenerator(),
            CloudProvider.AZURE: AzureTemplateGenerator(),
            CloudProvider.GCP: GCPTemplateGenerator(),
            CloudProvider.DIGITALOCEAN: DigitalOceanTemplateGenerator()
        }
    
    async def generate_template(
        self,
        cloud_provider: CloudProvider,
        project_type: ProjectType,
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate infrastructure template for specified cloud provider
        """
        generator = self.templates.get(cloud_provider)
        if not generator:
            raise ValueError(f"Unsupported cloud provider: {cloud_provider}")
        
        return await generator.generate_template(project_type, requirements, project_config)
    
    def get_supported_providers(self) -> List[CloudProvider]:
        """
        Get list of supported cloud providers
        """
        return list(self.templates.keys())
    
    def get_template_preview(
        self,
        cloud_provider: CloudProvider,
        project_type: ProjectType
    ) -> Dict[str, Any]:
        """
        Get preview of template structure without full generation
        """
        generator = self.templates.get(cloud_provider)
        if not generator:
            return {}
        
        return generator.get_template_preview(project_type)

class BaseTemplateGenerator:
    """
    Base class for cloud provider template generators
    """
    
    def __init__(self, provider: CloudProvider):
        self.provider = provider
    
    async def generate_template(
        self,
        project_type: ProjectType,
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate infrastructure template - to be implemented by subclasses
        """
        raise NotImplementedError
    
    def get_template_preview(self, project_type: ProjectType) -> Dict[str, Any]:
        """
        Get template preview - to be implemented by subclasses
        """
        raise NotImplementedError
    
    def _generate_metadata(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate common metadata for templates
        """
        return {
            "generated_by": "CodeFlowOps Smart Deploy",
            "provider": self.provider.value,
            "timestamp": project_config.get("timestamp"),
            "project_name": project_config.get("project_name") or "webapp",
            "environment": project_config.get("environment", "production")
        }

class AWSTemplateGenerator(BaseTemplateGenerator):
    """
    AWS CloudFormation template generator
    """
    
    def __init__(self):
        super().__init__(CloudProvider.AWS)
    
    async def generate_template(
        self,
        project_type: ProjectType,
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate AWS CloudFormation template
        """
        project_name = project_config.get("project_name") or "webapp"
        
        template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": f"CodeFlowOps Smart Deploy - {project_name}",
            "Parameters": self._generate_aws_parameters(project_config),
            "Resources": {},
            "Outputs": {}
        }
        
        # Generate resources based on project type and requirements
        if project_type in [ProjectType.STATIC_SITE, ProjectType.SPA]:
            self._add_static_site_resources(template, requirements, project_config)
        elif project_type == ProjectType.FULLSTACK_APP:
            self._add_fullstack_resources(template, requirements, project_config)
        elif project_type == ProjectType.API_SERVICE:
            self._add_api_service_resources(template, requirements, project_config)
        elif project_type == ProjectType.CONTAINER_APP:
            self._add_container_resources(template, requirements, project_config)
        
        # Add common resources
        if requirements.monitoring:
            self._add_monitoring_resources(template, project_config)
        
        return {
            "template": template,
            "format": "cloudformation",
            "provider": "aws",
            "deployment_method": "cloudformation_stack"
        }
    
    def get_template_preview(self, project_type: ProjectType) -> Dict[str, Any]:
        """
        Get AWS template preview
        """
        preview = {
            "provider": "aws",
            "format": "cloudformation",
            "estimated_resources": []
        }
        
        if project_type in [ProjectType.STATIC_SITE, ProjectType.SPA]:
            preview["estimated_resources"] = [
                "S3 Bucket (Static Website Hosting)",
                "CloudFront Distribution (CDN)",
                "Route53 Record (DNS)",
                "Certificate Manager (SSL)"
            ]
        elif project_type == ProjectType.FULLSTACK_APP:
            preview["estimated_resources"] = [
                "Application Load Balancer",
                "ECS Cluster & Service",
                "RDS Database",
                "S3 Buckets (Assets & Backups)",
                "CloudFront Distribution"
            ]
        
        return preview
    
    def _generate_aws_parameters(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate CloudFormation parameters
        """
        return {
            "ProjectName": {
                "Type": "String",
                "Default": project_config.get("project_name") or "webapp",
                "Description": "Name of the project"
            },
            "Environment": {
                "Type": "String",
                "Default": project_config.get("environment", "production"),
                "AllowedValues": ["development", "staging", "production"],
                "Description": "Environment name"
            },
            "DomainName": {
                "Type": "String",
                "Default": project_config.get("domain_name", ""),
                "Description": "Custom domain name (optional)"
            }
        }
    
    def _add_static_site_resources(
        self,
        template: Dict[str, Any],
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> None:
        """
        Add AWS resources for static site hosting
        """
        # S3 Bucket for static hosting
        template["Resources"]["WebsiteBucket"] = {
            "Type": "AWS::S3::Bucket",
            "Properties": {
                "BucketName": {"Fn::Sub": "${ProjectName}-${Environment}-website"},
                "PublicAccessBlockConfiguration": {
                    "BlockPublicAcls": True,
                    "BlockPublicPolicy": True,
                    "IgnorePublicAcls": True,
                    "RestrictPublicBuckets": True
                },
                "WebsiteConfiguration": {
                    "IndexDocument": "index.html",
                    "ErrorDocument": "index.html"
                }
            }
        }
        
        # Origin Access Control for CloudFront
        template["Resources"]["OriginAccessControl"] = {
            "Type": "AWS::CloudFront::OriginAccessControl",
            "Properties": {
                "OriginAccessControlConfig": {
                    "Name": {"Fn::Sub": "${ProjectName}-${Environment}-oac"},
                    "OriginAccessControlOriginType": "s3",
                    "SigningBehavior": "always",
                    "SigningProtocol": "sigv4"
                }
            }
        }
        
        # CloudFront Distribution
        if requirements.cdn:
            template["Resources"]["CloudFrontDistribution"] = {
                "Type": "AWS::CloudFront::Distribution",
                "Properties": {
                    "DistributionConfig": {
                        "Enabled": True,
                        "DefaultRootObject": "index.html",
                        "PriceClass": "PriceClass_100",
                        "Origins": [{
                            "DomainName": {"Fn::GetAtt": ["WebsiteBucket", "RegionalDomainName"]},
                            "Id": "S3Origin",
                            "S3OriginConfig": {
                                "OriginAccessIdentity": ""
                            },
                            "OriginAccessControlId": {"Ref": "OriginAccessControl"}
                        }],
                        "DefaultCacheBehavior": {
                            "TargetOriginId": "S3Origin",
                            "ViewerProtocolPolicy": "redirect-to-https",
                            "AllowedMethods": ["GET", "HEAD", "OPTIONS"],
                            "CachedMethods": ["GET", "HEAD"],
                            "Compress": True,
                            "ForwardedValues": {
                                "QueryString": False,
                                "Cookies": {"Forward": "none"}
                            }
                        },
                        "CustomErrorResponses": [{
                            "ErrorCode": 404,
                            "ResponseCode": 200,
                            "ResponsePagePath": "/index.html"
                        }]
                    }
                }
            }
        
        # S3 Bucket Policy
        template["Resources"]["WebsiteBucketPolicy"] = {
            "Type": "AWS::S3::BucketPolicy",
            "Properties": {
                "Bucket": {"Ref": "WebsiteBucket"},
                "PolicyDocument": {
                    "Statement": [{
                        "Action": "s3:GetObject",
                        "Effect": "Allow",
                        "Resource": {"Fn::Sub": "${WebsiteBucket.Arn}/*"},
                        "Principal": {
                            "Service": "cloudfront.amazonaws.com"
                        },
                        "Condition": {
                            "StringEquals": {
                                "AWS:SourceArn": {"Fn::Sub": "arn:aws:cloudfront::${AWS::AccountId}:distribution/${CloudFrontDistribution}"}
                            }
                        }
                    }]
                }
            }
        }
        
        # Outputs
        template["Outputs"]["WebsiteURL"] = {
            "Description": "Website URL",
            "Value": {"Fn::GetAtt": ["CloudFrontDistribution", "DomainName"]},
            "Export": {"Name": {"Fn::Sub": "${AWS::StackName}-WebsiteURL"}}
        }
        
        template["Outputs"]["S3BucketName"] = {
            "Description": "S3 Bucket for website content",
            "Value": {"Ref": "WebsiteBucket"},
            "Export": {"Name": {"Fn::Sub": "${AWS::StackName}-S3Bucket"}}
        }
    
    def _add_fullstack_resources(
        self,
        template: Dict[str, Any],
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> None:
        """
        Add AWS resources for full-stack applications
        """
        # VPC and Networking
        template["Resources"]["VPC"] = {
            "Type": "AWS::EC2::VPC",
            "Properties": {
                "CidrBlock": "10.0.0.0/16",
                "EnableDnsHostnames": True,
                "EnableDnsSupport": True,
                "Tags": [{"Key": "Name", "Value": {"Fn::Sub": "${ProjectName}-${Environment}-vpc"}}]
            }
        }
        
        # Public Subnets
        template["Resources"]["PublicSubnet1"] = {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": {"Ref": "VPC"},
                "CidrBlock": "10.0.1.0/24",
                "AvailabilityZone": {"Fn::Select": [0, {"Fn::GetAZs": ""}]},
                "MapPublicIpOnLaunch": True
            }
        }
        
        template["Resources"]["PublicSubnet2"] = {
            "Type": "AWS::EC2::Subnet",
            "Properties": {
                "VpcId": {"Ref": "VPC"},
                "CidrBlock": "10.0.2.0/24",
                "AvailabilityZone": {"Fn::Select": [1, {"Fn::GetAZs": ""}]},
                "MapPublicIpOnLaunch": True
            }
        }
        
        # ECS Cluster for container hosting
        if requirements.compute:
            template["Resources"]["ECSCluster"] = {
                "Type": "AWS::ECS::Cluster",
                "Properties": {
                    "ClusterName": {"Fn::Sub": "${ProjectName}-${Environment}-cluster"}
                }
            }
        
        # RDS Database
        if requirements.database:
            template["Resources"]["DatabaseSubnetGroup"] = {
                "Type": "AWS::RDS::DBSubnetGroup",
                "Properties": {
                    "DBSubnetGroupDescription": "Subnet group for RDS database",
                    "SubnetIds": [{"Ref": "PublicSubnet1"}, {"Ref": "PublicSubnet2"}]
                }
            }
            
            template["Resources"]["Database"] = {
                "Type": "AWS::RDS::DBInstance",
                "Properties": {
                    "DBInstanceIdentifier": {"Fn::Sub": "${ProjectName}-${Environment}-db"},
                    "DBInstanceClass": "db.t3.micro",
                    "Engine": "postgres",
                    "MasterUsername": "dbadmin",
                    "MasterUserPassword": "{{resolve:secretsmanager:db-password:SecretString:password}}",
                    "AllocatedStorage": "20",
                    "DBSubnetGroupName": {"Ref": "DatabaseSubnetGroup"},
                    "VPCSecurityGroups": [{"Ref": "DatabaseSecurityGroup"}]
                }
            }
    
    def _add_api_service_resources(
        self,
        template: Dict[str, Any],
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> None:
        """
        Add AWS resources for API service
        """
        # Lambda function for serverless API
        template["Resources"]["APIFunction"] = {
            "Type": "AWS::Lambda::Function",
            "Properties": {
                "FunctionName": {"Fn::Sub": "${ProjectName}-${Environment}-api"},
                "Runtime": project_config.get("runtime", "nodejs18.x"),
                "Handler": "index.handler",
                "Code": {
                    "ZipFile": "exports.handler = async (event) => { return { statusCode: 200, body: 'Hello World' }; };"
                },
                "Environment": {
                    "Variables": {
                        "ENVIRONMENT": {"Ref": "Environment"}
                    }
                }
            }
        }
        
        # API Gateway
        template["Resources"]["APIGateway"] = {
            "Type": "AWS::ApiGateway::RestApi",
            "Properties": {
                "Name": {"Fn::Sub": "${ProjectName}-${Environment}-api"},
                "Description": "API Gateway for the application"
            }
        }
    
    def _add_container_resources(
        self,
        template: Dict[str, Any],
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> None:
        """
        Add AWS resources for containerized applications
        """
        # ECR Repository
        template["Resources"]["ECRRepository"] = {
            "Type": "AWS::ECR::Repository",
            "Properties": {
                "RepositoryName": {"Fn::Sub": "${ProjectName}-${Environment}"},
                "ImageScanningConfiguration": {
                    "ScanOnPush": True
                }
            }
        }
        
        # ECS Task Definition
        template["Resources"]["TaskDefinition"] = {
            "Type": "AWS::ECS::TaskDefinition",
            "Properties": {
                "Family": {"Fn::Sub": "${ProjectName}-${Environment}"},
                "NetworkMode": "awsvpc",
                "RequiresCompatibilities": ["FARGATE"],
                "Cpu": "256",
                "Memory": "512",
                "ContainerDefinitions": [{
                    "Name": {"Fn::Sub": "${ProjectName}-container"},
                    "Image": {"Fn::Sub": "${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${ECRRepository}:latest"},
                    "PortMappings": [{
                        "ContainerPort": 3000,
                        "Protocol": "tcp"
                    }],
                    "LogConfiguration": {
                        "LogDriver": "awslogs",
                        "Options": {
                            "awslogs-group": {"Ref": "LogGroup"},
                            "awslogs-region": {"Ref": "AWS::Region"},
                            "awslogs-stream-prefix": "ecs"
                        }
                    }
                }]
            }
        }
    
    def _add_monitoring_resources(
        self,
        template: Dict[str, Any],
        project_config: Dict[str, Any]
    ) -> None:
        """
        Add monitoring and logging resources
        """
        # CloudWatch Log Group
        template["Resources"]["LogGroup"] = {
            "Type": "AWS::Logs::LogGroup",
            "Properties": {
                "LogGroupName": {"Fn::Sub": "/aws/ecs/${ProjectName}-${Environment}"},
                "RetentionInDays": 7
            }
        }

class AzureTemplateGenerator(BaseTemplateGenerator):
    """
    Azure Resource Manager template generator
    """
    
    def __init__(self):
        super().__init__(CloudProvider.AZURE)
    
    async def generate_template(
        self,
        project_type: ProjectType,
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate Azure ARM template
        """
        template = {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "parameters": self._generate_azure_parameters(project_config),
            "variables": {},
            "resources": [],
            "outputs": {}
        }
        
        # Add resources based on project type
        if project_type in [ProjectType.STATIC_SITE, ProjectType.SPA]:
            self._add_azure_static_resources(template, requirements, project_config)
        
        return {
            "template": template,
            "format": "arm",
            "provider": "azure",
            "deployment_method": "arm_deployment"
        }
    
    def get_template_preview(self, project_type: ProjectType) -> Dict[str, Any]:
        """
        Get Azure template preview
        """
        return {
            "provider": "azure",
            "format": "arm",
            "estimated_resources": ["Storage Account", "CDN Profile", "CDN Endpoint"]
        }
    
    def _generate_azure_parameters(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate ARM template parameters
        """
        return {
            "projectName": {
                "type": "string",
                "defaultValue": project_config.get("project_name") or "webapp",
                "metadata": {"description": "Name of the project"}
            },
            "environment": {
                "type": "string",
                "defaultValue": project_config.get("environment", "production"),
                "allowedValues": ["development", "staging", "production"],
                "metadata": {"description": "Environment name"}
            }
        }
    
    def _add_azure_static_resources(
        self,
        template: Dict[str, Any],
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> None:
        """
        Add Azure resources for static site hosting
        """
        # Storage Account for static website
        template["resources"].append({
            "type": "Microsoft.Storage/storageAccounts",
            "apiVersion": "2021-09-01",
            "name": "[concat(parameters('projectName'), parameters('environment'), 'storage')]",
            "location": "[resourceGroup().location]",
            "sku": {"name": "Standard_LRS"},
            "kind": "StorageV2",
            "properties": {
                "staticWebsite": {
                    "enabled": True,
                    "indexDocument": "index.html",
                    "errorDocument404Path": "index.html"
                }
            }
        })

class GCPTemplateGenerator(BaseTemplateGenerator):
    """
    Google Cloud Deployment Manager template generator
    """
    
    def __init__(self):
        super().__init__(CloudProvider.GCP)
    
    async def generate_template(
        self,
        project_type: ProjectType,
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate GCP Deployment Manager template
        """
        template = {
            "resources": []
        }
        
        if project_type in [ProjectType.STATIC_SITE, ProjectType.SPA]:
            self._add_gcp_static_resources(template, requirements, project_config)
        
        return {
            "template": template,
            "format": "deployment_manager",
            "provider": "gcp",
            "deployment_method": "gcloud_deployment"
        }
    
    def get_template_preview(self, project_type: ProjectType) -> Dict[str, Any]:
        """
        Get GCP template preview
        """
        return {
            "provider": "gcp",
            "format": "deployment_manager",
            "estimated_resources": ["Cloud Storage Bucket", "Cloud CDN", "Load Balancer"]
        }
    
    def _add_gcp_static_resources(
        self,
        template: Dict[str, Any],
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> None:
        """
        Add GCP resources for static site hosting
        """
        project_name = project_config.get("project_name") or "webapp"
        
        # Cloud Storage Bucket
        template["resources"].append({
            "name": f"{project_name}-website-bucket",
            "type": "storage.v1.bucket",
            "properties": {
                "website": {
                    "mainPageSuffix": "index.html",
                    "notFoundPage": "index.html"
                },
                "iamConfiguration": {
                    "uniformBucketLevelAccess": {"enabled": True}
                }
            }
        })

class DigitalOceanTemplateGenerator(BaseTemplateGenerator):
    """
    DigitalOcean template generator (using their API structure)
    """
    
    def __init__(self):
        super().__init__(CloudProvider.DIGITALOCEAN)
    
    async def generate_template(
        self,
        project_type: ProjectType,
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate DigitalOcean configuration
        """
        config = {
            "droplets": [],
            "spaces": [],
            "cdn": [],
            "apps": []
        }
        
        if project_type in [ProjectType.STATIC_SITE, ProjectType.SPA]:
            self._add_do_static_resources(config, requirements, project_config)
        
        return {
            "template": config,
            "format": "digitalocean_config",
            "provider": "digitalocean",
            "deployment_method": "do_api"
        }
    
    def get_template_preview(self, project_type: ProjectType) -> Dict[str, Any]:
        """
        Get DigitalOcean template preview
        """
        return {
            "provider": "digitalocean",
            "format": "digitalocean_config",
            "estimated_resources": ["Spaces (Object Storage)", "CDN", "App Platform"]
        }
    
    def _add_do_static_resources(
        self,
        config: Dict[str, Any],
        requirements: InfrastructureRequirement,
        project_config: Dict[str, Any]
    ) -> None:
        """
        Add DigitalOcean resources for static site hosting
        """
        project_name = project_config.get("project_name") or "webapp"
        
        # DigitalOcean App Platform
        config["apps"].append({
            "name": f"{project_name}-app",
            "spec": {
                "name": f"{project_name}-app",
                "static_sites": [{
                    "name": "web",
                    "source_dir": "/build",
                    "github": {
                        "repo": project_config.get("github_repo", ""),
                        "branch": "main"
                    }
                }]
            }
        })

# Helper function to create template engine instance
def create_template_engine() -> InfrastructureTemplateEngine:
    """
    Create and return a configured infrastructure template engine
    """
    return InfrastructureTemplateEngine()

# Template utility functions
def detect_project_type(analysis_data: Dict[str, Any]) -> ProjectType:
    """
    Detect project type from analysis data
    """
    framework_raw = analysis_data.get("framework", "")
    framework = str(framework_raw).lower() if framework_raw else ""
    languages = analysis_data.get("languages", [])
    has_server = analysis_data.get("has_server_code", False)
    has_database = analysis_data.get("database_config") is not None
    
    if not has_server and ("html" in languages or "javascript" in languages):
        if framework in ["react", "vue", "angular"]:
            return ProjectType.SPA
        else:
            return ProjectType.STATIC_SITE
    elif has_server and has_database:
        return ProjectType.FULLSTACK_APP
    elif has_server and not has_database:
        return ProjectType.API_SERVICE
    elif analysis_data.get("containerization"):
        return ProjectType.CONTAINER_APP
    else:
        return ProjectType.STATIC_SITE  # Default fallback

def detect_requirements(analysis_data: Dict[str, Any]) -> InfrastructureRequirement:
    """
    Detect infrastructure requirements from analysis data
    """
    requirements = InfrastructureRequirement()
    
    # Storage needed for static files or file uploads
    requirements.storage = True  # Almost always needed
    
    # CDN for better performance
    requirements.cdn = True  # Recommended for all projects
    
    # Compute needed for server-side applications
    requirements.compute = analysis_data.get("has_server_code", False)
    
    # Database detection
    requirements.database = analysis_data.get("database_config") is not None
    
    # Load balancer for high-traffic applications
    requirements.load_balancer = requirements.compute and analysis_data.get("expected_traffic", "low") == "high"
    
    # Container registry for containerized apps
    requirements.container_registry = analysis_data.get("containerization") is not None
    
    # Auto-scaling for production applications
    requirements.auto_scaling = analysis_data.get("environment") == "production" and requirements.compute
    
    # Backup for production databases
    requirements.backup = requirements.database and analysis_data.get("environment") == "production"
    
    return requirements
