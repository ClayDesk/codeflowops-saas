"""
🎯 Framework Detection Stage - Crash-Proof Laravel Detection with Stack Blueprint Generation
"""
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import re

# Import crash-proof utilities and detectors
from utils.composer import read_composer, composer_packages
from detectors.laravel import detect_laravel

logger = logging.getLogger(__name__)

def run_framework_detection(repo_root: Path) -> dict:
    """🎯 Crash-proof framework detection with heuristic fallback"""
    composer = read_composer(repo_root)
    candidates = []

    def safe_run(detector, name):
        try:
            res = detector(repo_root, composer)
            if res: candidates.append(res)
        except Exception as e:
            logger.warning("Detector %s failed: %s", name, e)

    safe_run(detect_laravel, "laravel")
    # safe_run(detect_symfony, "symfony") ... add more detectors here

    if not candidates:
        # Heuristic: the files alone look like Laravel
        hints = any((repo_root / p).exists() for p in [
            "artisan", "bootstrap/app.php", "public/index.php", "routes/web.php", "routes/api.php"
        ])
        if hints:
            candidates.append({"framework":"laravel","runtime":"php","confidence":0.72,"evidence":["filesystem-heuristic"]})

    return max(candidates, key=lambda c: c.get("confidence", 0.0)) if candidates else {
        "framework":"unknown","runtime":"unknown","confidence":0.0,"evidence":[]
    }

def build_blueprint(repo_root, detection: dict) -> dict:
    """🏗️ Build deployment blueprint - emit Laravel blueprint when Laravel detected"""
    fw = (detection.get("framework") or "").lower()

    if fw == "laravel":
        return {
            "stack_blueprint_version": "1.0.0",
            "project_kind": "monolith-webapp",
            "services": [{
                "id": "webapp",
                "role": "laravel-app",
                "framework": {"name":"php","variant":"laravel","confidence":detection.get("confidence",0.85)},
                "build": {
                    "tool": "composer+node",
                    "commands": [
                        "composer install --no-dev --prefer-dist --optimize-autoloader",
                        "php artisan config:cache && php artisan route:cache && php artisan view:cache",
                        "npm ci && npm run prod"
                    ]
                },
                "runtime": {
                    "kind": "ecs-fargate",
                    "containers": [
                        {"name":"php-fpm","image":"php:8.2-fpm","port":9000},
                        {"name":"nginx","image":"nginx:stable","port":80,"depends_on":["php-fpm"]}
                    ]
                },
                "health_path": "/",
                "env_example": ".env.example"
            }],
            "shared_resources": {
                "database": {"type":"rds-mysql"},
                "cache": {"type":"elasticache-redis"},
                "object_storage": {"type":"s3"}
            },
            "deployment_targets": {"preferred":"aws"},
            "final_recommendation": {
                "stack_id":"aws.ecs.fargate.php.laravel.v1",
                "confidence": max(0.85, detection.get("confidence", 0.85)),
                "deployment_recipe_id":"aws.ecs.fargate.php.laravel.v1"
            }
        }

    # truly static fallback
    return {
        "stack_blueprint_version":"1.0.0",
        "project_kind":"monolith",
        "services":[],
        "shared_resources":{"object_storage":None,"cdn":None,"auth":None},
        "deployment_targets":{"preferred":"aws"},
        "final_recommendation":{"stack_id":"","confidence":0.5,"deployment_recipe_id":"aws.static.v1"}
    }

class FrameworkDetectionStage:
    """🔍 Crash-Proof Framework Detection with Laravel Blueprint Generation"""

    async def analyze(self, context) -> None:
        """🔍 Main analysis method with comprehensive error handling"""
        try:
            await self._safe_analyze(context)
        except Exception as e:
            logger.error(f"❌ Framework detection failed: {e}")
            # Ensure intelligence_profile is valid even on total failure
            if not hasattr(context, "intelligence_profile") or not isinstance(getattr(context, "intelligence_profile"), dict):
                context.intelligence_profile = {}
            
            context.intelligence_profile["frameworks"] = []
            context.intelligence_profile["stack_classification"] = {"type": "unknown", "confidence": 0.1, "error": str(e)}
            context.intelligence_profile["project_kind"] = "app"
            
    async def _safe_analyze(self, context) -> None:
        """🔍 Safe analysis implementation"""
        repo_path = getattr(context, "repo_path", None)
        if not repo_path or not repo_path.exists():
            logger.error(f"Repository path does not exist: {repo_path}")
            if not hasattr(context, "intelligence_profile") or not isinstance(getattr(context, "intelligence_profile"), dict):
                context.intelligence_profile = {}
            context.intelligence_profile["frameworks"] = []
            context.intelligence_profile["stack_classification"] = {"type": "unknown", "confidence": 0.1}
            context.intelligence_profile["project_kind"] = "app"
            return

        logger.info(f"🔍 Analyzing frameworks in: {repo_path}")

        # 🛡️ Defensive: Ensure intelligence_profile is always a dict
        if not hasattr(context, "intelligence_profile") or context.intelligence_profile is None:
            context.intelligence_profile = {}
        elif not isinstance(context.intelligence_profile, dict):
            context.intelligence_profile = {}

        # 🎯 STEP 1: Run crash-proof framework detection
        detection = run_framework_detection(repo_path)
        
        # 🎯 STEP 2: Create frameworks list for compatibility
        frameworks = []
        if detection["framework"] != "unknown":
            frameworks.append({
                "name": detection["framework"],
                "confidence": detection["confidence"],
                "evidence": detection["evidence"],
                "framework_type": "backend" if detection["runtime"] == "php" else "frontend",
                "language": detection["runtime"],
                "requires_server": detection["runtime"] == "php",
                "deployment_target": "ecs-fargate" if detection["framework"] == "laravel" else "s3+cloudfront"
            })

        # 🎯 STEP 3: Set stack classification
        if detection["framework"] == "laravel":
            stack_classification = {
                "type": "php-laravel",
                "confidence": detection["confidence"],
                "rendering_mode": "server",
                "required_runtimes": ["php-fpm"],
                "evidence": detection["evidence"]
            }
        else:
            stack_classification = {
                "type": "unknown",
                "confidence": 0.1,
                "rendering_mode": "static",
                "required_runtimes": [],
                "evidence": []
            }

        # 🎯 STEP 4: Build stack blueprint
        blueprint = build_blueprint(repo_path, detection)

        # 🎯 STEP 5: Set all context properties
        context.intelligence_profile["frameworks"] = frameworks
        context.intelligence_profile["stack_classification"] = stack_classification
        context.intelligence_profile["project_kind"] = "app"
        context.stack_blueprint = blueprint
        
        # Set detected framework for legacy compatibility
        context.detected_framework = detection["framework"]
        context.confidence = detection["confidence"]
        
        # Set final recommendation
        context.intelligence_profile["final_recommendation"] = {
            "stack_id": blueprint["final_recommendation"]["stack_id"],
            "blueprint_id": blueprint["final_recommendation"]["deployment_recipe_id"], 
            "confidence": blueprint["final_recommendation"]["confidence"]
        }
        
        # Deployment readiness
        if detection["framework"] == "laravel":
            context.intelligence_profile["ready_to_deploy"] = True
            context.intelligence_profile["deployment_complexity"] = "medium"
            context.intelligence_profile["estimated_monthly_cost"] = "$80-200 for Laravel ECS Fargate + RDS + ElastiCache"
            context.intelligence_profile["_prose_verdict_line"] = "✅ Deployable: Laravel → AWS ECS Fargate (Nginx + PHP-FPM) + RDS MySQL"
        else:
            context.intelligence_profile["ready_to_deploy"] = False
            context.intelligence_profile["deployment_complexity"] = "low"
            context.intelligence_profile["estimated_monthly_cost"] = "$10-30/month"
            context.intelligence_profile["_prose_verdict_line"] = "❌ Unknown framework - fallback to static hosting"
        
        logger.info(f"✅ Framework detection complete: framework={detection['framework']}, confidence={detection['confidence']}")
