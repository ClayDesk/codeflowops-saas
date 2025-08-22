"""
Static site detector - identifies HTML/CSS/JS static websites
"""
from pathlib import Path
from typing import Optional
from core.models import StackPlan
from core.utils import find_files, check_file_exists

class StaticSiteDetector:
    """Detects static HTML/CSS/JS websites"""
    
    def detect(self, repo_dir: Path) -> Optional[StackPlan]:
        """
        Detect if repository contains a static website
        
        Looks for:
        - index.html file
        - HTML files in root
        - No package.json (to avoid conflicts with React/Vue)
        - Not a Python project (avoid conflicts with Python apps)
        """
        # First check: Don't claim Python projects
        if self._is_python_project(repo_dir):
            return None
            
        # Primary indicator: index.html in root
        if check_file_exists(repo_dir, "index.html"):
            return StackPlan(
                stack_key="static",
                build_cmds=[],  # No build needed for static sites
                output_dir=repo_dir,
                config={
                    "entry_point": "index.html",
                    "type": "static_html"
                }
            )
        
        # Secondary: HTML files present but no Node.js project
        html_files = find_files(repo_dir, ["*.html"])
        package_json = check_file_exists(repo_dir, "package.json")
        
        if html_files and not package_json:
            # Don't claim Python projects even if they have HTML files
            if self._is_python_project(repo_dir):
                return None
                
            # Use first HTML file as entry point
            entry_point = html_files[0].name
            return StackPlan(
                stack_key="static",
                build_cmds=[],
                output_dir=repo_dir,
                config={
                    "entry_point": entry_point,
                    "type": "static_html",
                    "html_files": [f.name for f in html_files[:5]]  # List first 5
                }
            )
        
        # No static site detected
        return None
    
    def _is_python_project(self, repo_dir: Path) -> bool:
        """Check if this is primarily a Python project that shouldn't be static"""
        
        # Count Python files
        python_files = list(repo_dir.rglob('*.py'))
        total_files = list(repo_dir.rglob('*'))
        total_files = [f for f in total_files if f.is_file() and not any(part.startswith('.git') for part in f.parts)]
        
        if not total_files:
            return False
            
        python_ratio = len(python_files) / len(total_files)
        
        # If >30% Python files, or >5 Python files, it's likely a Python project
        if python_ratio > 0.3 or len(python_files) > 5:
            return True
            
        # Check for Python project indicators
        python_indicators = [
            'requirements.txt', 'setup.py', 'pyproject.toml', 
            'Pipfile', 'environment.yml', 'main.py', 'app.py'
        ]
        
        for indicator in python_indicators:
            if check_file_exists(repo_dir, indicator):
                return True
                
        return False
    
    def get_priority(self) -> int:
        """Static sites should run before PHP fallback to catch pure HTML sites"""
        return 35  # Higher priority than PHP (30) - check before PHP fallback
