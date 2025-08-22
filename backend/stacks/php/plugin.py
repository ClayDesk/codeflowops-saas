"""
Complete PHP Stack Plugin
"""
import logging
from pathlib import Path
from typing import Optional
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from core.interfaces import StackPlugin, StackDetector, StackBuilder, StackProvisioner, StackDeployer
from core.registry import register_stack
from .detector import PHPDetector
from .builder import PHPBuilder
from .provisioner import PHPProvisioner
from .deployer import PHPDeployer

logger = logging.getLogger(__name__)

class PHPStackPlugin:
    """Complete PHP stack plugin implementing all required interfaces"""
    
    def __init__(self):
        self._detector = PHPDetector()
        self._builder = PHPBuilder()
        self._provisioner = PHPProvisioner()
        self._deployer = PHPDeployer()
    
    @property
    def stack_key(self) -> str:
        """Unique identifier for this stack"""
        return "php"
    
    @property
    def display_name(self) -> str:
        """Human-readable name for this stack"""
        return "PHP API Applications"
    
    @property
    def description(self) -> str:
        """Description of what this stack handles"""
        return "Deploys PHP API applications including Laravel, Symfony, and vanilla PHP APIs to AWS using containerized deployments with ECS Fargate, Application Load Balancer, and CloudFront CDN"
    
    @property
    def detector(self) -> StackDetector:
        """Stack detector instance"""
        return self._detector
    
    @property
    def builder(self) -> StackBuilder:
        """Stack builder instance"""
        return self._builder
    
    @property
    def provisioner(self) -> StackProvisioner:
        """Stack provisioner instance"""
        return self._provisioner
    
    @property
    def deployer(self) -> StackDeployer:
        """Stack deployer instance"""
        return self._deployer
    
    def health_check(self) -> bool:
        """Check if this plugin is healthy and ready to use"""
        try:
            # Check if all components are properly initialized
            if not self._detector:
                logger.error("PHP detector not initialized")
                return False
                
            if not self._builder:
                logger.error("PHP builder not initialized") 
                return False
                
            if not self._provisioner:
                logger.error("PHP provisioner not initialized")
                return False
                
            if not self._deployer:
                logger.error("PHP deployer not initialized")
                return False
            
            # Test detector functionality
            try:
                # Create a minimal test to verify detector works
                test_result = hasattr(self._detector, 'detect') and callable(getattr(self._detector, 'detect'))
                if not test_result:
                    logger.error("PHP detector missing detect method")
                    return False
            except Exception as e:
                logger.error(f"PHP detector health check failed: {e}")
                return False
            
            logger.info("✅ PHP stack plugin health check passed")
            return True
            
        except Exception as e:
            logger.error(f"PHP stack plugin health check failed: {e}")
            return False

def load():
    """Load and register the PHP stack plugin"""
    try:
        from core.registry import _registry
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Always try to register (handle duplicate registration gracefully)
        try:
            plugin = PHPStackPlugin()
            _registry.register_stack(plugin)
            print("✅ PHP plugin loaded successfully")
            logger.info("✅ PHP plugin registered successfully")
        except ValueError as e:
            if "already registered" in str(e):
                logger.info("✅ PHP plugin already registered")
            else:
                raise
                
    except Exception as e:
        print(f"❌ Failed to load PHP plugin: {e}")
        logger.error(f"Failed to load PHP plugin: {e}")
        raise

# Create plugin instance
php_plugin = PHPStackPlugin()

# Auto-load the plugin when this module is imported
if __name__ != "__main__":
    load()
