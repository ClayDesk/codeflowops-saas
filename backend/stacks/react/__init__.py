"""
React stack package init
"""
from .plugin import load

# Ensure React stack is registered when package is imported
load()
