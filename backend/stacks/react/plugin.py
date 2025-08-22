"""
React stack plugin registration
"""
from core.interfaces import StackDetector, StackBuilder, StackProvisioner, StackDeployer, StackPlugin
from core.registry import register_stack
from .detector import ReactDetector
from .builder import ReactBuilder  
from .proper_provisioner import ReactProvisioner
from .deployer import ReactDeployer

class ReactStackPlugin:
    """Complete React stack plugin implementation"""
    
    def __init__(self):
        self._detector = ReactDetector()
        self._builder = ReactBuilder()
        self._provisioner = ReactProvisioner()
        self._deployer = ReactDeployer()
    
    @property
    def stack_key(self) -> str:
        return "react"
    
    @property
    def display_name(self) -> str:
        return "React SPA"
    
    @property
    def description(self) -> str:
        return "React Single Page Applications with npm build process"
    
    @property
    def detector(self) -> StackDetector:
        return self._detector
    
    @property
    def builder(self) -> StackBuilder:
        return self._builder
    
    @property
    def provisioner(self) -> StackProvisioner:
        return self._provisioner
    
    @property
    def deployer(self) -> StackDeployer:
        return self._deployer
    
    def health_check(self) -> bool:
        """Check if React plugin is healthy"""
        try:
            # Basic component check
            return all([
                self._detector is not None,
                self._builder is not None,
                self._provisioner is not None,
                self._deployer is not None
            ])
        except Exception:
            return False

def load():
    """Load and register the React stack plugin"""
    try:
        from core.registry import _registry
        
        # Check if already registered
        if "react" in _registry._stacks:
            return
            
        plugin = ReactStackPlugin()
        register_stack(plugin)
        print("✅ React plugin loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load React plugin: {e}")
        raise

# Auto-register when imported
load()
