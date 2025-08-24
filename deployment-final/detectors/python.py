"""
🐍 Python Framework Detector
================================================================================
Specialized detector for Python web frameworks including Django, Flask, FastAPI.
Distinguishes between web applications and Python libraries/tools.

Key Detection Patterns:
- Django: manage.py, settings.py, models.py, urls.py
- Flask: app.py, requirements.txt with Flask
- FastAPI: main.py, requirements.txt with fastapi
- Generic Python: setup.py, pyproject.toml, requirements.txt
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class PythonFrameworkDetector:
    """🎯 Specialized Python framework detection with high accuracy"""
    
    def __init__(self):
        self.confidence_threshold = 0.5
        
    def detect_python(self, repo_path: str, file_analysis: Dict[str, Any], 
                     dependencies: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        🔍 Detect Python frameworks with precise classification
        
        Priority Order:
        1. Django (web framework)
        2. Flask (micro web framework) 
        3. FastAPI (modern API framework)
        4. Generic Python (libraries/tools)
        """
        
        detections = []
        
        # Django Detection
        django_result = self._detect_django(repo_path, file_analysis, dependencies)
        if django_result:
            detections.append(django_result)
            
        # Flask Detection  
        flask_result = self._detect_flask(repo_path, file_analysis, dependencies)
        if flask_result:
            detections.append(flask_result)
            
        # FastAPI Detection
        fastapi_result = self._detect_fastapi(repo_path, file_analysis, dependencies)
        if fastapi_result:
            detections.append(fastapi_result)
            
        # Generic Python Detection (fallback)
        if not detections:
            python_result = self._detect_generic_python(repo_path, file_analysis, dependencies)
            if python_result:
                detections.append(python_result)
        
        # Sort by confidence
        detections.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        return detections
    
    def _detect_django(self, repo_path: str, file_analysis: Dict[str, Any], 
                      dependencies: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """🎯 Detect Django web framework"""
        
        evidence = []
        confidence = 0.0
        
        # Core Django files
        django_files = [
            'manage.py',
            'settings.py', 
            'urls.py',
            'models.py',
            'views.py',
            'admin.py',
            'wsgi.py',
            'asgi.py'
        ]
        
        found_files = []
        for django_file in django_files:
            if self._file_exists_anywhere(repo_path, django_file):
                found_files.append(django_file)
                
        if 'manage.py' in found_files:
            confidence += 0.5
            evidence.append('Django manage.py found')
            
        if 'settings.py' in found_files:
            confidence += 0.3
            evidence.append('Django settings.py found')
            
        if len(found_files) >= 3:
            confidence += 0.2
            evidence.append(f'Multiple Django files detected: {found_files}')
        
        # Dependencies check
        if dependencies:
            deps = dependencies.get('python', {})
            if 'django' in str(deps).lower():
                confidence += 0.3
                evidence.append('Django dependency found')
                
        # Directory structure
        if self._has_django_structure(repo_path):
            confidence += 0.2
            evidence.append('Django app structure detected')
            
        if confidence >= self.confidence_threshold:
            return {
                'framework': 'django',
                'runtime': 'python',
                'confidence': min(confidence, 0.99),
                'evidence': evidence,
                'variant': 'web-framework',
                'category': 'web-backend',
                'is_deployable': True
            }
            
        return None
    
    def _detect_flask(self, repo_path: str, file_analysis: Dict[str, Any], 
                     dependencies: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """🎯 Detect Flask web framework"""
        
        evidence = []
        confidence = 0.0
        
        # Flask entry points
        flask_files = ['app.py', 'main.py', 'run.py', '__init__.py']
        
        for flask_file in flask_files:
            if self._file_exists_anywhere(repo_path, flask_file):
                # Check if file contains Flask imports
                if self._file_contains_flask_imports(repo_path, flask_file):
                    confidence += 0.4
                    evidence.append(f'Flask imports found in {flask_file}')
                    break
                    
        # Dependencies check
        if dependencies:
            deps = dependencies.get('python', {})
            if 'flask' in str(deps).lower():
                confidence += 0.4
                evidence.append('Flask dependency found')
                
        # Templates directory (common Flask pattern)
        if self._directory_exists(repo_path, 'templates'):
            confidence += 0.2
            evidence.append('Templates directory found')
            
        if confidence >= self.confidence_threshold:
            return {
                'framework': 'flask',
                'runtime': 'python',
                'confidence': min(confidence, 0.99),
                'evidence': evidence,
                'variant': 'micro-framework',
                'category': 'web-backend',
                'is_deployable': True
            }
            
        return None
    
    def _detect_fastapi(self, repo_path: str, file_analysis: Dict[str, Any], 
                       dependencies: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """🎯 Detect FastAPI framework"""
        
        evidence = []
        confidence = 0.0
        
        # FastAPI entry points
        fastapi_files = ['main.py', 'app.py', 'server.py']
        
        for fastapi_file in fastapi_files:
            if self._file_exists_anywhere(repo_path, fastapi_file):
                if self._file_contains_fastapi_imports(repo_path, fastapi_file):
                    confidence += 0.5
                    evidence.append(f'FastAPI imports found in {fastapi_file}')
                    break
                    
        # Dependencies check
        if dependencies:
            deps = dependencies.get('python', {})
            if 'fastapi' in str(deps).lower():
                confidence += 0.4
                evidence.append('FastAPI dependency found')
                
        if confidence >= self.confidence_threshold:
            return {
                'framework': 'fastapi',
                'runtime': 'python',
                'confidence': min(confidence, 0.99), 
                'evidence': evidence,
                'variant': 'async-api',
                'category': 'web-backend',
                'is_deployable': True
            }
            
        return None
    
    def _detect_generic_python(self, repo_path: str, file_analysis: Dict[str, Any], 
                              dependencies: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """🎯 Detect generic Python project"""
        
        evidence = []
        confidence = 0.0
        
        # Python project indicators
        python_indicators = [
            'setup.py',
            'pyproject.toml', 
            'requirements.txt',
            'Pipfile',
            'poetry.lock',
            'environment.yml'
        ]
        
        found_indicators = []
        for indicator in python_indicators:
            if self._file_exists_anywhere(repo_path, indicator):
                found_indicators.append(indicator)
                
        if found_indicators:
            confidence += 0.3 * len(found_indicators)
            evidence.append(f'Python project files: {found_indicators}')
            
        # Python file count
        py_files = file_analysis.get('file_types', {}).get('.py', 0)
        if py_files > 0:
            confidence += min(0.1 * py_files, 0.4)
            evidence.append(f'{py_files} Python files found')
            
        # Determine if it's a library or app
        is_library = self._is_python_library(repo_path)
        
        if confidence >= self.confidence_threshold:
            return {
                'framework': 'python',
                'runtime': 'python',
                'confidence': min(confidence, 0.85),
                'evidence': evidence,
                'variant': 'library' if is_library else 'application',
                'category': 'library' if is_library else 'application',
                'is_deployable': not is_library
            }
            
        return None
    
    def _file_exists_anywhere(self, repo_path: str, filename: str) -> bool:
        """Check if file exists anywhere in repo"""
        try:
            for root, dirs, files in os.walk(repo_path):
                if filename in files:
                    return True
            return False
        except Exception:
            return False
    
    def _directory_exists(self, repo_path: str, dirname: str) -> bool:
        """Check if directory exists in repo"""
        return os.path.exists(os.path.join(repo_path, dirname))
    
    def _has_django_structure(self, repo_path: str) -> bool:
        """Check for Django app structure"""
        try:
            # Look for Django app patterns
            for root, dirs, files in os.walk(repo_path):
                # Django apps typically have models.py, views.py, etc.
                app_files = ['models.py', 'views.py', 'urls.py']
                found_app_files = [f for f in app_files if f in files]
                if len(found_app_files) >= 2:
                    return True
            return False
        except Exception:
            return False
    
    def _file_contains_flask_imports(self, repo_path: str, filename: str) -> bool:
        """Check if file contains Flask imports"""
        try:
            for root, dirs, files in os.walk(repo_path):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        return 'from flask import' in content or 'import flask' in content
            return False
        except Exception:
            return False
    
    def _file_contains_fastapi_imports(self, repo_path: str, filename: str) -> bool:
        """Check if file contains FastAPI imports"""
        try:
            for root, dirs, files in os.walk(repo_path):
                if filename in files:
                    file_path = os.path.join(root, filename)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read().lower()
                        return 'from fastapi import' in content or 'import fastapi' in content
            return False
        except Exception:
            return False
    
    def _is_python_library(self, repo_path: str) -> bool:
        """Determine if this is a Python library vs application"""
        
        # Libraries typically have setup.py or pyproject.toml
        if self._file_exists_anywhere(repo_path, 'setup.py'):
            return True
        if self._file_exists_anywhere(repo_path, 'pyproject.toml'):
            return True
            
        # Applications typically have main entry points
        app_files = ['main.py', 'app.py', 'run.py', 'server.py', 'manage.py']
        for app_file in app_files:
            if self._file_exists_anywhere(repo_path, app_file):
                return False
                
        # Default to application for deployment purposes
        return False


def detect_python(repo_path: str, file_analysis: Dict[str, Any], 
                 dependencies: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    🎯 Entry point for Python framework detection
    
    Usage:
        from detectors.python import detect_python
        results = detect_python(repo_path, file_analysis, dependencies)
    """
    
    detector = PythonFrameworkDetector()
    return detector.detect_python(repo_path, file_analysis, dependencies)
