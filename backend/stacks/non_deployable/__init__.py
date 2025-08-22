"""
Non-Deployable Repository Stack
Handles repositories that are tools, libraries, or not meant for web deployment
"""

# Import the plugin to auto-register it
from .plugin import NonDeployablePlugin

__all__ = ['NonDeployablePlugin']
