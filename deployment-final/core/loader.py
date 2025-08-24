"""
Plugin auto-loader - automatically discovers and loads stack plugins
"""
import os
import sys
import importlib
import logging
from pathlib import Path
from typing import List, Dict, Any
from core.registry import _registry

logger = logging.getLogger(__name__)

class PluginLoader:
    """Automatically discovers and loads stack plugins"""
    
    def __init__(self, stacks_dir: Path = None):
        self.stacks_dir = stacks_dir or Path(__file__).parent.parent / "stacks"
        self.loaded_plugins: Dict[str, Any] = {}
        
    def discover_plugins(self) -> List[str]:
        """
        Discover all available plugin directories in stacks/
        """
        plugin_dirs = []
        
        if not self.stacks_dir.exists():
            logger.warning(f"Stacks directory not found: {self.stacks_dir}")
            return plugin_dirs
            
        logger.info(f"🔍 Scanning for plugins in: {self.stacks_dir}")
        
        for item in self.stacks_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # Check if it has a plugin.py file
                plugin_file = item / "plugin.py"
                init_file = item / "__init__.py"
                
                if plugin_file.exists():
                    plugin_dirs.append(item.name)
                    logger.info(f"  📦 Found plugin: {item.name}")
                elif init_file.exists():
                    plugin_dirs.append(item.name)
                    logger.info(f"  📦 Found plugin package: {item.name}")
                else:
                    logger.debug(f"  ⚠️ Skipping directory without plugin files: {item.name}")
                    
        return plugin_dirs
    
    def load_plugin(self, plugin_name: str) -> bool:
        """
        Load a specific plugin by name
        """
        try:
            # Check if already loaded
            if plugin_name in self.loaded_plugins:
                logger.debug(f"Plugin '{plugin_name}' already loaded")
                return True
                
            logger.info(f"📥 Loading plugin: {plugin_name}")
            
            # Import the plugin package
            module_path = f"stacks.{plugin_name}"
            
            # Try to import the plugin package
            plugin_module = importlib.import_module(module_path)
            
            # Mark as loaded
            self.loaded_plugins[plugin_name] = plugin_module
            
            logger.info(f"✅ Successfully loaded plugin: {plugin_name}")
            return True
            
        except ImportError as e:
            logger.error(f"❌ Failed to import plugin '{plugin_name}': {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error loading plugin '{plugin_name}': {e}")
            return False
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """
        Discover and load all available plugins
        """
        logger.info("🚀 Starting plugin auto-loader...")
        
        # Discover available plugins
        plugin_names = self.discover_plugins()
        
        if not plugin_names:
            logger.warning("⚠️ No plugins found")
            return {}
            
        # Load each plugin
        results = {}
        for plugin_name in plugin_names:
            results[plugin_name] = self.load_plugin(plugin_name)
            
        # Summary
        loaded_count = sum(results.values())
        total_count = len(results)
        
        logger.info(f"📊 Plugin loading complete: {loaded_count}/{total_count} plugins loaded")
        
        if loaded_count > 0:
            logger.info(f"✅ Loaded plugins: {[name for name, success in results.items() if success]}")
            
        if loaded_count < total_count:
            failed = [name for name, success in results.items() if not success]
            logger.warning(f"❌ Failed plugins: {failed}")
            
        return results
    
    def get_loaded_plugins(self) -> List[str]:
        """Get list of successfully loaded plugin names"""
        return list(self.loaded_plugins.keys())
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get current registry status after loading"""
        return {
            "loaded_plugins": self.get_loaded_plugins(),
            "registered_stacks": list(_registry._stacks.keys()),
            "total_detectors": len(_registry._detectors),
            "registry_health": _registry.health_check() if hasattr(_registry, 'health_check') else "unknown"
        }
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a specific plugin (useful for development)
        """
        try:
            if plugin_name in self.loaded_plugins:
                module_path = f"stacks.{plugin_name}"
                importlib.reload(sys.modules[module_path])
                logger.info(f"🔄 Reloaded plugin: {plugin_name}")
                return True
            else:
                logger.warning(f"Plugin '{plugin_name}' not currently loaded")
                return self.load_plugin(plugin_name)
                
        except Exception as e:
            logger.error(f"❌ Failed to reload plugin '{plugin_name}': {e}")
            return False

# Global plugin loader instance
_loader = PluginLoader()

def auto_load_plugins() -> Dict[str, bool]:
    """Auto-load all available plugins using global loader"""
    return _loader.load_all_plugins()

def get_plugin_status() -> Dict[str, Any]:
    """Get current plugin and registry status"""
    return _loader.get_registry_status()

def reload_plugin(plugin_name: str) -> bool:
    """Reload a specific plugin"""
    return _loader.reload_plugin(plugin_name)

def force_reload_all() -> Dict[str, bool]:
    """Force reload all plugins (clears cache first)"""
    _loader.loaded_plugins.clear()
    return _loader.load_all_plugins()
