"""
Main Intelligence Pipeline
Orchestrates comprehensive repository analysis
"""

# Fix GitPython issue at the beginning
import os
os.environ['GIT_PYTHON_REFRESH'] = 'quiet'

import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
import git
import logging

from .contracts import AnalysisContext, IntelligenceProfile, StackBlueprint
from .stages import (
    DeepCrawlStage,
    DependencyAnalysisStage, 
    FrameworkDetectionStage,
    EnvironmentScanStage,
    DatabaseAnalysisStage,
    IntegrationDetectionStage,
    AuthenticationAnalysisStage,
    CICDAnalysisStage,
    InfrastructureAnalysisStage,
    SecurityAnalysisStage,
    StackComposerStage
)

logger = logging.getLogger(__name__)

class IntelligencePipeline:
    """
    Main pipeline for exhaustive repository analysis
    
    Principles:
    1. No early exits - analyze everything first
    2. Zero execution - static analysis only 
    3. Secret-safe - redact at capture time
    4. Confidence-weighted - evidence accumulates
    5. Deterministic output - same repo = same result
    """
    
    def __init__(self):
        self.stages = [
            DeepCrawlStage(),
            DependencyAnalysisStage(),
            FrameworkDetectionStage(), 
            EnvironmentScanStage(),
            DatabaseAnalysisStage(),
            IntegrationDetectionStage(),
            AuthenticationAnalysisStage(),
            CICDAnalysisStage(),
            InfrastructureAnalysisStage(),
            SecurityAnalysisStage(),
            StackComposerStage()  # Final stage - produces Stack Blueprint
        ]
    
    async def analyze_repository(self, repo_url: str, deployment_id: str) -> Dict[str, Any]:
        """
        Main entry point - clone repo and run complete analysis
        
        Returns:
            Dict containing:
            - success: bool
            - intelligence_profile: IntelligenceProfile 
            - stack_blueprint: StackBlueprint
            - local_repo_path: str
            - analysis_time_seconds: float
        """
        temp_dir = None
        start_time = asyncio.get_event_loop().time()
        
        try:
            # 1. Clone Repository
            temp_dir = tempfile.mkdtemp(prefix=f"intel_{deployment_id}_")
            logger.info(f"🔍 Cloning {repo_url} for exhaustive analysis...")
            
            repo = git.Repo.clone_from(repo_url, temp_dir)
            logger.info(f"✅ Repository cloned: {len(list(Path(temp_dir).rglob('*')))} total items")
            
            # 2. Initialize Analysis Context
            context = AnalysisContext(
                repo_path=Path(temp_dir),
                repo_url=repo_url,
                analysis_id=deployment_id
            )
            
            # 3. Run All Analysis Stages (NO EARLY EXITS)
            logger.info(f"🚀 Starting {len(self.stages)}-stage exhaustive analysis...")
            
            for i, stage in enumerate(self.stages, 1):
                stage_name = stage.__class__.__name__
                logger.info(f"📊 Stage {i}/{len(self.stages)}: {stage_name}")
                
                try:
                    await stage.analyze(context)
                    logger.info(f"✅ {stage_name} completed")
                except Exception as e:
                    logger.error(f"❌ {stage_name} failed: {e}")
                    # Continue with other stages - don't fail fast
                    context.add_security_risk({
                        "type": "analysis_stage_failure",
                        "severity": "medium", 
                        "locations": [stage_name],
                        "note": f"Stage failed: {str(e)}"
                    })
            
            # 4. Calculate Analysis Time
            end_time = asyncio.get_event_loop().time()
            analysis_time = end_time - start_time
            
            # 5. Finalize Intelligence Profile
            intelligence_profile = context.intelligence_profile
            intelligence_profile["analysis_metadata"] = {
                "analysis_time_seconds": analysis_time,
                "stages_completed": len(self.stages),
                "total_files_analyzed": len(context.files),
                "repository_size_bytes": sum(f["size"] for f in context.files)
            }
            
            # 6. Get Stack Blueprint (created by StackComposerStage)
            stack_blueprint = context.stack_blueprint
            
            logger.info(f"🎉 Analysis complete! {analysis_time:.1f}s, {len(context.files)} files")
            
            return {
                "success": True,
                "intelligence_profile": intelligence_profile,
                "stack_blueprint": stack_blueprint, 
                "local_repo_path": temp_dir,
                "analysis_time_seconds": analysis_time,
                "deployment_id": deployment_id
            }
            
        except Exception as e:
            logger.error(f"💥 Intelligence pipeline failed: {e}")
            
            # Cleanup on failure
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            return {
                "success": False,
                "error": str(e),
                "analysis_time_seconds": asyncio.get_event_loop().time() - start_time
            }
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get information about the analysis pipeline"""
        return {
            "version": "1.0.0",
            "stages": [stage.__class__.__name__ for stage in self.stages],
            "capabilities": [
                "Deep file analysis (every file, every word)",
                "Dependency graph extraction", 
                "Framework detection with confidence scoring",
                "Secret detection with redaction",
                "Database schema analysis",
                "Third-party integration detection", 
                "Authentication method analysis",
                "CI/CD pipeline analysis",
                "Infrastructure as Code detection",
                "Security risk assessment",
                "Complete stack blueprint generation"
            ],
            "supported_frameworks": [
                "Laravel (API, Blade, SPA)",
                "Next.js (SSR, Static)",
                "React (SPA, with API)",
                "Vue.js (SPA, Nuxt)",
                "Django (Web, API)",
                "Flask/FastAPI",
                "Ruby on Rails", 
                "Express.js",
                "Static Sites"
            ]
        }
