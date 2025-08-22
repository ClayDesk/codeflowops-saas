# Phase 2: Runtime Adapter Architecture
# backend/stacks/api/adapters/__init__.py

"""
Runtime adapter architecture for standardized API deployments
Provides consistent interface across Node.js, Python, PHP, and Java runtimes
"""

from .base_adapter import RuntimeAdapter, BuildResult, DeploymentResult
from .nodejs_adapter import NodeJSAdapter  
from .python_adapter import PythonAdapter
from .php_adapter import PHPAdapter
from .java_adapter import JavaAdapter

__all__ = [
    'RuntimeAdapter',
    'BuildResult', 
    'DeploymentResult',
    'NodeJSAdapter',
    'PythonAdapter',
    'PHPAdapter',
    'JavaAdapter'
]
