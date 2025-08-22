"""
🎮 Unity Game Engine Detector
================================================================================
Specialized detector for Unity projects including WebGL deployment support.
Detects Coherence networking backend for multiplayer games.

Key Detection Patterns:
- Assets/ directory (Unity project structure)
- ProjectSettings/ directory with ProjectVersion.txt
- Packages/manifest.json with com.unity.* dependencies
- Unity file extensions: .unity, .meta, .asmdef, .shadergraph, .fbx, .anim
- Coherence SDK detection for multiplayer backend
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class UnityDetector:
    """🎯 Specialized Unity project detection with WebGL deployment support"""
    
    def __init__(self):
        self.confidence_threshold = 0.8
        self.skip_dirs = {"Library", "Temp", ".git", "node_modules"}
        self.unity_extensions = {".unity", ".meta", ".asmdef", ".shadergraph", ".fbx", ".anim"}
        
    def detect_unity(self, repo_path: Path, file_stats: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """
        🔍 Detect Unity projects with deployment recommendations
        
        Scoring system (weights):
        - Assets/ directory (2 points)
        - ProjectSettings/ directory (2 points) 
        - Packages/manifest.json with Unity deps (2 points)
        - Unity file extensions (1 each, max 2 points)
        - ProjectVersion.txt parseable (2 points)
        
        Confidence = min(1.0, total_score / 6)
        Detected if confidence >= 0.8
        """
        
        score = 0
        evidence = []
        unity_version = None
        networking_backend = None
        webgl_build_present = False
        
        try:
            # Signal 1: Assets/ directory (2 points)
            assets_dir = repo_path / "Assets"
            if assets_dir.exists() and assets_dir.is_dir():
                score += 2
                evidence.append("Assets/ directory")
                
            # Signal 2: ProjectSettings/ directory (2 points)
            project_settings = repo_path / "ProjectSettings"
            if project_settings.exists() and project_settings.is_dir():
                score += 2
                evidence.append("ProjectSettings/ directory")
                
                # Parse ProjectVersion.txt for Unity version (2 points)
                version_file = project_settings / "ProjectVersion.txt"
                if version_file.exists():
                    unity_version = self._parse_unity_version(version_file)
                    if unity_version:
                        score += 2
                        evidence.append(f"Unity version {unity_version}")
                        
            # Signal 3: Packages/manifest.json with Unity dependencies (2 points)
            packages_manifest = repo_path / "Packages" / "manifest.json"
            if packages_manifest.exists():
                unity_packages, coherence_detected = self._analyze_unity_packages(packages_manifest)
                if unity_packages > 0:
                    score += 2
                    evidence.append(f"{unity_packages} Unity packages")
                    
                if coherence_detected:
                    networking_backend = "coherence"
                    evidence.append("Coherence SDK detected")
                    
            # Signal 4: Unity file extensions (1 each, max 2 points)
            unity_files = 0
            for ext in self.unity_extensions:
                if ext in [f".{k}" for k in file_stats.keys()]:
                    unity_files += file_stats.get(ext.lstrip('.'), 0)
                    
            # Quick scan for Unity files if file_stats incomplete
            if unity_files == 0:
                unity_files = self._count_unity_files(repo_path)
                
            if unity_files > 0:
                ext_score = min(2, unity_files // 10 + 1)  # Scale based on file count
                score += ext_score
                evidence.append(f"{unity_files} Unity asset files")
                
            # Check for WebGL build
            webgl_build_present = self._check_webgl_build(repo_path)
            if webgl_build_present:
                evidence.append("WebGL build detected")
                
            # Calculate confidence
            confidence = min(1.0, score / 6.0)
            
            if confidence < self.confidence_threshold:
                return None
                
            # Determine deployment readiness and target
            deployment_target, deploy_ready, deployment_recipe = self._determine_deployment(
                webgl_build_present, networking_backend
            )
            
            return {
                "name": "unity",
                "framework": "unity",
                "runtime": "unity-engine",
                "framework_type": "game-engine",
                "language": "csharp",
                "port": 80 if webgl_build_present else None,
                "confidence": round(confidence, 2),
                "evidence": evidence,
                "requires_server": False,
                "deployment_target": deployment_target,
                "is_deployable": deploy_ready,
                "unity_version": unity_version,
                "networking_backend": networking_backend,
                "webgl_build_present": webgl_build_present,
                "build_tool": "unity-editor",
                "deployment_recipe": deployment_recipe
            }
            
        except Exception as e:
            logger.warning(f"Unity detection failed: {e}")
            return None
    
    def _parse_unity_version(self, version_file: Path) -> Optional[str]:
        """Parse Unity version from ProjectVersion.txt"""
        try:
            content = version_file.read_text(encoding='utf-8')
            match = re.search(r'(?i)Unity\s+(\d+\.\d+\.\d+[a-z0-9]*)', content)
            return match.group(1) if match else None
        except Exception:
            return None
    
    def _analyze_unity_packages(self, manifest_file: Path) -> Tuple[int, bool]:
        """Analyze Packages/manifest.json for Unity and Coherence dependencies"""
        try:
            with open(manifest_file) as f:
                manifest = json.load(f)
                
            dependencies = manifest.get("dependencies", {})
            
            # Count Unity packages
            unity_packages = sum(1 for pkg in dependencies.keys() if pkg.startswith("com.unity."))
            
            # Check for Coherence SDK
            coherence_detected = any(
                "coherence" in pkg.lower() or "io.coherence" in pkg
                for pkg in dependencies.keys()
            )
            
            return unity_packages, coherence_detected
            
        except Exception:
            return 0, False
    
    def _count_unity_files(self, repo_path: Path) -> int:
        """Quick count of Unity-specific files"""
        count = 0
        try:
            for ext in self.unity_extensions:
                files = list(repo_path.rglob(f"*{ext}"))
                # Filter out files in skip directories
                filtered_files = [
                    f for f in files 
                    if not any(skip_dir in str(f) for skip_dir in self.skip_dirs)
                ]
                count += len(filtered_files)
        except Exception:
            pass
        return min(count, 1000)  # Cap for performance
    
    def _check_webgl_build(self, repo_path: Path) -> bool:
        """Check if WebGL build directory exists"""
        potential_paths = [
            repo_path / "Build" / "WebGL",
            repo_path / "Builds" / "WebGL", 
            repo_path / "WebGL",
            repo_path / "build" / "webgl"
        ]
        
        return any(path.exists() and path.is_dir() for path in potential_paths)
    
    def _determine_deployment(self, webgl_build_present: bool, networking_backend: Optional[str]) -> Tuple[str, bool, str]:
        """Determine deployment target and readiness"""
        
        if webgl_build_present:
            # WebGL build present - ready for web deployment
            return "s3+cloudfront", True, "aws.s3.cloudfront.unity.webgl.v1"
        
        # No WebGL build but Unity projects can be built for WebGL deployment
        # Mark as deployable with guidance to build for WebGL
        return "s3+cloudfront", True, "aws.s3.cloudfront.unity.webgl.v1"


def detect_unity(repo_path: Path, file_stats: Dict[str, int]) -> Optional[Dict[str, Any]]:
    """Main entry point for Unity detection"""
    detector = UnityDetector()
    return detector.detect_unity(repo_path, file_stats)
