from pathlib import Path
from utils.composer import composer_packages

def detect_laravel(repo_root: Path, composer: dict | None):
    """Robust multi-signal Laravel detection that works even if composer is bad/missing"""
    
    # Check both root level and common subdirectories
    search_paths = [repo_root]
    
    # Add subdirectories that might contain Laravel apps
    try:
        for item in repo_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Common Laravel subdirectory patterns - be more inclusive
                if any(pattern in item.name.lower() for pattern in ['app', 'laravel', 'lara', 'web', 'src', 'project', 'book']) or len(item.name) < 15:
                    search_paths.append(item)
    except Exception:
        pass  # Continue with just root path if directory scanning fails
    
    best_result = None
    best_score = 0
    
    for search_path in search_paths:
        result = _detect_laravel_in_path(search_path, composer if search_path == repo_root else None)
        if result and result.get("confidence", 0) > best_score:
            best_result = result
            best_score = result.get("confidence", 0)
    
    return best_result

def _detect_laravel_in_path(repo_root: Path, composer: dict | None):
    """Check for Laravel in a specific path"""
    # Try to read composer.json from this path if not provided
    if composer is None and (repo_root / "composer.json").exists():
        try:
            import json
            with open(repo_root / "composer.json") as f:
                composer = json.load(f)
        except Exception:
            composer = None
    
    pkgs = composer_packages(composer)

    # File signals (robust even in partial clones)
    signals = [
        (repo_root / "artisan").exists(),
        (repo_root / "bootstrap" / "app.php").exists(),
        (repo_root / "public" / "index.php").exists(),
        (repo_root / "routes" / "web.php").exists() or (repo_root / "routes" / "api.php").exists(),
        (repo_root / "config" / "app.php").exists(),
    ]
    score = sum(bool(x) for x in signals)

    pkg_hit = any(
        p == "laravel/framework" or p.startswith("laravel/") or p.startswith("illuminate/")
        for p in pkgs
    )

    if not (score >= 2 or pkg_hit):
        return None

    evidence = []
    if (repo_root / "artisan").exists(): evidence.append("artisan")
    if (repo_root / "bootstrap" / "app.php").exists(): evidence.append("bootstrap/app.php")
    if (repo_root / "public" / "index.php").exists(): evidence.append("public/index.php")
    if (repo_root / "routes" / "web.php").exists(): evidence.append("routes/web.php")
    if (repo_root / "routes" / "api.php").exists(): evidence.append("routes/api.php")
    if pkg_hit: evidence.append("composer: laravel/illuminate packages")

    conf = 0.6 + 0.2 * min(score, 3) + (0.2 if pkg_hit else 0.0)
    return {"framework":"laravel","runtime":"php","confidence":round(min(conf, 0.98),2),"evidence":evidence}
