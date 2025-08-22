# Smart Deploy Controller - Traditional Terraform-based infrastructure deployment
import json
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import tempfile
import shutil

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import redis.asyncio as redis

from ..utils.memory_storage import create_memory_redis_client
from ..services.enhanced_analysis_service import EnhancedAnalysisService
from ..services.template_selector import TemplateSelector
from ..services.terraform_executor import TerraformExecutor
from ..models.enhanced_models import User, Organization, DeploymentHistory, DeploymentStatus
from ..utils.database import get_db_session

# Import real deployment services - Traditional Terraform Templates Approach
try:
    import sys
    import os
    backend_dir = os.path.join(os.path.dirname(__file__), '../..')
    sys.path.append(backend_dir)
    
    from src.services import (
        get_websocket_service
    )
    REAL_DEPLOYMENT_AVAILABLE = True
    print("✅ Traditional Terraform Templates loaded successfully")
except ImportError as e:
    print(f"Warning: WebSocket service not available: {e}")
    REAL_DEPLOYMENT_AVAILABLE = False

class SmartDeployError(Exception):
    """Custom exception for Smart Deploy operations"""
    pass

class SmartDeployController:
    """
    Main controller for Traditional Terraform-based Smart Deployments
    Orchestrates the entire process from repository analysis to infrastructure deployment
    """
    
    def __init__(self):
        self.analysis_service = EnhancedAnalysisService()
        self.template_selector = TemplateSelector()
        self.terraform_executor = TerraformExecutor()
        
        # Redis for deployment state management
        self.redis_client = None
        
        # Deployment tracking
        self.active_deployments: Dict[str, Dict] = {}
        self.cleanup_task = None
        
        # Real deployment orchestrator
        if REAL_DEPLOYMENT_AVAILABLE:
            try:
                # Import dependencies locally to avoid scope issues
                from ..utils.websocket_manager import WebSocketManager
                
                websocket_manager = WebSocketManager()
                # Simplified deployment without orchestrator
                # (DeploymentOrchestrator removed due to Claude dependencies)
                print("✅ Real deployment services enabled")
            except Exception as e:
                print(f"⚠️ Failed to initialize deployment orchestrator: {e}")
                self.deployment_orchestrator = None
        else:
            self.deployment_orchestrator = None
            print("⚠️ Using simulated deployment (real services not available)")
        
    async def get_redis_client(self) -> Any:
        """Get Redis client for deployment state management"""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url("redis://localhost:6379/1")
                await self.redis_client.ping()
                print("✅ Connected to Redis successfully")
            except Exception as e:
                # Use in-memory fallback if Redis not available
                print(f"⚠️ Redis not available ({str(e)}), using in-memory storage")
                self.redis_client = create_memory_redis_client()
            
            # Start cleanup task when Redis is first accessed
            await self.start_cleanup_if_needed()
        
        return self.redis_client
    
    async def start_cleanup_if_needed(self):
        """Start cleanup task if not already running"""
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._start_cleanup_loop())
            print("🧹 Started deployment cleanup task")
    
    async def analyze_repository_basic(
        self, 
        repo_path: str, 
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Basic repository analysis for testing
        """
        return {
            "success": True,
            "framework": "react",
            "languages": ["javascript"],
            "has_server_code": False,
            "database_config": None,
            "project_type": "spa"
        }
    
    async def analyze_repository_enhanced(
        self, 
        repo_path: str, 
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Enhanced repository analysis for testing
        """
        return {
            "success": True,
            "framework": "react",
            "languages": ["javascript", "html", "css"],
            "has_server_code": False,
            "database_config": None,
            "complexity_score": 3,
            "deployment_confidence": 0.85,
            "project_summary": {
                "name": "Test Project",
                "type": "spa",
                "framework": "react",
                "languages": ["javascript", "html", "css"],
                "estimated_size": "medium"
            },
            "recommendations": [
                {
                    "type": "infrastructure",
                    "priority": "high",
                    "description": "Use AWS S3 + CloudFront for optimal SPA hosting"
                },
                {
                    "type": "optimization",
                    "priority": "medium", 
                    "description": "Enable gzip compression for better performance"
                },
                {
                    "type": "security",
                    "priority": "high",
                    "description": "Configure HTTPS with SSL certificate"
                }
            ]
        }
    
    async def analyze_repository(
        self, 
        repo_path: str, 
        user_id: str,
        deployment_id: str
    ) -> Dict[str, Any]:
        """
        Analyze repository for Smart Deploy
        """
        try:
            await self._update_deployment_status(
                deployment_id, 
                DeploymentStatus.ANALYZING,
                "🔍 Analyzing repository structure and requirements..."
            )
            
            # Enhanced analysis for template selection
            analysis_result = await self.analysis_service.analyze_for_terraform_template(repo_path)
            
            # Store analysis results
            await self._store_deployment_data(deployment_id, "analysis", analysis_result)
            
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.ANALYSIS_COMPLETE,
                f"✅ Analysis complete - {analysis_result.get('project_type', 'Unknown')} project detected"
            )
            
            return analysis_result
            
        except Exception as e:
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.FAILED,
                f"❌ Analysis failed: {str(e)}"
            )
            raise SmartDeployError(f"Repository analysis failed: {str(e)}")
    
    async def generate_infrastructure(
        self,
        deployment_id: str,
        analysis_data: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate infrastructure code using traditional Terraform templates
        """
        try:
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.GENERATING,
                "🏗️ Analyzing project and selecting optimal Terraform template..."
            )
            
            # Use the template selector to determine the best template
            selected_template, template_info = self.template_selector.analyze_and_select_template(
                analysis_data, deployment_config
            )
            
            print(f"📋 Selected template: {selected_template}")
            print(f"📝 Template info: {template_info}")
            
            # Generate template-specific variables
            template_variables = self.template_selector.get_template_variables(
                selected_template, analysis_data, deployment_config
            )
            
            # Load the Terraform template files
            terraform_template = self._get_terraform_template(selected_template, deployment_config)
            
            # Update status to ready
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.READY,
                f"✅ {template_info.get('name', 'Template')} ready for deployment"
            )
            
            # Store deployment data with template information
            deployment_update = {
                "terraform_code": terraform_template,
                "selected_template": selected_template,
                "template_info": template_info,
                "template_variables": template_variables,
                "status": "ready",
                "progress": 100,
                "message": f"✅ {template_info.get('name', 'Infrastructure')} ready for deployment"
            }
            await self._store_deployment_data(deployment_id, "final_status", deployment_update)
            
            # Process and validate infrastructure
            infrastructure_result = await self._process_infrastructure_code(
                terraform_template.get("main_tf", ""),
                analysis_data,
                deployment_config
            )
            
            # Store infrastructure results
            await self._store_deployment_data(deployment_id, "infrastructure", infrastructure_result)
            
            return infrastructure_result
            
        except Exception as e:
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.FAILED,
                f"❌ Infrastructure template selection failed: {str(e)}"
            )
            raise SmartDeployError(f"Infrastructure generation failed: {str(e)}")
    
    def _get_terraform_template(
        self, 
        project_type: str, 
        deployment_config: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Get appropriate Terraform template based on project type from file system
        """
        # Map project types to template directories
        template_mapping = {
            "static_site": "static_site",
            "spa": "static_site",  # SPAs use static site template
            "react": "static_site",  # React apps use static site template
            "vue": "static_site",    # Vue apps use static site template
            "angular": "static_site", # Angular apps use static site template
            "react_node_app": "react_node_app",
            "fullstack": "react_node_app",  # Full-stack apps use react_node_app template
            "api": "react_node_app",        # API apps use react_node_app template
            "node": "react_node_app",       # Node apps use react_node_app template
        }
        
        # Default to static_site if project type not recognized
        template_name = template_mapping.get(project_type, "static_site")
        
        try:
            # Get the infrastructure templates directory
            backend_dir = Path(__file__).resolve().parent.parent.parent
            templates_dir = backend_dir.parent / "infrastructure" / "templates" / template_name
            
            if not templates_dir.exists():
                raise SmartDeployError(f"Template directory not found: {templates_dir}")
            
            # Read all template files
            template_files = {}
            required_files = ["main.tf", "variables.tf", "outputs.tf", "provider.tf"]
            
            for file_name in required_files:
                file_path = templates_dir / file_name
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Apply variable substitution for common values
                    content = self._apply_template_variables(content, deployment_config)
                    template_files[file_name.replace('.', '_')] = content
                else:
                    raise SmartDeployError(f"Required template file not found: {file_path}")
            
            print(f"✅ Loaded Terraform template: {template_name}")
            print(f"📁 Template files: {list(template_files.keys())}")
            
            return template_files
            
        except Exception as e:
            print(f"❌ Failed to load template {template_name}: {str(e)}")
            # Fallback to a simple static site template if file loading fails
            return self._get_fallback_template(deployment_config)
    
    def _apply_template_variables(self, content: str, deployment_config: Dict[str, Any]) -> str:
        """
        Apply basic variable substitution to template content
        """
        try:
            project_name = deployment_config.get("project_name") or "webapp"
            environment = deployment_config.get("environment", "prod")
            aws_region = deployment_config.get("aws_region", "us-east-1")
            domain_name = deployment_config.get("domain_name", "")
            
            # Apply substitutions for template variables that need dynamic defaults
            substitutions = {
                "{{PROJECT_NAME}}": project_name,
                "{{ENVIRONMENT}}": environment,
                "{{AWS_REGION}}": aws_region,
                "{{DOMAIN_NAME}}": domain_name,
            }
            
            for placeholder, value in substitutions.items():
                content = content.replace(placeholder, value)
            
            return content
        except Exception as e:
            print(f"⚠️ Warning: Failed to apply template variables: {e}")
            return content
    
    def _get_fallback_template(self, deployment_config: Dict[str, Any]) -> Dict[str, str]:
        """
        Fallback template if file-based templates are not available
        """
        project_name = deployment_config.get("project_name") or "webapp"
        region = deployment_config.get("aws_region", "us-east-1")
        
        return {
            "main_tf": f'''
# Fallback Static Website Infrastructure
resource "aws_s3_bucket" "website" {{
  bucket = "{project_name}-website-bucket-${{random_id.suffix.hex}}"
}}

resource "random_id" "suffix" {{
  byte_length = 4
}}

resource "aws_s3_bucket_public_access_block" "website" {{
  bucket = aws_s3_bucket.website.id
  
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}}

resource "aws_s3_bucket_website_configuration" "website" {{
  bucket = aws_s3_bucket.website.id
  
  index_document {{
    suffix = "index.html"
  }}
}}

resource "aws_s3_bucket_policy" "website" {{
  bucket = aws_s3_bucket.website.id
  
  policy = jsonencode({{
    Version = "2012-10-17"
    Statement = [
      {{
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${{aws_s3_bucket.website.arn}}/*"
      }}
    ]
  }})
  
  depends_on = [aws_s3_bucket_public_access_block.website]
}}
''',
            "variables_tf": f'''
variable "project_name" {{
  description = "Name of the project"
  type        = string
  default     = "{project_name}"
}}

variable "aws_region" {{
  description = "AWS region"
  type        = string
  default     = "{region}"
}}
''',
            "outputs_tf": '''
output "website_url" {
  description = "Website URL"
  value       = "https://${aws_s3_bucket.website.bucket_regional_domain_name}"
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = aws_s3_bucket.website.bucket
}
''',
            "provider_tf": f'''
terraform {{
  required_version = ">= 1.0"
  
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
    random = {{
      source  = "hashicorp/random"
      version = "~> 3.1"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
}}
'''
        }
    
    async def create_smart_deployment(
        self,
        user_id: str,
        repo_path: str,
        deployment_config: Dict[str, Any],
        background_tasks: BackgroundTasks
    ) -> Dict[str, Any]:
        """
        Create a new Smart Deployment with AI-powered infrastructure generation
        """
        deployment_id = str(uuid.uuid4())
        
        try:
            # Initialize deployment tracking
            deployment_data = {
                "id": deployment_id,
                "user_id": user_id,
                "repo_path": repo_path,
                "config": deployment_config,
                "status": DeploymentStatus.INITIALIZING,
                "created_at": datetime.utcnow().isoformat(),
                "steps": []
            }
            
            await self._store_deployment_data(deployment_id, "metadata", deployment_data)
            
            # Store repo path and config separately for real deployment
            await self._store_deployment_data(deployment_id, "repo_path", repo_path)
            await self._store_deployment_data(deployment_id, "config", deployment_config)
            
            # Update deployment status for tracking
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.INITIALIZING,
                "Smart deployment started - AI analysis in progress"
            )
            
            # Start background processing
            background_tasks.add_task(
                self._process_smart_deployment,
                deployment_id,
                user_id,
                repo_path,
                deployment_config
            )
            
            return {
                "deployment_id": deployment_id,
                "status": "initializing",
                "message": "Smart deployment started - AI analysis in progress",
                "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
            }
            
        except Exception as e:
            raise SmartDeployError(f"Failed to create smart deployment: {str(e)}")
    
    async def _process_smart_deployment(
        self,
        deployment_id: str,
        user_id: str,
        repo_path: str,
        deployment_config: Dict[str, Any]
    ) -> None:
        """
        Background task to process the complete Smart Deployment workflow
        """
        try:
            print(f"🧪 DEBUG: Starting _process_smart_deployment for {deployment_id}")
            
            # Step 1: Repository Analysis
            print(f"🧪 DEBUG: Starting repository analysis...")
            analysis_data = await self.analyze_repository(repo_path, user_id, deployment_id)
            print(f"🧪 DEBUG: Repository analysis completed: {type(analysis_data)}")
            
            # Step 2: Infrastructure Generation
            print(f"🧪 DEBUG: Starting infrastructure generation...")
            infrastructure_data = await self.generate_infrastructure(
                deployment_id, 
                analysis_data, 
                deployment_config
            )
            
            # Step 3: Deployment Pipeline Creation
            print(f"🧪 DEBUG: Starting pipeline creation...")
            pipeline_data = await self._create_deployment_pipeline(
                deployment_id,
                analysis_data,
                infrastructure_data,
                deployment_config
            )
            print(f"🧪 DEBUG: Pipeline creation completed")
            
            # Step 4: Final preparation
            print(f"🧪 DEBUG: Starting finalization...")
            await self._finalize_deployment(deployment_id, pipeline_data)
            print(f"🧪 DEBUG: Finalization completed")
            
        except Exception as e:
            print(f"🧪 DEBUG: Exception in _process_smart_deployment: {e}")
            print(f"🧪 DEBUG: Exception type: {type(e).__name__}")
            import traceback
            print(f"🧪 DEBUG: Full traceback:")
            traceback.print_exc()
            
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.FAILED,
                f"❌ Smart deployment failed: {str(e)}"
            )
    
    async def _create_deployment_pipeline(
        self,
        deployment_id: str,
        analysis_data: Dict[str, Any],
        infrastructure_data: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create CI/CD pipeline configuration
        """
        try:
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.CREATING_PIPELINE,
                "⚙️ Creating optimized deployment pipeline..."
            )
            
            # Generate pipeline based on project type and infrastructure
            project_type = analysis_data.get("project_type", "static_site")
            cloud_provider = deployment_config.get("cloud_provider", "aws")
            
            pipeline_config = {
                "project_type": project_type,
                "cloud_provider": cloud_provider,
                "build_steps": self._generate_build_steps(analysis_data),
                "deploy_steps": self._generate_deploy_steps(infrastructure_data),
                "monitoring": self._generate_monitoring_config(deployment_config),
                "rollback": self._generate_rollback_config(infrastructure_data)
            }
            
            # Store pipeline configuration
            await self._store_deployment_data(deployment_id, "pipeline", pipeline_config)
            
            return pipeline_config
            
        except Exception as e:
            raise SmartDeployError(f"Pipeline creation failed: {str(e)}")
    
    async def _finalize_deployment(
        self,
        deployment_id: str,
        pipeline_data: Dict[str, Any]
    ) -> None:
        """
        Finalize the Smart Deployment and perform real AWS deployment
        """
        try:
            # Calculate deployment summary
            deployment_summary = await self._generate_deployment_summary(deployment_id)
            
            # Traditional Terraform Templates are always available
            if REAL_DEPLOYMENT_AVAILABLE:
                await self._perform_real_deployment(deployment_id, pipeline_data)
            else:
                await self._update_deployment_status(
                    deployment_id,
                    DeploymentStatus.READY,
                    "🚀 Smart deployment ready! (Traditional Terraform templates loaded)"
                )
            
            # Store final summary
            await self._store_deployment_data(deployment_id, "summary", deployment_summary)
            
        except Exception as e:
            raise SmartDeployError(f"Deployment finalization failed: {str(e)}")
    
    async def _perform_real_deployment(
        self,
        deployment_id: str,
        pipeline_data: Dict[str, Any]
    ) -> None:
        """
        Perform actual AWS deployment using Traditional Terraform Templates
        """
        try:
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.DEPLOYING,
                "🚀 Deploying to AWS cloud infrastructure..."
            )
            
            # Get deployment data for real deployment
            redis_client = await self.get_redis_client()
            repo_path = None
            deployment_config = {}
            
            if redis_client:
                repo_data = await redis_client.get(f"deployment:{deployment_id}:repo_path")
                config_data = await redis_client.get(f"deployment:{deployment_id}:config")
                if repo_data:
                    repo_path = repo_data.decode()
                if config_data:
                    deployment_config = json.loads(config_data)
            
            if not repo_path:
                raise SmartDeployError("Repository path not found for deployment")
            
            # Use Traditional Terraform Templates Approach
            environment = deployment_config.get("environment", "production")
            
            # Execute traditional Terraform deployment
            terraform_config = {
                "project_type": pipeline_data.get("project_type", "static_site"),
                "environment": environment,
                "deployment_id": deployment_id,
                "repo_path": repo_path,
                "project_name": deployment_config.get("project_name", f"project-{deployment_id[:8]}"),
                "aws_region": deployment_config.get("aws_region", "us-east-1"),
                "domain_name": deployment_config.get("domain_name"),
                "auto_deploy": deployment_config.get("auto_deploy", False)
            }
            
            # Execute traditional Terraform deployment using TerraformExecutor
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.DEPLOYING,
                "☁️ Provisioning AWS infrastructure..."
            )
            
            # Execute Traditional Terraform deployment
            try:
                # Use TerraformExecutor for deployment
                result = await self.terraform_executor.execute_terraform_deployment(
                    deployment_id=deployment_id,
                    template_files=terraform_config.get("template_files", {}),
                    template_variables=terraform_config.get("template_variables", {}),
                    deployment_config=deployment_config
                )
                
                print(f"🏗️ Traditional Terraform deployment result: {result}")
                print(f"🏗️ Result status: {result.get('status', 'unknown')}")
                
                if result.get("status") == "completed":
                    await self._update_deployment_status(
                        deployment_id,
                        DeploymentStatus.COMPLETED,
                        f"✅ Traditional Terraform deployment completed! URL: {result.get('live_url', 'Pending DNS propagation')}"
                    )
                    
                    # Store deployment URL
                    if result.deployment_url:
                        await self._store_deployment_data(deployment_id, "deployment_url", result.deployment_url)
                        
                else:
                    error_message = getattr(result, 'error_message', 'Unknown deployment error')
                    await self._update_deployment_status(
                        deployment_id,
                        DeploymentStatus.FAILED,
                        f"❌ AWS deployment failed: {error_message}"
                    )
                    
            except Exception as deploy_error:
                print(f"🧪 DEBUG: Exception during deployment: {deploy_error}")
                await self._update_deployment_status(
                    deployment_id,
                    DeploymentStatus.FAILED,
                    f"❌ Deployment execution failed: {str(deploy_error)}"
                )
                
        except Exception as e:
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.FAILED,
                f"❌ Real deployment failed: {str(e)}"
            )
    
    async def _update_deployment_status(
        self,
        deployment_id: str,
        status: DeploymentStatus,
        message: str
    ) -> None:
        """
        Update deployment status with real-time updates
        """
        # Convert enum to string for frontend compatibility
        status_string = status.value
        if status == DeploymentStatus.READY:
            status_string = "ready"
        elif status == DeploymentStatus.FAILED:
            status_string = "error"
        elif status == DeploymentStatus.GENERATING:
            status_string = "generating"
        elif status == DeploymentStatus.INFRASTRUCTURE_READY:
            status_string = "infrastructure_ready"
        
        status_data = {
            "deployment_id": deployment_id,
            "status": status_string,  # Use string status for frontend
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
            "progress": self._calculate_progress(status)
        }
        
        try:
            # Store in Redis for real-time updates
            redis_client = await self.get_redis_client()
            if redis_client:
                await redis_client.setex(
                    f"deployment:{deployment_id}:status",
                    3600,  # 1 hour TTL
                    json.dumps(status_data)
                )
                
                # Also store with a simpler key for easier access
                await redis_client.setex(
                    f"deployment_status:{deployment_id}",
                    3600,
                    json.dumps(status_data)
                )
            
            # Store in memory as fallback
            self.active_deployments[deployment_id] = status_data
            
            print(f"🧪 DEBUG: Status updated to {status_string} (progress: {status_data['progress']}%)")
            
        except Exception as e:
            # Fallback to in-memory only
            self.active_deployments[deployment_id] = status_data
            print(f"🧪 DEBUG: Redis failed, using memory fallback for status: {status_string}")
    
    async def _store_deployment_data(
        self,
        deployment_id: str,
        data_type: str,
        data: Dict[str, Any]
    ) -> None:
        """
        Store deployment data (analysis, infrastructure, etc.)
        """
        try:
            redis_client = await self.get_redis_client()
            if redis_client:
                await redis_client.setex(
                    f"deployment:{deployment_id}:{data_type}",
                    7200,  # 2 hours TTL
                    json.dumps(data, default=str)
                )
        except Exception:
            # Could store in database as fallback
            pass
    
    def _assess_complexity(self, analysis_data: Dict[str, Any]) -> str:
        """
        Assess project complexity for template selection
        """
        factors = {
            "languages": len(analysis_data.get("languages", [])),
            "dependencies": len(analysis_data.get("dependencies", [])),
            "files": len(analysis_data.get("file_structure", [])),
            "has_database": bool(analysis_data.get("database_config")),
            "has_microservices": "microservice" in str(analysis_data.get("architecture", "")).lower(),
            "has_docker": bool(analysis_data.get("containerization"))
        }
        
        complexity_score = (
            factors["languages"] * 2 +
            min(factors["dependencies"] // 10, 5) +
            min(factors["files"] // 20, 5) +
            (5 if factors["has_database"] else 0) +
            (10 if factors["has_microservices"] else 0) +
            (3 if factors["has_docker"] else 0)
        )
        
        if complexity_score < 10:
            return "simple"
        elif complexity_score < 25:
            return "moderate"
        else:
            return "complex"
    
    def _calculate_progress(self, status: DeploymentStatus) -> int:
        """
        Calculate deployment progress percentage
        """
        progress_map = {
            DeploymentStatus.INITIALIZING: 5,
            DeploymentStatus.ANALYZING: 20,
            DeploymentStatus.ANALYSIS_COMPLETE: 35,
            DeploymentStatus.GENERATING: 50,
            DeploymentStatus.INFRASTRUCTURE_READY: 70,
            DeploymentStatus.CREATING_PIPELINE: 85,
            DeploymentStatus.READY: 100,
            DeploymentStatus.FAILED: 0
        }
        return progress_map.get(status, 0)
    
    async def _process_infrastructure_code(
        self,
        infrastructure_code: str,
        analysis_data: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process and validate generated infrastructure code
        """
        # Parse infrastructure code format (YAML/JSON/Terraform)
        code_format = self._detect_infrastructure_format(infrastructure_code)
        
        # Validate infrastructure code
        validation_result = await self._validate_infrastructure_code(
            infrastructure_code, 
            code_format
        )
        
        # Generate deployment resources list
        resources = self._extract_infrastructure_resources(infrastructure_code, code_format)
        
        return {
            "code": infrastructure_code,
            "format": code_format,
            "validation": validation_result,
            "resources": resources,
            "estimated_cost": self._estimate_infrastructure_cost(resources),
            "deployment_time": self._estimate_deployment_time(resources)
        }
    
    def _detect_infrastructure_format(self, code: str) -> str:
        """
        Detect infrastructure code format
        """
        code_lower = code.lower().strip()
        
        if code_lower.startswith("awstemplateformatversion") or "resources:" in code_lower:
            return "cloudformation"
        elif "terraform" in code_lower or "resource \"" in code_lower:
            return "terraform"
        elif code_lower.startswith("{") and "resources" in code_lower:
            return "arm"  # Azure Resource Manager
        else:
            return "cloudformation"  # Default fallback
    
    async def _validate_infrastructure_code(
        self, 
        code: str, 
        format_type: str
    ) -> Dict[str, Any]:
        """
        Basic validation of infrastructure code
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Basic syntax checks
        if not code.strip():
            validation["valid"] = False
            validation["errors"].append("Empty infrastructure code")
            return validation
        
        # Format-specific validation
        if format_type == "cloudformation":
            if "Resources:" not in code and "resources:" not in code:
                validation["warnings"].append("No resources section found")
        
        return validation
    
    def _extract_infrastructure_resources(
        self, 
        code: str, 
        format_type: str
    ) -> List[Dict[str, Any]]:
        """
        Extract resource list from infrastructure code
        """
        resources = []
        
        # Simple resource extraction (could be enhanced with proper parsing)
        if format_type == "cloudformation":
            # Look for AWS resource types
            aws_resources = [
                "AWS::S3::Bucket", "AWS::CloudFront::Distribution",
                "AWS::Lambda::Function", "AWS::ApiGateway::RestApi",
                "AWS::EC2::Instance", "AWS::RDS::DBInstance"
            ]
            
            for resource_type in aws_resources:
                if resource_type in code:
                    resources.append({
                        "type": resource_type,
                        "provider": "aws",
                        "category": self._categorize_resource(resource_type)
                    })
        
        return resources
    
    def _categorize_resource(self, resource_type: str) -> str:
        """
        Categorize AWS resource types
        """
        if "S3" in resource_type or "CloudFront" in resource_type:
            return "storage"
        elif "Lambda" in resource_type or "ApiGateway" in resource_type:
            return "compute"
        elif "EC2" in resource_type:
            return "virtual_machine"
        elif "RDS" in resource_type:
            return "database"
        else:
            return "other"
    
    def _estimate_infrastructure_cost(self, resources: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Rough cost estimation for infrastructure resources
        """
        cost_estimates = {
            "storage": 2.0,   # $2/month for basic S3 + CloudFront
            "compute": 10.0,  # $10/month for Lambda/API Gateway
            "virtual_machine": 25.0,  # $25/month for small EC2
            "database": 15.0  # $15/month for small RDS
        }
        
        monthly_cost = 0.0
        cost_breakdown = {}
        
        for resource in resources:
            category = resource.get("category", "other")
            cost = cost_estimates.get(category, 5.0)
            monthly_cost += cost
            cost_breakdown[category] = cost_breakdown.get(category, 0) + cost
        
        return {
            "monthly_usd": round(monthly_cost, 2),
            "yearly_usd": round(monthly_cost * 12, 2),
            "breakdown": cost_breakdown
        }
    
    def _estimate_deployment_time(self, resources: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Estimate deployment time based on resources
        """
        base_time = 2  # 2 minutes base
        resource_time = len(resources) * 1  # 1 minute per resource
        
        total_minutes = base_time + resource_time
        
        return {
            "estimated_minutes": total_minutes,
            "estimated_seconds": total_minutes * 60
        }
    
    def _generate_build_steps(self, analysis_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate build steps based on project analysis
        """
        project_type = analysis_data.get("project_type", "static_site")
        build_tools = analysis_data.get("build_tools", [])
        
        steps = []
        
        # Common setup steps
        steps.append({
            "name": "checkout",
            "action": "checkout_code",
            "description": "Check out source code"
        })
        
        # Language-specific steps
        if "npm" in build_tools or "node" in analysis_data.get("languages", []):
            steps.extend([
                {
                    "name": "setup_node",
                    "action": "setup_node",
                    "version": "18",
                    "description": "Setup Node.js environment"
                },
                {
                    "name": "install_dependencies",
                    "action": "run_command",
                    "command": "npm ci",
                    "description": "Install dependencies"
                },
                {
                    "name": "build",
                    "action": "run_command",
                    "command": "npm run build",
                    "description": "Build application"
                }
            ])
        
        return steps
    
    def _generate_deploy_steps(self, infrastructure_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate deployment steps based on infrastructure
        """
        resources = infrastructure_data.get("resources", [])
        
        steps = [
            {
                "name": "deploy_infrastructure",
                "action": "deploy_cloudformation",
                "description": "Deploy infrastructure resources"
            }
        ]
        
        # Add resource-specific deployment steps
        for resource in resources:
            if resource.get("category") == "storage":
                steps.append({
                    "name": "upload_assets",
                    "action": "upload_to_s3",
                    "description": "Upload application assets"
                })
        
        return steps
    
    def _generate_monitoring_config(self, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate monitoring configuration
        """
        return {
            "health_checks": True,
            "metrics": ["response_time", "error_rate", "throughput"],
            "alerts": {
                "error_rate_threshold": 5.0,
                "response_time_threshold": 1000
            }
        }
    
    def _generate_rollback_config(self, infrastructure_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate rollback configuration
        """
        return {
            "enabled": True,
            "strategy": "blue_green",
            "rollback_timeout_minutes": 5,
            "health_check_required": True
        }
    
    async def _generate_deployment_summary(self, deployment_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive deployment summary
        """
        try:
            # Get stored data
            redis_client = await self.get_redis_client()
            
            analysis_data = {}
            infrastructure_data = {}
            pipeline_data = {}
            
            if redis_client:
                analysis_raw = await redis_client.get(f"deployment:{deployment_id}:analysis")
                infrastructure_raw = await redis_client.get(f"deployment:{deployment_id}:infrastructure")
                pipeline_raw = await redis_client.get(f"deployment:{deployment_id}:pipeline")
                
                if analysis_raw:
                    analysis_data = json.loads(analysis_raw)
                if infrastructure_raw:
                    infrastructure_data = json.loads(infrastructure_raw)
                if pipeline_raw:
                    pipeline_data = json.loads(pipeline_raw)
            
            return {
                "deployment_id": deployment_id,
                "project_summary": {
                    "type": analysis_data.get("project_type", "Unknown"),
                    "languages": analysis_data.get("languages", []),
                    "framework": analysis_data.get("framework", "None")
                },
                "infrastructure_summary": {
                    "resources": len(infrastructure_data.get("resources", [])),
                    "estimated_cost": infrastructure_data.get("estimated_cost", {}),
                    "deployment_time": infrastructure_data.get("deployment_time", {})
                },
                "deployment_ready": True,
                "next_steps": [
                    "Review generated infrastructure code",
                    "Configure environment variables",
                    "Click 'Deploy' to launch your application"
                ]
            }
            
        except Exception as e:
            return {
                "deployment_id": deployment_id,
                "error": f"Failed to generate summary: {str(e)}"
            }
    
    async def execute_deployment(
        self,
        deployment_id: str,
        deployment_config: Dict[str, Any],
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Execute the actual Terraform deployment
        
        This method takes a generated infrastructure template and deploys it to AWS
        """
        try:
            print(f"🚀 Starting deployment execution for {deployment_id}")
            
            # Get the stored deployment data
            redis_client = await self.get_redis_client()
            
            # Retrieve template data
            template_data_key = f"deployment:{deployment_id}:final_status"
            template_data_str = await redis_client.get(template_data_key)
            
            if not template_data_str:
                raise SmartDeployError(f"No template data found for deployment {deployment_id}")
            
            template_data = json.loads(template_data_str)
            terraform_template = template_data.get("terraform_code", {})
            template_variables = template_data.get("template_variables", {})
            selected_template = template_data.get("selected_template", "static_site")
            
            print(f"📋 Using template: {selected_template}")
            print(f"🔧 Variables: {list(template_variables.keys())}")
            
            # Enhanced deployment configuration
            enhanced_config = {
                **deployment_config,
                "selected_template": selected_template,
                "auto_approve": auto_approve,
                "dry_run": deployment_config.get("dry_run", False)
            }
            
            # Execute Terraform deployment
            execution_result = await self.terraform_executor.execute_deployment(
                deployment_id=deployment_id,
                template_files=terraform_template,
                template_variables=template_variables,
                deployment_config=enhanced_config
            )
            
            # Store final results
            final_result = {
                **execution_result,
                "template_used": selected_template,
                "variables_applied": template_variables,
                "deployment_config": enhanced_config,
                "completed_at": datetime.utcnow().isoformat()
            }
            
            # Update deployment status with final result
            await self._store_deployment_data(deployment_id, "execution_result", final_result)
            
            # Update overall deployment status
            if execution_result["status"] == "completed":
                await self._update_deployment_status(
                    deployment_id,
                    DeploymentStatus.COMPLETED,
                    f"🎉 Deployment completed! {execution_result.get('message', '')}"
                )
            elif execution_result["status"] == "plan_complete":
                await self._update_deployment_status(
                    deployment_id,
                    DeploymentStatus.READY,
                    f"📋 Plan completed! {execution_result.get('message', '')}"
                )
            
            print(f"✅ Deployment execution completed: {execution_result['status']}")
            
            return final_result
            
        except Exception as e:
            error_message = f"Deployment execution failed: {str(e)}"
            print(f"❌ {error_message}")
            
            await self._update_deployment_status(
                deployment_id,
                DeploymentStatus.FAILED,
                f"❌ {error_message}"
            )
            
            raise SmartDeployError(error_message)
    
    async def get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get comprehensive deployment status including Terraform execution progress
        """
        try:
            # Get basic deployment status
            basic_status = await self._get_deployment_data(deployment_id, "metadata")
            
            # Get Terraform execution status
            terraform_status = await self.terraform_executor.get_deployment_status(deployment_id)
            
            # Get recent logs
            logs = await self.terraform_executor.get_deployment_logs(deployment_id, limit=50)
            
            # Combine all status information
            comprehensive_status = {
                "deployment_id": deployment_id,
                "basic_status": basic_status,
                "terraform_status": terraform_status,
                "logs": logs,
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return comprehensive_status
            
        except Exception as e:
            return {
                "deployment_id": deployment_id,
                "status": "error",
                "error": f"Failed to get deployment status: {str(e)}"
            }
    
    async def get_deployment_outputs(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get deployment outputs including live URLs and resource information
        """
        try:
            # Get execution result with outputs
            execution_result = await self._get_deployment_data(deployment_id, "execution_result")
            
            if not execution_result:
                return {"error": "No execution results found"}
            
            outputs = execution_result.get("outputs", {})
            
            # Enhance outputs with additional information
            enhanced_outputs = {
                "deployment_id": deployment_id,
                "status": execution_result.get("status", "unknown"),
                "live_url": outputs.get("website_url") or outputs.get("application_url"),
                "resources": outputs,
                "deployment_info": execution_result.get("deployment_config", {}),
                "execution_time": execution_result.get("execution_time", "unknown"),
                "template_used": execution_result.get("template_used", "unknown")
            }
            
            return enhanced_outputs
            
        except Exception as e:
            return {
                "deployment_id": deployment_id,
                "error": f"Failed to get deployment outputs: {str(e)}"
            }

    async def _start_cleanup_loop(self):
        """Start background cleanup task"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_expired_deployments()
            except Exception as e:
                print(f"⚠️ Cleanup task error: {e}")
                await asyncio.sleep(60)  # Retry in 1 minute on error

    async def _cleanup_expired_deployments(self):
        """Clean up expired deployments from Redis and memory"""
        try:
            redis_client = await self.get_redis_client()
            current_time = datetime.utcnow()
            cleaned_count = 0
            
            # Get all deployment keys
            if hasattr(redis_client, 'keys'):
                keys = await redis_client.keys("deployment:*:status")
                
                for key in keys:
                    try:
                        data = await redis_client.get(key)
                        if data:
                            status_data = json.loads(data)
                            timestamp = status_data.get("timestamp")
                            
                            if timestamp:
                                deploy_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00').replace('+00:00', ''))
                                age = current_time - deploy_time
                                
                                # Clean up deployments older than 1 hour
                                if age.total_seconds() > 3600:
                                    deployment_id = key.decode() if isinstance(key, bytes) else key
                                    deployment_id = deployment_id.split(':')[1]
                                    
                                    await self._delete_deployment(deployment_id)
                                    cleaned_count += 1
                    except Exception as e:
                        print(f"⚠️ Error cleaning deployment {key}: {e}")
                        continue
            
            if cleaned_count > 0:
                print(f"🧹 Cleaned up {cleaned_count} expired deployments")
                
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

    async def _delete_deployment(self, deployment_id: str):
        """Delete a deployment from all storage"""
        try:
            redis_client = await self.get_redis_client()
            
            # Delete from Redis
            keys_to_delete = [
                f"deployment:{deployment_id}:status",
                f"deployment:{deployment_id}:metadata", 
                f"deployment:{deployment_id}:execution_result",
                f"deployment:{deployment_id}:deployment_url",
                f"deployment_status:{deployment_id}"
            ]
            
            for key in keys_to_delete:
                await redis_client.delete(key)
            
            # Delete from memory
            if deployment_id in self.active_deployments:
                del self.active_deployments[deployment_id]
                
            print(f"🗑️ Deleted expired deployment: {deployment_id}")
            
        except Exception as e:
            print(f"⚠️ Error deleting deployment {deployment_id}: {e}")

    async def cleanup_deployment_now(self, deployment_id: str):
        """Manually clean up a specific deployment"""
        await self._delete_deployment(deployment_id)
        return {"success": True, "message": f"Deployment {deployment_id} cleaned up"}
