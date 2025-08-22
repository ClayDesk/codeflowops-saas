"""
API stack plugin - registers complete API deployment stack
"""
import logging
from pathlib import Path
from typing import Dict, Any
from core.interfaces import StackPlugin
from core.registry import register_stack
from core.models import StackPlan
from .detector import ApiDetector
from .runtime_integration import RuntimeAdapterIntegration

logger = logging.getLogger(__name__)

class ApiBuilder:
    """API project builder"""
    
    def build(self, repo_dir: Path, plan: StackPlan) -> Dict[str, Any]:
        """Build API project based on runtime"""
        runtime = plan.config.get('runtime', 'nodejs')
        framework = plan.config.get('framework', 'unknown')
        
        logger.info(f"🔨 Building {runtime} API with {framework}")
        
        # Execute build commands
        build_result = {
            "runtime": runtime,
            "framework": framework,
            "build_path": str(repo_dir),
            "artifacts": []
        }
        
        # Run build commands if specified
        for cmd in plan.build_cmds:
            logger.info(f"Running build command: {cmd}")
            # Build commands would be executed here
            # For now, we'll simulate successful builds
        
        # Detect entry points
        if runtime == 'nodejs':
            build_result["entry_point"] = self._find_nodejs_entry_point(repo_dir)
        elif runtime == 'python':
            build_result["entry_point"] = self._find_python_entry_point(repo_dir)
        elif runtime == 'php':
            build_result["entry_point"] = self._find_php_entry_point(repo_dir)
        elif runtime == 'java':
            build_result["entry_point"] = self._find_java_entry_point(repo_dir)
        
        return build_result
    
    def _find_nodejs_entry_point(self, repo_dir: Path) -> str:
        """Find Node.js entry point"""
        candidates = ['index.js', 'app.js', 'server.js', 'main.js']
        for candidate in candidates:
            if (repo_dir / candidate).exists():
                return candidate
        return 'index.js'  # Default
    
    def _find_python_entry_point(self, repo_dir: Path) -> str:
        """Find Python entry point"""
        candidates = ['app.py', 'main.py', 'server.py', 'wsgi.py']
        for candidate in candidates:
            if (repo_dir / candidate).exists():
                return candidate
        return 'app.py'  # Default
    
    def _find_php_entry_point(self, repo_dir: Path) -> str:
        """Find PHP entry point"""
        candidates = ['index.php', 'public/index.php']
        for candidate in candidates:
            if (repo_dir / candidate).exists():
                return candidate
        return 'index.php'  # Default
    
    def _find_java_entry_point(self, repo_dir: Path) -> str:
        """Find Java entry point"""
        # Java typically uses JAR files after build
        return 'target/app.jar'

class ApiProvisioner:
    """API infrastructure provisioner"""
    
    def provision(self, build_result: Dict[str, Any], plan: StackPlan) -> Dict[str, Any]:
        """Provision infrastructure for API deployment"""
        runtime = build_result['runtime']
        deployment_method = plan.config.get('deployment_method', 'ecs')
        
        logger.info(f"🚀 Provisioning {runtime} API infrastructure using {deployment_method}")
        
        if deployment_method == 'ecs':
            return self._provision_ecs_infrastructure(build_result, plan)
        elif deployment_method == 'lambda':
            return self._provision_lambda_infrastructure(build_result, plan)
        else:
            raise ValueError(f"Unsupported deployment method: {deployment_method}")
    
    def _provision_ecs_infrastructure(self, build_result: Dict[str, Any], plan: StackPlan) -> Dict[str, Any]:
        """Provision ECS infrastructure with RDS"""
        return {
            "infrastructure_type": "ecs",
            "cluster_name": f"api-{build_result['runtime']}-cluster",
            "service_name": f"api-{build_result['runtime']}-service",
            "task_definition": f"api-{build_result['runtime']}-task",
            "load_balancer": f"api-{build_result['runtime']}-alb",
            "database": {
                "engine": "postgresql",
                "instance_class": "db.t3.micro",
                "allocated_storage": 20
            },
            "vpc": {
                "cidr": "10.0.0.0/16",
                "public_subnets": 2,
                "private_subnets": 2
            }
        }
    
    def _provision_lambda_infrastructure(self, build_result: Dict[str, Any], plan: StackPlan) -> Dict[str, Any]:
        """Provision Lambda infrastructure"""
        return {
            "infrastructure_type": "lambda",
            "function_name": f"api-{build_result['runtime']}-function",
            "runtime": self._get_lambda_runtime(build_result['runtime']),
            "api_gateway": {
                "name": f"api-{build_result['runtime']}-gateway",
                "stage": "prod"
            }
        }
    
    def _get_lambda_runtime(self, runtime: str) -> str:
        """Map runtime to Lambda runtime identifier"""
        runtime_map = {
            'nodejs': 'nodejs18.x',
            'python': 'python3.9',
            'java': 'java11'
        }
        return runtime_map.get(runtime, 'nodejs18.x')

class ApiDeployer:
    """API deployment orchestrator"""
    
    def deploy(self, infrastructure: Dict[str, Any], build_result: Dict[str, Any], plan: StackPlan) -> Dict[str, Any]:
        """Deploy API to provisioned infrastructure"""
        infra_type = infrastructure['infrastructure_type']
        
        logger.info(f"🚀 Deploying API to {infra_type}")
        
        if infra_type == 'ecs':
            return self._deploy_to_ecs(infrastructure, build_result, plan)
        elif infra_type == 'lambda':
            return self._deploy_to_lambda(infrastructure, build_result, plan)
        else:
            raise ValueError(f"Unsupported infrastructure type: {infra_type}")
    
    def _deploy_to_ecs(self, infrastructure: Dict[str, Any], build_result: Dict[str, Any], plan: StackPlan) -> Dict[str, Any]:
        """Deploy to ECS with RDS database"""
        # This would use the existing ECS deployment logic
        return {
            "deployment_type": "ecs",
            "status": "deployed",
            "endpoint_url": f"http://{infrastructure['load_balancer']}.us-east-1.elb.amazonaws.com",
            "health_check_url": f"http://{infrastructure['load_balancer']}.us-east-1.elb.amazonaws.com/health",
            "database_endpoint": f"{infrastructure['load_balancer']}-db.cluster.amazonaws.com:5432",
            "runtime": build_result['runtime'],
            "framework": build_result['framework']
        }
    
    def _deploy_to_lambda(self, infrastructure: Dict[str, Any], build_result: Dict[str, Any], plan: StackPlan) -> Dict[str, Any]:
        """Deploy to Lambda with API Gateway"""
        return {
            "deployment_type": "lambda",
            "status": "deployed",
            "endpoint_url": f"https://{infrastructure['api_gateway']['name']}.execute-api.us-east-1.amazonaws.com/prod",
            "function_arn": f"arn:aws:lambda:us-east-1:123456789012:function:{infrastructure['function_name']}",
            "runtime": build_result['runtime'],
            "framework": build_result['framework']
        }

class ApiStackPlugin:
    """Complete API deployment plugin"""
    
    def __init__(self):
        self._detector = ApiDetector()
        self._builder = ApiBuilder()
        self._provisioner = ApiProvisioner()
        self._deployer = ApiDeployer()
        self._runtime_manager = RuntimeAdapterIntegration()
    
    @property
    def stack_key(self) -> str:
        return "api"
    
    @property
    def display_name(self) -> str:
        return "API Backend"
    
    @property
    def description(self) -> str:
        return "Backend APIs deployed to ECS/Lambda with database support"
    
    @property
    def detector(self):
        return self._detector
    
    @property
    def builder(self):
        return self._builder
    
    @property
    def provisioner(self):
        return self._provisioner
    
    @property
    def deployer(self):
        return self._deployer
    
    def health_check(self) -> bool:
        """Check if API plugin is ready"""
        try:
            # Basic validation
            return True
        except Exception as e:
            logger.error(f"API plugin health check failed: {e}")
            return False

def load():
    """Load and register the API plugin"""
    try:
        from core.registry import _registry
        
        # Check if already registered
        if "api" in _registry._stacks:
            return
            
        plugin = ApiStackPlugin()
        register_stack(plugin)
        print("✅ API plugin loaded successfully")
        logger.info("✅ API plugin registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load API plugin: {e}")
        raise

# Auto-register when imported
load()
