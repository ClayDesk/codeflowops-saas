# core/utils_js_compat.py
import json, os, shutil
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def _write_npmrc(repo: Path):
    """Write .npmrc with legacy compatibility settings"""
    npmrc_content = """legacy-peer-deps=true
engine-strict=false
fund=false
audit=false
"""
    (repo / ".npmrc").write_text(npmrc_content, encoding="utf-8")
    logger.info("✅ Created .npmrc with legacy peer deps enabled")

def patch_legacy_next_for_node22(repo: Path) -> bool:
    """
    For old Next (e.g., 10.x) under Node 22:
    - pin postcss to a pre-exports build (works with next 10's compiled postcss-scss)
    - enable legacy peer deps via .npmrc
    - clean node_modules + npm lock (force re-resolve)
    Returns True if a patch was applied.
    """
    pj = repo / "package.json"
    if not pj.exists():
        logger.warning(f"❌ package.json not found at {pj}")
        return False

    try:
        pkg = json.loads(pj.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"❌ Failed to parse package.json: {e}")
        return False

    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    next_ver = str(deps.get("next", ""))

    # Heuristic: apply only for very old Next (<= 10.x)
    apply = next_ver and (next_ver.startswith("10.") or next_ver.startswith("^10") or next_ver == "10")
    if not apply:
        logger.info(f"ℹ️ Next.js {next_ver} - no legacy patch needed")
        return False

    logger.info(f"🔧 Applying legacy Next.js patch for Node 22 compatibility (Next.js {next_ver})")

    # Add overrides/resolutions to pin postcss (pre-exports)
    # 8.3.11 is a common safe pin for Next 10 vintage
    pkg.setdefault("overrides", {}).update({"postcss": "8.3.11"})
    # If yarn classic is used, also add resolutions
    pkg.setdefault("resolutions", {}).update({"postcss": "8.3.11"})

    pj.write_text(json.dumps(pkg, indent=2), encoding="utf-8")
    logger.info("✅ PostCSS pinned to 8.3.11 for compatibility")

    # .npmrc enabling legacy peer deps for npm installs
    _write_npmrc(repo)

    # clean so the new constraints take effect
    logger.info("🧹 Cleaning node_modules and lock files for fresh install...")
    shutil.rmtree(repo / "node_modules", ignore_errors=True)
    for lf in ("package-lock.json", "pnpm-lock.yaml", "bun.lockb"):
        try:
            (repo / lf).unlink()
            logger.info(f"🗑️ Removed {lf}")
        except Exception:
            pass

    logger.info("✅ Legacy Next.js patch applied successfully")
    return True

def get_next_version_info(repo: Path) -> dict:
    """Get Next.js version information from package.json"""
    pj = repo / "package.json"
    if not pj.exists():
        return {"found": False, "version": None, "is_legacy": False}
    
    try:
        pkg = json.loads(pj.read_text(encoding="utf-8"))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        next_ver = deps.get("next")
        
        if not next_ver:
            return {"found": False, "version": None, "is_legacy": False}
        
        # Check if legacy (needs compatibility patch)
        next_ver_str = str(next_ver)
        is_legacy = next_ver_str.startswith(("10.", "^10")) or next_ver_str == "10"
        
        return {
            "found": True,
            "version": next_ver,
            "is_legacy": is_legacy,
            "needs_patch": is_legacy
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get Next.js version info: {e}")
        return {"found": False, "version": None, "is_legacy": False, "error": str(e)}
