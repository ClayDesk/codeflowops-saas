"""
🎯 Angular Framework Detector
Detects Angular applications including Angular CLI projects
"""
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

def detect_angular(repo_root: Path, package_json: dict | None = None):
    """Robust Angular detection"""
    
    # Read package.json if not provided
    if package_json is None:
        package_path = repo_root / "package.json"
        if package_path.exists():
            try:
                with open(package_path) as f:
                    package_json = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read package.json: {e}")
                package_json = {}
        else:
            package_json = {}
    
    if not package_json:
        return None
    
    # Get dependencies
    deps = list((package_json.get('dependencies', {}) or {}).keys())
    dev_deps = list((package_json.get('devDependencies', {}) or {}).keys())
    all_deps = deps + dev_deps
    
    # Check for Angular dependencies
    angular_deps = [p for p in all_deps if p.startswith('@angular/')]
    has_angular_core = '@angular/core' in all_deps
    has_angular_cli = '@angular/cli' in all_deps
    
    # Check for Angular project files
    has_angular_json = (repo_root / "angular.json").exists()
    has_ng_package = (repo_root / "ng-package.json").exists()
    
    # Check for Angular project structure
    has_src = (repo_root / "src").exists()
    has_app = (repo_root / "src" / "app").exists() if has_src else False
    
    # Check for TypeScript files (Angular typically uses TypeScript)
    ts_files = list(repo_root.glob("**/*.ts"))
    component_files = list(repo_root.glob("**/*.component.ts"))
    
    # Check for Angular CLI commands
    scripts = package_json.get('scripts', {})
    ng_commands = [s for s in scripts.values() if 'ng ' in s]
    
    # Calculate confidence
    confidence = 0.0
    evidence = []
    
    if has_angular_core:
        confidence += 0.4
        evidence.append("@angular/core dependency")
    
    if len(angular_deps) >= 3:
        confidence += 0.3
        evidence.append(f"{len(angular_deps)} Angular packages")
    
    if has_angular_json:
        confidence += 0.2
        evidence.append("angular.json config file")
    
    if has_angular_cli:
        confidence += 0.1
        evidence.append("@angular/cli")
    
    if ng_commands:
        confidence += 0.1
        evidence.append(f"Angular CLI scripts: {ng_commands[:2]}")
    
    if component_files:
        confidence += 0.1
        evidence.append(f"{len(component_files)} component files")
    
    if has_app and has_src:
        confidence += 0.1
        evidence.append("Standard Angular project structure")
    
    # Must have angular core to be considered Angular
    if not has_angular_core or confidence < 0.4:
        return None
    
    # Determine Angular version
    angular_version = "unknown"
    if '@angular/core' in deps:
        try:
            core_version = package_json['dependencies']['@angular/core']
            if '^6.' in core_version or '~6.' in core_version:
                angular_version = "6"
            elif '^7.' in core_version or '~7.' in core_version:
                angular_version = "7"
            elif '^8.' in core_version or '~8.' in core_version:
                angular_version = "8"
            elif '^9.' in core_version or '~9.' in core_version:
                angular_version = "9"
            elif '^10.' in core_version or '~10.' in core_version:
                angular_version = "10"
            elif '^11.' in core_version or '~11.' in core_version:
                angular_version = "11"
            elif '^12.' in core_version or '~12.' in core_version:
                angular_version = "12"
            elif '^13.' in core_version or '~13.' in core_version:
                angular_version = "13"
            elif '^14.' in core_version or '~14.' in core_version:
                angular_version = "14"
            elif '^15.' in core_version or '~15.' in core_version:
                angular_version = "15"
            elif '^16.' in core_version or '~16.' in core_version:
                angular_version = "16"
            elif '^17.' in core_version or '~17.' in core_version:
                angular_version = "17"
        except:
            pass
    
    return {
        "name": "angular",
        "framework": "angular",
        "runtime": "nodejs",
        "framework_type": "frontend",
        "language": "typescript",
        "port": 4200,  # Default Angular dev server port
        "confidence": round(min(confidence, 0.98), 2),
        "evidence": evidence,
        "requires_server": False,
        "deployment_target": "s3+cloudfront",
        "variant": f"angular{angular_version}",
        "version": angular_version,
        "build_tool": "angular-cli"
    }
