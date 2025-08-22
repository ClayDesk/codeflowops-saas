"""
🎯 Robust Laravel Framework Detector
Safe detection that prevents NoneType errors and provides high-confidence Laravel detection
"""
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

def safe_load_json(p: Path):
    """Safely load JSON file without crashing on invalid/missing files"""
    try:
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        logger.debug(f"Could not parse JSON {p}: {e}")
        return {}

def is_laravel(repo_root: Path):
    """
    🔍 Robust Laravel detection using multiple heuristics
    Returns None if not Laravel, or dict with framework info if detected
    """
    if not repo_root or not repo_root.exists():
        return None
        
    # File heuristics (any 2+ is enough for Laravel)
    file_checks = [
        (repo_root / "artisan").exists(),
        (repo_root / "bootstrap" / "app.php").exists(),
        (repo_root / "public" / "index.php").exists(),
        (repo_root / "routes" / "web.php").exists() or (repo_root / "routes" / "api.php").exists(),
        (repo_root / "config" / "app.php").exists(),
    ]
    file_score = sum(1 for x in file_checks if x)

    # Composer heuristics (safe even if composer.json missing/malformed)
    composer = safe_load_json(repo_root / "composer.json")
    require = composer.get("require") or {}
    require_dev = composer.get("require-dev") or {}
    
    # Ensure require and require_dev are dictionaries
    if not isinstance(require, dict):
        require = {}
    if not isinstance(require_dev, dict):
        require_dev = {}

    pkgs = set(require.keys()) | set(require_dev.keys())
    composer_hit = any(
        p.startswith("laravel/") or p.startswith("illuminate/") or p == "laravel/framework"
        for p in pkgs
    )

    # Calculate confidence: base 60% + file score + composer bonus
    confidence = 0.6 + 0.2 * min(file_score, 3) + (0.2 if composer_hit else 0.0)
    is_match = (file_score >= 2) or composer_hit

    if not is_match:
        return None

    # Build evidence list
    evidence = []
    if (repo_root / "artisan").exists(): 
        evidence.append("artisan command file")
    if (repo_root / "bootstrap" / "app.php").exists(): 
        evidence.append("bootstrap/app.php")
    if (repo_root / "routes" / "web.php").exists(): 
        evidence.append("routes/web.php")
    if (repo_root / "routes" / "api.php").exists(): 
        evidence.append("routes/api.php")
    if (repo_root / "public" / "index.php").exists(): 
        evidence.append("public/index.php")
    if (repo_root / "config" / "app.php").exists():
        evidence.append("config/app.php")
    if composer_hit: 
        evidence.append("composer.json: laravel/illuminate packages")

    # Check for additional Laravel features
    if (repo_root / "database" / "migrations").exists():
        evidence.append("database/migrations")
    if (repo_root / "app" / "Http" / "Controllers").exists():
        evidence.append("app/Http/Controllers")
    if (repo_root / "resources" / "views").exists():
        evidence.append("resources/views")

    return {
        "name": "laravel",
        "framework": "laravel",
        "runtime": "php",
        "framework_type": "backend",
        "language": "php",
        "port": 80,
        "confidence": round(min(confidence, 0.98), 2),
        "evidence": evidence,
        "requires_server": True,
        "deployment_target": "ecs-fargate",
        "variant": "webapp"
    }

def detect_vue_frontend(repo_root: Path):
    """
    🔍 Detect Vue.js frontend in Laravel application
    """
    if not repo_root or not repo_root.exists():
        return None
        
    # Check for Vue.js files in Laravel structure
    vue_files = list(repo_root.glob("**/*.vue"))
    if not vue_files:
        return None
        
    # Check package.json for Vue dependencies
    package_json = safe_load_json(repo_root / "package.json")
    deps = {}
    deps.update(package_json.get("dependencies", {}))
    deps.update(package_json.get("devDependencies", {}))
    
    has_vue = "vue" in deps
    has_webpack_mix = "laravel-mix" in deps or (repo_root / "webpack.mix.js").exists()
    
    if not (has_vue or len(vue_files) >= 5):
        return None
        
    evidence = []
    evidence.append(f"{len(vue_files)} Vue components")
    if has_vue:
        evidence.append("vue in package.json")
    if has_webpack_mix:
        evidence.append("Laravel Mix for asset compilation")
    if (repo_root / "resources" / "assets").exists():
        evidence.append("resources/assets directory")
        
    return {
        "name": "vue",
        "framework": "vue",
        "runtime": "javascript", 
        "framework_type": "frontend",
        "language": "javascript",
        "confidence": 0.90 if has_vue else 0.75,
        "evidence": evidence,
        "requires_server": False,
        "deployment_target": "embedded",
        "variant": "laravel-embedded"
    }
