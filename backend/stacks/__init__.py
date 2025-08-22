"""
Stack plugins for different deployment targets
"""

def load_all_plugins():
    """Load all available stack plugins"""
    try:
        # Load special purpose plugins first
        from . import non_deployable
        
        # Load frontend plugins
        from . import react
        from . import nextjs
        from . import static_site
        
        # Load backend plugins
        from .api import plugin as api_plugin
        from . import python
        
        print("✅ All stack plugins loaded")
    except Exception as e:
        print(f"❌ Error loading plugins: {e}")

# Auto-load plugins when imported
load_all_plugins()
