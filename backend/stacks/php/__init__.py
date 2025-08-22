"""
PHP Stack Plugin Package

Supports deployment of PHP applications including:
- Laravel applications
- Symfony applications  
- Vanilla PHP projects

Uses containerized deployments with Docker, ECS Fargate, ALB, and CloudFront.
"""

from .plugin import PHPStackPlugin, php_plugin, load

# Auto-load the plugin when the package is imported
try:
    load()
except Exception as e:
    import logging
    logging.getLogger(__name__).error(f"Failed to auto-load PHP plugin: {e}")

__all__ = ['PHPStackPlugin', 'php_plugin', 'load']