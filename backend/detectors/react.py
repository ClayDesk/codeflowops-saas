"""
🎯 React Framework Detector
Detects React applications including Create React App, Vite, Next.js, and custom setups
"""
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

def detect_react(repo_root: Path, package_json: dict | None = None):
    """Robust multi-signal React detection"""
    
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
    
    # Get dependencies
    deps = list((package_json.get('dependencies', {}) or {}).keys())
    dev_deps = list((package_json.get('devDependencies', {}) or {}).keys())
    all_deps = deps + dev_deps
    
    # Check for React dependencies
    react_deps = [p for p in all_deps if 'react' in p.lower()]
    has_react = 'react' in all_deps
    has_react_dom = 'react-dom' in all_deps
    
    # Check for React files
    jsx_files = list(repo_root.glob("**/*.jsx")) + list(repo_root.glob("**/*.js"))
    tsx_files = list(repo_root.glob("**/*.tsx")) + list(repo_root.glob("**/*.ts"))
    
    # Check for React project structure
    has_src = (repo_root / "src").exists()
    has_public = (repo_root / "public").exists()
    has_components = any([
        (repo_root / "src" / "components").exists(),
        (repo_root / "src" / "Components").exists(),
        (repo_root / "components").exists()
    ])
    
    # Check for build tools
    scripts = package_json.get('scripts', {})
    has_build_script = 'build' in scripts
    has_dev_script = 'dev' in scripts or 'start' in scripts
    
    # Determine React variant
    variant = "unknown"
    build_tool = "unknown"
    
    if '@vitejs/plugin-react' in all_deps or 'vite' in all_deps:
        variant = "vite"
        build_tool = "vite"
    elif 'next' in all_deps or (repo_root / "next.config.js").exists():
        variant = "nextjs"
        build_tool = "next"
    elif 'react-scripts' in all_deps:
        variant = "create-react-app"  
        build_tool = "react-scripts"
    elif has_react and has_react_dom:
        variant = "custom"
        build_tool = "webpack" if 'webpack' in all_deps else "custom"
    
    # Calculate confidence score
    score = 0
    evidence = []
    
    if has_react:
        score += 40
        evidence.append("react dependency")
    if has_react_dom:
        score += 30
        evidence.append("react-dom dependency")
    if jsx_files:
        score += 20
        evidence.append(f"{len(jsx_files)} JSX files")
    if has_src:
        score += 10
        evidence.append("src directory")
    if has_components:
        score += 10
        evidence.append("components directory")
    if has_build_script:
        score += 10
        evidence.append("build script")
    if len(react_deps) > 2:
        score += 10
        evidence.append(f"multiple React packages: {react_deps[:3]}")
    
    # Must have basic React indicators
    if not (has_react and (jsx_files or has_src)):
        return None
    
    confidence = min(score / 100.0, 0.98)
    
    return {
        "framework": "react",
        "runtime": "nodejs",
        "confidence": round(confidence, 2),
        "evidence": evidence,
        "variant": variant,
        "build_tool": build_tool,
        "typescript": len(tsx_files) > 0
    }
