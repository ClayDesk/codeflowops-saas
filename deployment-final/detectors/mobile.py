"""
📱 Mobile Application Detector
================================================================================
Specialized detector for mobile applications including Android, iOS, React Native, Flutter.
Provides appropriate guidance for mobile app distribution vs web deployment.

Key Detection Patterns:
- Android: build.gradle, AndroidManifest.xml, res/ directory, Java/Kotlin
- iOS: .xcodeproj/.xcworkspace, Info.plist, Swift/Objective-C
- React Native: package.json + android/ios dirs + React Native deps
- Flutter: pubspec.yaml, lib/ directory, Dart files
- Xamarin: .sln + Xamarin project structure
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)

class MobileDetector:
    """🎯 Specialized mobile application detection with distribution guidance"""
    
    def __init__(self):
        self.confidence_threshold = 0.7
        
    def detect_mobile(self, repo_path: Path, file_stats: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """
        🔍 Detect mobile applications with distribution recommendations
        
        Detection priority:
        1. React Native (cross-platform web/mobile)
        2. Flutter (cross-platform)
        3. Android (native)
        4. iOS (native)  
        5. Xamarin (cross-platform)
        """
        
        # Check React Native first (has web deployment potential)
        react_native_result = self._detect_react_native(repo_path)
        if react_native_result:
            return react_native_result
            
        # Check Flutter
        flutter_result = self._detect_flutter(repo_path)
        if flutter_result:
            return flutter_result
            
        # Check Android
        android_result = self._detect_android(repo_path, file_stats)
        if android_result:
            return android_result
            
        # Check iOS
        ios_result = self._detect_ios(repo_path)
        if ios_result:
            return ios_result
            
        # Check Xamarin
        xamarin_result = self._detect_xamarin(repo_path)
        if xamarin_result:
            return xamarin_result
            
        return None
    
    def _detect_react_native(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Detect React Native applications"""
        score = 0
        evidence = []
        
        # Check package.json for React Native dependencies
        package_json = repo_path / "package.json"
        has_rn_deps = False
        
        if package_json.exists():
            try:
                with open(package_json) as f:
                    pkg_data = json.load(f)
                    
                all_deps = {}
                all_deps.update(pkg_data.get("dependencies", {}))
                all_deps.update(pkg_data.get("devDependencies", {}))
                
                # Check for React Native dependencies
                rn_indicators = ["react-native", "@react-native", "expo"]
                has_rn_deps = any(any(indicator in dep for indicator in rn_indicators) 
                                for dep in all_deps.keys())
                
                if has_rn_deps:
                    score += 3
                    evidence.append("React Native dependencies")
                    
            except Exception:
                pass
        
        # Check for mobile platform directories
        if (repo_path / "android").exists() and (repo_path / "android").is_dir():
            score += 2
            evidence.append("android/ directory")
            
        if (repo_path / "ios").exists() and (repo_path / "ios").is_dir():
            score += 2  
            evidence.append("ios/ directory")
        
        # Check for React Native specific files
        if (repo_path / "metro.config.js").exists():
            score += 1
            evidence.append("Metro config")
            
        if (repo_path / "react-native.config.js").exists():
            score += 1
            evidence.append("React Native config")
            
        confidence = min(1.0, score / 6.0)
        
        if confidence < self.confidence_threshold or not has_rn_deps:
            return None
            
        return {
            "name": "react-native",
            "framework": "react-native", 
            "runtime": "react-native",
            "framework_type": "mobile-crossplatform",
            "language": "javascript",
            "port": 8081,
            "confidence": round(confidence, 2),
            "evidence": evidence,
            "requires_server": False,
            "deployment_target": "mobile-stores",
            "is_deployable": False,  # Mobile apps don't deploy to web hosting
            "build_tool": "react-native",
            "distribution_method": "app-stores"
        }
    
    def _detect_flutter(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Detect Flutter applications"""
        score = 0
        evidence = []
        
        # Check pubspec.yaml (Flutter's package file)
        pubspec = repo_path / "pubspec.yaml"
        if pubspec.exists():
            score += 3
            evidence.append("pubspec.yaml")
            
            # Check for Flutter dependencies
            try:
                content = pubspec.read_text()
                if "flutter:" in content:
                    score += 2
                    evidence.append("Flutter dependencies")
            except Exception:
                pass
        
        # Check lib/ directory (Flutter source)
        if (repo_path / "lib").exists() and (repo_path / "lib").is_dir():
            score += 2
            evidence.append("lib/ directory")
            
        # Check for Dart files
        dart_files = list(repo_path.rglob("*.dart"))
        if dart_files:
            score += min(2, len(dart_files) // 5 + 1)
            evidence.append(f"{len(dart_files)} Dart files")
            
        confidence = min(1.0, score / 7.0)
        
        if confidence < self.confidence_threshold:
            return None
            
        return {
            "name": "flutter",
            "framework": "flutter",
            "runtime": "flutter",
            "framework_type": "mobile-crossplatform", 
            "language": "dart",
            "port": None,
            "confidence": round(confidence, 2),
            "evidence": evidence,
            "requires_server": False,
            "deployment_target": "mobile-stores",
            "is_deployable": False,
            "build_tool": "flutter",
            "distribution_method": "app-stores"
        }
    
    def _detect_android(self, repo_path: Path, file_stats: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Detect Android applications"""
        score = 0
        evidence = []
        
        # Check for Gradle build files
        gradle_files = list(repo_path.rglob("build.gradle")) + list(repo_path.rglob("*.gradle"))
        if gradle_files:
            score += 2
            evidence.append("Gradle build files")
            
        # Check for AndroidManifest.xml
        manifest_files = list(repo_path.rglob("AndroidManifest.xml"))
        if manifest_files:
            score += 3
            evidence.append("AndroidManifest.xml")
            
        # Check for res/ directory (Android resources)
        res_dirs = [p for p in repo_path.rglob("res") if p.is_dir()]
        if res_dirs:
            score += 2
            evidence.append("Android res/ directory")
            
        # Check for Java/Kotlin files in typical Android structure
        java_files = file_stats.get("java", 0) + file_stats.get("kt", 0)  # Kotlin
        if java_files > 5:
            score += 1
            evidence.append(f"{java_files} Java/Kotlin files")
            
        # Check for typical Android directories
        android_indicators = ["src/main/java", "app/src", "gradle"]
        for indicator in android_indicators:
            if any(indicator in str(p) for p in repo_path.rglob("*")):
                score += 1
                evidence.append(f"Android structure: {indicator}")
                break
                
        confidence = min(1.0, score / 8.0)
        
        if confidence < self.confidence_threshold:
            return None
            
        return {
            "name": "android",
            "framework": "android",
            "runtime": "android",
            "framework_type": "mobile-native",
            "language": "java",
            "port": None,
            "confidence": round(confidence, 2),
            "evidence": evidence,
            "requires_server": False,
            "deployment_target": "google-play",
            "is_deployable": False,
            "build_tool": "gradle",
            "distribution_method": "google-play-store"
        }
    
    def _detect_ios(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Detect iOS applications"""
        score = 0
        evidence = []
        
        # Check for Xcode project files
        xcodeproj = list(repo_path.rglob("*.xcodeproj"))
        xcworkspace = list(repo_path.rglob("*.xcworkspace"))
        
        if xcodeproj:
            score += 3
            evidence.append(".xcodeproj file")
            
        if xcworkspace:
            score += 2
            evidence.append(".xcworkspace file")
            
        # Check for Info.plist
        if list(repo_path.rglob("Info.plist")):
            score += 2
            evidence.append("Info.plist")
            
        # Check for Swift/Objective-C files
        swift_files = list(repo_path.rglob("*.swift"))
        objc_files = list(repo_path.rglob("*.m")) + list(repo_path.rglob("*.h"))
        
        if swift_files:
            score += min(2, len(swift_files) // 10 + 1)
            evidence.append(f"{len(swift_files)} Swift files")
            
        if objc_files:
            score += min(2, len(objc_files) // 10 + 1)  
            evidence.append(f"{len(objc_files)} Objective-C files")
            
        confidence = min(1.0, score / 8.0)
        
        if confidence < self.confidence_threshold:
            return None
            
        return {
            "name": "ios",
            "framework": "ios", 
            "runtime": "ios",
            "framework_type": "mobile-native",
            "language": "swift" if swift_files else "objective-c",
            "port": None,
            "confidence": round(confidence, 2),
            "evidence": evidence,
            "requires_server": False,
            "deployment_target": "app-store",
            "is_deployable": False,
            "build_tool": "xcode",
            "distribution_method": "apple-app-store"
        }
    
    def _detect_xamarin(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Detect Xamarin applications"""
        score = 0
        evidence = []
        
        # Check for .sln file (Visual Studio solution)
        if list(repo_path.rglob("*.sln")):
            score += 2
            evidence.append("Visual Studio solution")
            
        # Check for Xamarin-specific files
        xamarin_indicators = [
            "*.csproj",
            "packages.config", 
            "AssemblyInfo.cs"
        ]
        
        for pattern in xamarin_indicators:
            if list(repo_path.rglob(pattern)):
                score += 1
                evidence.append(pattern)
                
        # Check for typical Xamarin directory structure
        xamarin_dirs = ["Droid", "iOS", "PCL", "Shared"]
        for dir_name in xamarin_dirs:
            if any(dir_name in p.name for p in repo_path.iterdir() if p.is_dir()):
                score += 1
                evidence.append(f"Xamarin {dir_name} project")
                
        confidence = min(1.0, score / 6.0)
        
        if confidence < self.confidence_threshold:
            return None
            
        return {
            "name": "xamarin",
            "framework": "xamarin",
            "runtime": "dotnet", 
            "framework_type": "mobile-crossplatform",
            "language": "csharp",
            "port": None,
            "confidence": round(confidence, 2),
            "evidence": evidence,
            "requires_server": False,
            "deployment_target": "mobile-stores",
            "is_deployable": False,
            "build_tool": "msbuild",
            "distribution_method": "app-stores"
        }


def detect_mobile(repo_path: Path, file_stats: Dict[str, int]) -> Optional[Dict[str, Any]]:
    """Main entry point for mobile application detection"""
    detector = MobileDetector()
    return detector.detect_mobile(repo_path, file_stats)
