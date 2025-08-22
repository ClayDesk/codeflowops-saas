"""
🎯 Node.js Framework Detector - Differentiates apps, libraries, and monorepos
"""
from pathlib import Path
import json
import glob
import logging

logger = logging.getLogger(__name__)

def read_pkg(root_path):
    """Read package.json safely"""
    pkg_file = Path(root_path) / "package.json"
    if not pkg_file.exists():
        return None
    try:
        return json.loads(pkg_file.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning(f"Failed to read package.json: {e}")
        return None

def has_node_lock(root):
    """Check for Node.js lockfiles"""
    root_path = Path(root)
    return any((root_path / f).exists() for f in ("yarn.lock", "package-lock.json", "pnpm-lock.yaml"))

def is_monorepo(pkg, root):
    """Detect if this is a monorepo"""
    if not pkg:
        return False
    if "workspaces" in pkg:
        return True
    if (Path(root) / "pnpm-workspace.yaml").exists():
        return True
    if (Path(root) / "lerna.json").exists():
        return True
    return bool(glob.glob(str(Path(root) / "packages" / "*" / "package.json")))

def is_tooling_repo(root):
    """Detect if this is a tooling/library repo based on package structure"""
    packages_dir = Path(root) / "packages"
    if not packages_dir.exists():
        return False
    
    # Check for common tooling package names
    tooling_indicators = [
        "create-react-app", "react-scripts", "@babel/", "webpack", 
        "eslint-config", "prettier-config", "rollup", "vite"
    ]
    
    for pkg_dir in packages_dir.glob("*"):
        if pkg_dir.is_dir():
            pkg_name = pkg_dir.name
            if any(indicator in pkg_name for indicator in tooling_indicators):
                return True
            
            # Check package.json in subdirectory
            sub_pkg = read_pkg(pkg_dir)
            if sub_pkg:
                name = sub_pkg.get("name", "")
                if any(indicator in name for indicator in tooling_indicators):
                    return True
    
    return False

def get_repo_intent(pkg, root):
    """Determine if this is an app, library, or tooling repo"""
    if not pkg:
        return "unknown"
    
    # Check for library indicators
    if "bin" in pkg or "files" in pkg or "publishConfig" in pkg:
        return "library"
    
    # Check for monorepo tooling
    if is_monorepo(pkg, root) and is_tooling_repo(root):
        return "tooling"
    
    # Check for app indicators
    if "src" in str(Path(root).iterdir()) or (Path(root) / "public" / "index.html").exists():
        return "app"
    
    return "unknown"

def detect_nodejs(repo_root: Path, file_stats: dict = None):
    """Detect Node.js projects with proper classification"""
    pkg = read_pkg(repo_root)
    
    # Must have package.json or lockfile to be considered Node.js
    if not pkg and not has_node_lock(repo_root):
        return None
    
    if not pkg:
        # Has lockfile but no package.json - probably broken
        return {
            "framework": "nodejs",
            "runtime": "nodejs", 
            "confidence": 0.3,
            "evidence": ["lockfile found, no package.json"],
            "intent": "unknown",
            "is_deployable": False
        }
    
    deps = {**(pkg.get("dependencies", {}) or {}), **(pkg.get("devDependencies", {}) or {})}
    scripts = pkg.get("scripts", {})
    repo_intent = get_repo_intent(pkg, repo_root)
    
    # Monorepo detection
    if is_monorepo(pkg, repo_root):
        return {
            "framework": "nodejs-monorepo",
            "runtime": "nodejs",
            "confidence": 0.95,
            "evidence": ["workspaces or packages/* structure"],
            "intent": "tooling" if is_tooling_repo(repo_root) else "unknown", 
            "is_deployable": False,
            "build_commands": [],
            "output_dir": None
        }
    
    # React app variants
    if "react-scripts" in deps:
        return {
            "framework": "create-react-app",
            "runtime": "nodejs",
            "confidence": 0.99,
            "evidence": ["react-scripts dependency"],
            "intent": "app",
            "is_deployable": True,
            "build_commands": ["npm ci", "npm run build"],
            "output_dir": "build"
        }
    
    if "next" in deps:
        return {
            "framework": "nextjs",
            "runtime": "nodejs", 
            "confidence": 0.99,
            "evidence": ["next dependency"],
            "intent": "app",
            "is_deployable": True,
            "build_commands": ["npm ci", "npm run build"],
            "output_dir": ".next"
        }
    
    if "vite" in deps and ("react" in deps or "@vitejs/plugin-react" in deps):
        return {
            "framework": "react-vite",
            "runtime": "nodejs",
            "confidence": 0.95, 
            "evidence": ["vite + react dependencies"],
            "intent": "app",
            "is_deployable": True,
            "build_commands": ["npm ci", "npm run build"],
            "output_dir": "dist"
        }
    
    if "react" in deps and "react-dom" in deps:
        return {
            "framework": "react-custom",
            "runtime": "nodejs",
            "confidence": 0.85,
            "evidence": ["react + react-dom dependencies"],
            "intent": "app", 
            "is_deployable": True,
            "build_commands": ["npm ci", "npm run build"] if "build" in scripts else [],
            "output_dir": "build"
        }
    
    # Generic Node.js app
    has_build = "build" in scripts
    return {
        "framework": "nodejs",
        "runtime": "nodejs",
        "confidence": 0.7,
        "evidence": ["package.json found"],
        "intent": repo_intent,
        "is_deployable": has_build and repo_intent == "app",
        "build_commands": ["npm ci", "npm run build"] if has_build else [],
        "output_dir": None
    }

def should_skip_static_detection(repo_root: Path, file_stats: dict = None):
    """Determine if static detection should be skipped for this repo"""
    pkg = read_pkg(repo_root)
    
    # Has package.json with dependencies - not a simple static site
    if pkg and (pkg.get("dependencies") or pkg.get("devDependencies")):
        return True
    
    # Has lockfiles - Node.js project
    if has_node_lock(repo_root):
        return True
    
    # Many JS/TS files indicate a complex project, not static
    if file_stats:
        js_count = sum(file_stats.get(ext, 0) for ext in ('.js', '.ts', '.tsx', '.jsx'))
        if js_count > 20:
            return True
    
    return False
