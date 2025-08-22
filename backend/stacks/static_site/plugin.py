"""
Static site plugin - registers the complete static site stack
"""
import logging
from core.interfaces import StackPlugin
from core.registry import register_stack
from .detector import StaticSiteDetector
from .builder import StaticSiteBuilder
from .provisioner import StaticSiteProvisioner
from .deployer import StaticSiteDeployer

logger = logging.getLogger(__name__)

class StaticSitePlugin:
    """Complete static site deployment plugin"""
    
    def __init__(self):
        self._detector = StaticSiteDetector()
        self._builder = StaticSiteBuilder()
        self._provisioner = StaticSiteProvisioner()
        self._deployer = StaticSiteDeployer()
    
    @property
    def stack_key(self) -> str:
        return "static"
    
    @property
    def display_name(self) -> str:
        return "Static Website"
    
    @property
    def description(self) -> str:
        return "HTML, CSS, JavaScript static websites hosted on S3"
    
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
        """Check if static site plugin is ready"""
        try:
            # Basic validation - could check AWS CLI availability, etc.
            return True
        except Exception as e:
            logger.error(f"Static site plugin health check failed: {e}")
            return False

def load():
    """Load and register the static site plugin"""
    try:
        from core.registry import _registry
        
        # Check if already registered
        if "static" in _registry._stacks:
            return
            
        plugin = StaticSitePlugin()
        register_stack(plugin)
        print("✅ Static site plugin loaded successfully")
        logger.info("✅ Static site plugin registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to load static site plugin: {e}")
        raise

# Auto-register when imported
load()
