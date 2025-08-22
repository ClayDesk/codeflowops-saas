import json
from pathlib import Path

def read_composer(repo_root: Path) -> dict:
    """Safely read composer.json without any crashes"""
    p = repo_root / "composer.json"
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def composer_packages(composer: dict | None) -> set[str]:
    """Always return a set of packages, never None"""
    c = composer or {}
    req = c.get("require") or {}
    dev = c.get("require-dev") or {}
    if not isinstance(req, dict): req = {}
    if not isinstance(dev, dict): dev = {}
    return set(req.keys()) | set(dev.keys())
