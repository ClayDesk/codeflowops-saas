# core/utils_js.py
import json
import os
import platform
import shutil
import logging
from pathlib import Path
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

ROLLUP_MARKER = "Cannot find module @rollup/rollup-win32-"

def pick_package_manager(repo_dir: Path, override: Optional[str] = None) -> str:
    """
    Choose the best package manager for this repo, with smart fallbacks
    """
    if override:
        return override.lower()

    pkg_path = repo_dir / "package.json"
    pkg = {}
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # packageManager field takes precedence (Corepack)
    pm_field = (pkg.get("packageManager") or "").split("@")[0]
    if pm_field in {"pnpm", "yarn", "bun"}:
        logger.info(f"Using package manager from packageManager field: {pm_field}")
        return pm_field

    # lockfile-based detection
    if (repo_dir / "pnpm-lock.yaml").exists():
        logger.info("Detected pnpm-lock.yaml, using pnpm")
        return "pnpm"
    if (repo_dir / "yarn.lock").exists():
        logger.info("Detected yarn.lock, using yarn")
        return "yarn"
    if (repo_dir / "bun.lockb").exists():
        logger.info("Detected bun.lockb, using bun")
        return "bun"
    if (repo_dir / "package-lock.json").exists():
        # npm only if no better option - but prefer yarn for Windows Rollup compatibility
        if platform.system() == "Windows":
            logger.warning("Found package-lock.json on Windows - using yarn instead of npm for Rollup compatibility")
            return "yarn"
        else:
            logger.info("Detected package-lock.json, using npm")
            return "npm"

    # default that avoids npm's optional-deps quirk on Windows
    default_pm = "yarn" if platform.system() == "Windows" else "npm"
    logger.info(f"No lockfile detected, defaulting to {default_pm}")
    return default_pm

def has_rollup_platform_pkg(repo_dir: Path) -> bool:
    """Quick presence check for Rollup Windows platform package after install"""
    if platform.system() != "Windows":
        return True  # Not an issue on non-Windows
    
    nm = repo_dir / "node_modules" / "@rollup"
    if not nm.exists():
        return False
    
    # Check for Windows-specific Rollup packages
    rollup_packages = list(nm.glob("rollup-win32-*"))
    has_packages = len(rollup_packages) > 0
    logger.debug(f"Rollup Windows packages found: {[p.name for p in rollup_packages]}")
    return has_packages

def clean_modules_and_lock(repo_dir: Path):
    """Clean node_modules and all lock files for fresh install"""
    logger.info("🧹 Cleaning node_modules and lock files...")
    
    # Remove node_modules
    node_modules = repo_dir / "node_modules"
    if node_modules.exists():
        shutil.rmtree(node_modules, ignore_errors=True)
        logger.info("✅ Removed node_modules")
    
    # Remove all lock files
    lock_files = ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"]
    for lf in lock_files:
        lock_path = repo_dir / lf
        try:
            if lock_path.exists():
                lock_path.unlink()
                logger.info(f"✅ Removed {lf}")
        except Exception as e:
            logger.warning(f"Failed to remove {lf}: {e}")

def robust_install_and_build(
    run_cmd, 
    repo_dir: Path, 
    env: dict,
    pm: str, 
    has_build_script: bool, 
    timeout_install: int = 900, 
    timeout_build: int = 900
) -> Tuple[bool, str]:
    """
    Robust install and build with automatic fallback handling
    
    Args:
        run_cmd: function to run commands (like run_npm_command)
        repo_dir: repository directory 
        env: environment variables
        pm: package manager to use
        has_build_script: whether package.json has a build script
        timeout_install: install timeout in seconds
        timeout_build: build timeout in seconds
    
    Returns:
        (success, message)
    """
    logger.info(f"🚀 Starting robust install and build with {pm}")
    
    # 1) Choose install and build commands based on package manager
    if pm == "pnpm":
        install_cmd = ["pnpm", "install", "--frozen-lockfile"]
        build_cmd = ["pnpm", "build"] if has_build_script else ["pnpm", "exec", "vite", "build"]
    elif pm == "yarn":
        berry = (repo_dir / ".yarnrc.yml").exists()
        install_cmd = ["yarn", "install", "--immutable" if berry else "--frozen-lockfile"]
        build_cmd = ["yarn", "build"] if has_build_script else ["yarn", "vite", "build"]
        env.setdefault("YARN_NODE_LINKER", "node-modules")
        env.setdefault("COREPACK_ENABLE_DOWNLOAD_PROMPT", "0")
    elif pm == "bun":
        install_cmd = ["bun", "install", "--frozen-lockfile"]
        build_cmd = ["bun", "run", "build"] if has_build_script else ["bunx", "vite", "build"]
    else:
        # npm path
        if (repo_dir / "package-lock.json").exists():
            install_cmd = ["npm", "ci"]
        else:
            install_cmd = ["npm", "install"]
        build_cmd = ["npm", "run", "build"] if has_build_script else ["npm", "exec", "vite", "build"]

    logger.info(f"📦 Install command: {' '.join(install_cmd)}")
    logger.info(f"🔨 Build command: {' '.join(build_cmd)}")

    # 2) Initial install attempt
    logger.info("📦 Running initial install...")
    ok, out, err = run_cmd(install_cmd, repo_dir, env=env, timeout=timeout_install)
    
    if not ok:
        text = f"{out}\n{err}"
        # If npm + optional-deps bug → clean & re-resolve with npm install
        if pm == "npm" and ROLLUP_MARKER.lower() in text.lower():
            logger.warning("⚠️ npm optional-deps issue detected during install. Reinstalling with npm install.")
            clean_modules_and_lock(repo_dir)
            ok, out, err = run_cmd(["npm", "install"], repo_dir, env=env, timeout=timeout_install)
            if not ok:
                return False, f"Install failed after fallback: {err or out}"
        else:
            return False, f"Install failed: {err or out}"

    # 3) Preflight Rollup presence check on Windows
    if not has_rollup_platform_pkg(repo_dir):
        logger.warning("⚠️ Rollup platform package missing after install")
        if pm == "npm":
            logger.info("🧶 Trying Yarn fallback for Rollup compatibility...")
            clean_modules_and_lock(repo_dir)
            # Yarn fallback
            berry = (repo_dir / ".yarnrc.yml").exists()
            install_yarn = ["yarn", "install", "--immutable" if berry else "--frozen-lockfile"]
            ok, out, err = run_cmd(install_yarn, repo_dir, env=env, timeout=timeout_install)
            if not ok:
                # As last resort: npm install (not ci)
                logger.warning("⚠️ Yarn fallback failed. Trying npm install.")
                ok, out, err = run_cmd(["npm", "install"], repo_dir, env=env, timeout=timeout_install)
                if not ok:
                    return False, f"Reinstall attempts failed: {err or out}"

    # 4) Build attempt (with auto-retry on Rollup error)
    logger.info("🔨 Running build...")
    ok, out, err = run_cmd(build_cmd, repo_dir, env=env, timeout=timeout_build)
    
    if not ok:
        text = f"{out}\n{err}"
        if ROLLUP_MARKER.lower() in text.lower():
            logger.warning("⚠️ Rollup error on build; re-installing with Yarn and retrying build.")
            clean_modules_and_lock(repo_dir)
            berry = (repo_dir / ".yarnrc.yml").exists()
            install_yarn = ["yarn", "install", "--immutable" if berry else "--frozen-lockfile"]
            ok, out2, err2 = run_cmd(install_yarn, repo_dir, env=env, timeout=timeout_install)
            if ok:
                # retry build via Yarn (which resolves local bins)
                build2 = ["yarn", "build"] if has_build_script else ["yarn", "vite", "build"]
                logger.info("🔨 Retrying build with Yarn...")
                ok, out3, err3 = run_cmd(build2, repo_dir, env=env, timeout=timeout_build)
                if ok:
                    return True, "✅ Build succeeded after Yarn fallback"
                return False, f"Build failed after Yarn fallback: {err3 or out3}"
            
            # Yarn install failed; try npm install then build again
            logger.warning("⚠️ Yarn install failed, trying npm install fallback")
            ok, out4, err4 = run_cmd(["npm", "install"], repo_dir, env=env, timeout=timeout_install)
            if ok:
                ok, out5, err5 = run_cmd(build_cmd, repo_dir, env=env, timeout=timeout_build)
                if ok:
                    return True, "✅ Build succeeded after npm reinstall"
                return False, f"Build failed after npm reinstall: {err5 or out5}"
            return False, f"Build failed; reinstall attempts failed: {err2 or out2 or err4 or out4}"
        
        return False, f"Build failed: {err or out}"

    return True, "✅ Build succeeded"

def has_build_script(repo_dir: Path) -> bool:
    """Check if package.json has a build script"""
    pkg_path = repo_dir / "package.json"
    if not pkg_path.exists():
        return False
    
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        scripts = pkg.get("scripts", {})
        return "build" in scripts
    except Exception as e:
        logger.warning(f"Failed to parse package.json: {e}")
        return False
