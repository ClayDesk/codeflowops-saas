"""
Static site stack components
"""
from .plugin import load

# Ensure static site stack is registered when package is imported
load()
