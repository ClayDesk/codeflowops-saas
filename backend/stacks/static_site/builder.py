"""
Static site builder - no build process needed for static sites
"""
from pathlib import Path
from core.models import StackPlan, BuildResult
from core.utils import find_files
import logging

logger = logging.getLogger(__name__)

class StaticSiteBuilder:
    """Handles 'building' static sites (which is mostly validation)"""
    
    def build(self, plan: StackPlan, repo_dir: Path) -> BuildResult:
        """
        'Build' a static site - mainly validation since no compilation needed
        """
        try:
            logger.info("🔍 Validating static site structure...")
            
            # Validate that output directory exists
            if not plan.output_dir.exists():
                return BuildResult(
                    success=False,
                    artifact_dir=repo_dir,
                    error_message=f"Output directory not found: {plan.output_dir}"
                )
            
            # Check for entry point
            entry_point = plan.config.get("entry_point", "index.html")
            entry_file = plan.output_dir / entry_point
            
            if not entry_file.exists():
                return BuildResult(
                    success=False,
                    artifact_dir=repo_dir,
                    error_message=f"Entry point not found: {entry_point}"
                )
            
            # Count web assets
            html_files = find_files(plan.output_dir, ["*.html"])
            css_files = find_files(plan.output_dir, ["*.css"])
            js_files = find_files(plan.output_dir, ["*.js"])
            image_files = find_files(plan.output_dir, ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico"])
            
            total_files = len(html_files) + len(css_files) + len(js_files) + len(image_files)
            
            if total_files == 0:
                logger.warning("No web assets found in static site")
            
            logger.info(f"✅ Static site validated:")
            logger.info(f"   📄 HTML files: {len(html_files)}")
            logger.info(f"   🎨 CSS files: {len(css_files)}")
            logger.info(f"   ⚡ JS files: {len(js_files)}")
            logger.info(f"   🖼️ Image files: {len(image_files)}")
            
            return BuildResult(
                success=True,
                artifact_dir=plan.output_dir,
                build_time_seconds=0.1,  # Instant validation
                metadata={
                    "entry_point": entry_point,
                    "html_files": len(html_files),
                    "css_files": len(css_files),
                    "js_files": len(js_files),
                    "image_files": len(image_files),
                    "total_assets": total_files
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Static site validation failed: {e}")
            return BuildResult(
                success=False,
                artifact_dir=repo_dir,
                error_message=f"Validation failed: {str(e)}"
            )
    
    def validate_build_requirements(self, repo_dir: Path) -> bool:
        """Static sites have no build requirements"""
        return True  # Always ready - no tools needed
