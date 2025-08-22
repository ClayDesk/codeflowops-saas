# Phase 2: Runtime Adapter Integration
# backend/stacks/api/runtime_integration.py

"""
Integration layer connecting runtime adapters with existing API plugins
✅ Backward compatibility with existing Phase 2 plugins
✅ Comprehensive plan adapter architecture integration
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .adapters import (
    RuntimeAdapter, NodeJSAdapter, PythonAdapter, 
    PHPAdapter, JavaAdapter, DeploymentResult
)
from .base_api_plugin import ApiDeploymentConfig, ApiDeploymentResult, DeploymentMethod

logger = logging.getLogger(__name__)

class RuntimeAdapterIntegration:
    """
    Integration layer for runtime adapters with existing API plugin architecture
    ✅ Bridges comprehensive plan adapter architecture with Phase 2 plugins
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.adapters = {
            'nodejs': NodeJSAdapter(region),
            'python': PythonAdapter(region),
            'php': PHPAdapter(region),
            'java': JavaAdapter(region)
        }
    
    def detect_runtime_and_framework(self, repo_path: str) -> Dict[str, Any]:
        """
        Detect runtime and framework using adapter architecture
        ✅ Comprehensive runtime detection per comprehensive plan
        """
        
        repo_path_obj = Path(repo_path)
        
        # Check for Node.js
        if (repo_path_obj / 'package.json').exists():
            framework_config = self.adapters['nodejs'].detect_framework(repo_path)
            return {
                'runtime': 'nodejs',
                'framework': framework_config['framework'],
                'port': framework_config['port'],
                'health_check_path': framework_config['health_check_path'],
                'adapter_config': framework_config
            }
        
        # Check for Python
        elif any((repo_path_obj / f).exists() for f in ['requirements.txt', 'setup.py', 'pyproject.toml']):
            framework_config = self.adapters['python'].detect_framework(repo_path)
            return {
                'runtime': 'python',
                'framework': framework_config['framework'],
                'port': framework_config['port'],
                'health_check_path': framework_config['health_check_path'],
                'adapter_config': framework_config
            }
        
        # Check for PHP
        elif (repo_path_obj / 'composer.json').exists():
            framework_config = self.adapters['php'].detect_framework(repo_path)
            return {
                'runtime': 'php',
                'framework': framework_config['framework'],
                'port': framework_config['port'],
                'health_check_path': framework_config['health_check_path'],
                'adapter_config': framework_config
            }
        
        # Check for Java
        elif any((repo_path_obj / f).exists() for f in ['pom.xml', 'build.gradle']):
            framework_config = self.adapters['java'].detect_framework(repo_path)
            return {
                'runtime': 'java',
                'framework': framework_config['framework'],
                'port': framework_config['port'],
                'health_check_path': framework_config['health_check_path'],
                'adapter_config': framework_config
            }
        
        else:
            return {
                'runtime': 'unknown',
                'framework': 'unknown',
                'port': 8000,
                'health_check_path': '/health',
                'adapter_config': {}
            }
    
    def deploy_with_adapter(self, 
                          repo_path: str, 
                          deployment_config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """
        Deploy using runtime adapter architecture
        ✅ Standardized deployment per comprehensive plan
        """
        
        # Detect runtime and framework
        runtime_info = self.detect_runtime_and_framework(repo_path)
        runtime = runtime_info['runtime']
        
        if runtime == 'unknown':
            raise ValueError(f"Unable to detect runtime for repository: {repo_path}")
        
        # Get appropriate adapter
        adapter = self.adapters[runtime]
        
        # Build application
        build_config = {
            'framework': runtime_info['framework'],
            'environment_vars': deployment_config.environment_variables or {}
        }
        
        build_result = adapter.build(repo_path, build_config)
        
        if not build_result.success:
            return ApiDeploymentResult(
                app_name=deployment_config.app_name,
                deployment_method=deployment_config.deployment_method,
                endpoint_url="",
                status="failed",
                health_check_url=""
            )
        
        # Deploy using adapter
        adapter_deployment_config = {
            'target': deployment_config.deployment_method.value,
            'function_name': deployment_config.app_name,
            'service_name': deployment_config.app_name,
            'lambda': {
                'function_name': deployment_config.app_name,
                'memory_size': deployment_config.memory_size,
                'timeout': deployment_config.timeout
            },
            'ecs': {
                'service_name': deployment_config.app_name,
                'auto_scaling': deployment_config.auto_scaling
            }
        }
        
        deployment_result = adapter.deploy(build_result, adapter_deployment_config)
        
        # Convert adapter result to API plugin result for backward compatibility
        return self._convert_adapter_result_to_api_result(deployment_result, deployment_config)
    
    def _convert_adapter_result_to_api_result(self, 
                                            adapter_result: DeploymentResult, 
                                            config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """
        Convert adapter deployment result to API plugin result format
        ✅ Backward compatibility with existing API plugin architecture
        """
        
        status = "deployed" if adapter_result.success else "failed"
        
        return ApiDeploymentResult(
            app_name=config.app_name,
            deployment_method=config.deployment_method,
            endpoint_url=adapter_result.endpoint_url,
            function_arn=adapter_result.function_arn,
            service_arn=adapter_result.service_arn,
            load_balancer_arn=adapter_result.load_balancer_arn,
            health_check_url=adapter_result.health_check_url,
            deployment_id=adapter_result.deployment_id,
            status=status
        )
    
    def get_standardized_ports(self) -> Dict[str, int]:
        """
        Get standardized ports for all runtimes
        ✅ Port standardization per comprehensive plan
        """
        return {
            'nodejs': self.adapters['nodejs'].DEFAULT_PORT,
            'python': self.adapters['python'].DEFAULT_PORT,
            'php': self.adapters['php'].DEFAULT_PORT,
            'java': self.adapters['java'].DEFAULT_PORT
        }
    
    def get_health_check_paths(self) -> Dict[str, str]:
        """
        Get standardized health check paths for all runtimes
        ✅ Health check standardization per comprehensive plan
        """
        return {
            'nodejs': self.adapters['nodejs'].HEALTH_CHECK_PATH,
            'python': self.adapters['python'].HEALTH_CHECK_PATH,
            'php': self.adapters['php'].HEALTH_CHECK_PATH,
            'java': self.adapters['java'].HEALTH_CHECK_PATH
        }

class EnhancedApiPlugin:
    """
    Enhanced API plugin that uses runtime adapters while maintaining backward compatibility
    ✅ Integration of comprehensive plan adapter architecture with existing plugins
    """
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.adapter_integration = RuntimeAdapterIntegration(region)
        
        # Import existing plugins for fallback
        try:
            from .nodejs_api_plugin import NodeJSApiPlugin
            from .python_api_plugin import PythonApiPlugin
            from .php_api_plugin import PHPApiPlugin
            from .java_api_plugin import JavaApiPlugin
            
            self.legacy_plugins = {
                'nodejs': NodeJSApiPlugin(region),
                'python': PythonApiPlugin(region),
                'php': PHPApiPlugin(region),
                'java': JavaApiPlugin(region)
            }
        except ImportError:
            logger.warning("Legacy API plugins not found, using adapter-only mode")
            self.legacy_plugins = {}
    
    def deploy_api(self, repo_path: str, config: ApiDeploymentConfig, use_adapters: bool = True) -> ApiDeploymentResult:
        """
        Deploy API using either new adapter architecture or legacy plugins
        ✅ Flexible deployment with backward compatibility
        """
        
        if use_adapters:
            logger.info("🚀 Using new runtime adapter architecture for deployment")
            return self.adapter_integration.deploy_with_adapter(repo_path, config)
        
        else:
            logger.info("🔄 Using legacy plugin architecture for deployment")
            return self._deploy_with_legacy_plugins(repo_path, config)
    
    def _deploy_with_legacy_plugins(self, repo_path: str, config: ApiDeploymentConfig) -> ApiDeploymentResult:
        """Deploy using legacy plugin architecture for backward compatibility"""
        
        # Detect runtime
        runtime_info = self.adapter_integration.detect_runtime_and_framework(repo_path)
        runtime = runtime_info['runtime']
        
        if runtime in self.legacy_plugins:
            legacy_plugin = self.legacy_plugins[runtime]
            return legacy_plugin.deploy_api(repo_path, config)
        else:
            raise ValueError(f"No legacy plugin available for runtime: {runtime}")
    
    def get_deployment_info(self, repo_path: str) -> Dict[str, Any]:
        """
        Get comprehensive deployment information using adapter detection
        ✅ Enhanced runtime detection per comprehensive plan
        """
        
        runtime_info = self.adapter_integration.detect_runtime_and_framework(repo_path)
        
        return {
            'runtime': runtime_info['runtime'],
            'framework': runtime_info['framework'],
            'recommended_port': runtime_info['port'],
            'health_check_path': runtime_info['health_check_path'],
            'supports_lambda': runtime_info['runtime'] != 'php',  # PHP doesn't support Lambda directly
            'supports_ecs': True,
            'adapter_config': runtime_info['adapter_config'],
            'standardized_ports': self.adapter_integration.get_standardized_ports(),
            'health_check_paths': self.adapter_integration.get_health_check_paths()
        }
