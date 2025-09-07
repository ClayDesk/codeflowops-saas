"""
Stack registry and plugin management
"""
from typing import Dict, List, Optional, Type
from .interfaces import StackPlugin, StackDetector, StackBuilder, StackProvisioner, StackDeployer
from .models import StackPlan
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StackComponents:
    """Container for all components of a stack"""
    
    def __init__(self, plugin: StackPlugin):
        self.plugin = plugin
        self.detector = plugin.detector
        self.builder = plugin.builder
        self.provisioner = plugin.provisioner
        self.deployer = plugin.deployer
        
    @property
    def stack_key(self) -> str:
        return self.plugin.stack_key
        
    @property
    def display_name(self) -> str:
        return self.plugin.display_name

class StackRegistry:
    """Central registry for all stack plugins"""
    
    def __init__(self):
        self._stacks: Dict[str, StackComponents] = {}
        self._detectors: List[tuple[int, str, StackDetector]] = []  # (priority, key, detector)
        
    def register_stack(self, plugin: StackPlugin) -> None:
        """Register a complete stack plugin"""
        if plugin.stack_key in self._stacks:
            raise ValueError(f"Stack '{plugin.stack_key}' already registered")
            
        # Validate plugin health
        try:
            if not plugin.health_check():
                logger.warning(f"Stack plugin '{plugin.stack_key}' failed health check")
        except Exception as e:
            logger.error(f"Health check failed for '{plugin.stack_key}': {e}")
            
        components = StackComponents(plugin)
        self._stacks[plugin.stack_key] = components
        
        # Add detector to ordered list
        priority = plugin.detector.get_priority()
        self._detectors.append((priority, plugin.stack_key, plugin.detector))
        self._detectors.sort(key=lambda x: x[0], reverse=True)  # Higher priority first
        
        logger.info(f"✅ Registered stack plugin: {plugin.stack_key} ({plugin.display_name})")
        
    def get_stack(self, stack_key: str) -> Optional[StackComponents]:
        """Get stack components by key"""
        return self._stacks.get(stack_key)
        
    def detect_stack(self, repo_dir: Path, context: Optional[dict] = None) -> Optional[StackPlan]:
        """
        Run detectors in priority order to identify the best stack for a repository
        """
        logger.info(f"🔍 Detecting stack for repository: {repo_dir}")
        
        for priority, stack_key, detector in self._detectors:
            try:
                logger.debug(f"Trying detector: {stack_key} (priority: {priority})")
                
                # Check if detector supports context parameter
                import inspect
                detector_params = inspect.signature(detector.detect).parameters
                if 'context' in detector_params:
                    plan = detector.detect(repo_dir, context)
                else:
                    plan = detector.detect(repo_dir)
                    
                if plan:
                    logger.info(f"✅ Detected stack: {stack_key}")
                    
                    # 🚫 INTERCEPT PHP/LARAVEL/VUE DETECTIONS - Mark as non-deployable
                    if self._is_php_laravel_vue_stack(plan, context):
                        logger.info(f"🚫 Intercepted {stack_key} detection - redirecting to non-deployable")
                        return self._create_non_deployable_plan(plan, context, repo_dir)
                    
                    # Ensure repository URL is in config if context provided
                    if context and 'repo_url' in context and 'repository_url' not in plan.config:
                        plan.config['repository_url'] = context['repo_url']
                    return plan
            except Exception as e:
                logger.warning(f"Detector {stack_key} failed: {e}")
                continue
                
        logger.warning(f"❌ No stack detected for repository: {repo_dir}")
        return None
        
    def _is_php_laravel_vue_stack(self, plan: StackPlan, context: Optional[dict] = None) -> bool:
        """Check if the detected stack is PHP/Laravel/Vue that should be marked as non-deployable"""
        
        # Check stack key
        if plan.stack_key in ['php', 'api', 'php_api']:
            return True
            
        # Check context for framework information
        if context:
            detected_framework = None
            
            # Check direct context
            if isinstance(context, dict):
                detected_framework = context.get('detected_framework')
                
                # Check analysis section
                if not detected_framework and 'analysis' in context:
                    analysis = context['analysis']
                    if isinstance(analysis, dict):
                        detected_framework = analysis.get('detected_framework')
                        
            # Check for PHP/Laravel/Vue frameworks
            if detected_framework:
                php_laravel_vue_frameworks = [
                    'laravel', 'php', 'vue', 'vue.js', 'nuxt', 'nuxt.js',
                    'laravel-web', 'laravel-api', 'php-laravel', 'laravel-blade'
                ]
                
                framework_lower = str(detected_framework).lower()
                if any(framework in framework_lower for framework in php_laravel_vue_frameworks):
                    return True
                    
        # Check plan config for framework information
        if hasattr(plan, 'config') and plan.config:
            framework = plan.config.get('framework', '').lower()
            detected_framework = plan.config.get('detected_framework', '').lower()
            runtime = plan.config.get('runtime', '').lower()
            
            if any(fw in framework or fw in detected_framework or fw in runtime for fw in ['laravel', 'php', 'vue']):
                return True
                
        return False
        
    def _create_non_deployable_plan(self, original_plan: StackPlan, context: Optional[dict] = None, repo_dir: Path = None) -> StackPlan:
        """Create a non-deployable plan with professional messaging for PHP/Laravel/Vue apps"""
        
        # Determine the specific framework for messaging
        framework = "PHP/Laravel/Vue"
        if context and isinstance(context, dict):
            detected = context.get('detected_framework') or context.get('framework')
            if detected:
                framework = str(detected).title()
                
        # Create professional non-deployable configuration
        non_deployable_config = {
            "type": "web_framework_not_supported",
            "tool_name": f"{framework} Web Application",
            "language": "PHP/JavaScript",
            "deployable": False,
            "reason": "Framework Not Currently Supported",
            "explanation": f"This repository contains a {framework} web application. CodeFlowOps currently specializes in deploying specific web application stacks. While {framework} is a popular framework, it's not currently supported in our deployment pipeline.",
            "usage_instructions": [
                f"Deploy {framework} applications manually using your preferred hosting provider",
                f"Consider using platform-specific deployment tools for {framework}",
                "Check back later as we continuously add support for more frameworks",
                "Contact support if you need assistance with alternative deployment options"
            ],
            "what_to_deploy_instead": "Consider converting to a supported framework (React SPA, Static Website, or API applications) or deploy manually to your preferred hosting platform.",
            "codeflowops_message": f"CodeFlowOps currently supports React SPAs, Static Websites, and API applications. {framework} deployment is not available at this time.",
            "supported_alternatives": [
                "React Single Page Applications",
                "Static HTML/CSS/JavaScript websites", 
                "API applications (Node.js, Python, Java)"
            ],
            "original_detection": {
                "stack_key": original_plan.stack_key,
                "framework": framework
            }
        }
        
        # Return non-deployable StackPlan
        return StackPlan(
            stack_key="non_deployable",
            build_cmds=[],
            output_dir=repo_dir or Path("/tmp"),
            config=non_deployable_config
        )
        
    def list_stacks(self) -> List[str]:
        """Get list of all registered stack keys"""
        return list(self._stacks.keys())
        
    def get_stack_info(self, stack_key: str) -> Optional[dict]:
        """Get information about a specific stack"""
        components = self._stacks.get(stack_key)
        if not components:
            return None
            
        return {
            "stack_key": stack_key,
            "display_name": components.display_name,
            "description": components.plugin.description,
            "priority": next(
                (priority for priority, key, _ in self._detectors if key == stack_key), 
                0
            )
        }
        
    def get_all_stack_info(self) -> List[dict]:
        """Get information about all registered stacks"""
        return [self.get_stack_info(key) for key in self._stacks.keys()]
    
    def health_check(self) -> bool:
        """Check registry health and all registered plugins"""
        try:
            # Basic registry checks
            if not self._stacks:
                logger.warning("No stacks registered in registry")
                return False
                
            # Check each registered plugin
            healthy_plugins = 0
            total_plugins = len(self._stacks)
            
            for stack_key, components in self._stacks.items():
                try:
                    if components.plugin.health_check():
                        healthy_plugins += 1
                    else:
                        logger.warning(f"Plugin '{stack_key}' failed health check")
                except Exception as e:
                    logger.error(f"Health check error for '{stack_key}': {e}")
                    
            # Registry is healthy if at least one plugin is healthy
            is_healthy = healthy_plugins > 0
            
            if is_healthy:
                logger.info(f"Registry health check: {healthy_plugins}/{total_plugins} plugins healthy")
            else:
                logger.error("Registry health check failed: no healthy plugins")
                
            return is_healthy
            
        except Exception as e:
            logger.error(f"Registry health check failed: {e}")
            return False

# Global registry instance
_registry = StackRegistry()

def register_stack(plugin: StackPlugin) -> None:
    """Register a stack plugin with the global registry"""
    _registry.register_stack(plugin)

def get_stack(stack_key: str) -> Optional[StackComponents]:
    """Get stack components from global registry"""
    return _registry.get_stack(stack_key)

def detect_stack(repo_dir: Path, context: Optional[dict] = None) -> Optional[StackPlan]:
    """Detect stack using global registry"""
    return _registry.detect_stack(repo_dir, context)

def list_stacks() -> List[str]:
    """List all registered stacks"""
    return _registry.list_stacks()

def get_stack_info(stack_key: str) -> Optional[dict]:
    """Get stack information"""
    return _registry.get_stack_info(stack_key)

def get_all_stack_info() -> List[dict]:
    """Get all stack information"""
    return _registry.get_all_stack_info()

def get_registry() -> StackRegistry:
    """Get the global registry instance"""
    return _registry
