# Phase 2: Base API Plugin
# backend/stacks/api/__init__.py

"""
API plugin system for Phase 2 implementation
Supports Node.js, Python, PHP, and Java API deployments
"""

from .base_api_plugin import BaseApiPlugin
from .nodejs_api_plugin import NodeJSApiPlugin
from .python_api_plugin import PythonApiPlugin
from .php_api_plugin import PHPApiPlugin
from .java_api_plugin import JavaApiPlugin

__all__ = [
    'BaseApiPlugin',
    'NodeJSApiPlugin',
    'PythonApiPlugin', 
    'PHPApiPlugin',
    'JavaApiPlugin'
]
