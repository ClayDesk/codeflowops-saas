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
                    # Ensure repository URL is in config if context provided
                    if context and 'repo_url' in context and 'repository_url' not in plan.config:
                        plan.config['repository_url'] = context['repo_url']
                    return plan
            except Exception as e:
                logger.warning(f"Detector {stack_key} failed: {e}")
                continue
                
        logger.warning(f"❌ No stack detected for repository: {repo_dir}")
        return None
        
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
