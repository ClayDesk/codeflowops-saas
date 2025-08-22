"""
Enhanced Repository Analyzer
Integrates the new Intelligence Pipeline with Stack Composer for complete analysis
"""
from typing import Dict, Any
import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from analyzer.pipeline import IntelligencePipeline
from analyzer.stack_composer import StackComposer, create_stack_composer

logger = logging.getLogger(__name__)

class EnhancedRepositoryAnalyzer:
    """
    Enhanced analyzer that uses the new Intelligence Pipeline + S            # 🔥 Firebase configuration files (CLIENT-SIDE)
            "firebase.json": "firestore",
            ".firebaserc": "firestore",
            "firestore.rules": "firestore_security",
            "firestore.indexes.json": "firestore",
            "firebase.config.js": "firestore",
            "firebase.config.ts": "firestore",
            "src/firebase.js": "firestore_config",
            "src/firebase.ts": "firestore_config", 
            "src/config/firebase.js": "firestore_config",
            "src/config/firebase.ts": "firestore_config",
            "src/database/firebase.js": "firestore_config",
            "src/database/firebase.ts": "firestore_config",
            "firebase-config.js": "firestore_config",
            "firebase-config.ts": "firestore_config",
            
            # 🟦 Supabase configuration files (CLIENT-SIDE)
            "supabase/config.toml": "supabase",
            "types/supabase.ts": "supabase",
            "types/database.types.ts": "supabase",
            "src/supabase.js": "supabase_config",
            "src/supabase.ts": "supabase_config",
            "src/config/supabase.js": "supabase_config",
            "src/config/supabase.ts": "supabase_config",
            "src/lib/supabase.js": "supabase_config",
            "src/lib/supabase.ts": "supabase_config",
            
            # Environment variable files
            ".env": "env_config",
            ".env.local": "env_config", 
            ".env.development": "env_config",
            ".env.production": "env_config",
            ".env.example": "env_example"r
    while maintaining compatibility with existing API
    """
    
    def __init__(self):
        self.intelligence_pipeline = IntelligencePipeline()
        self.stack_composer = create_stack_composer()
    
    async def analyze_repository_comprehensive(self, repo_url: str, deployment_id: str) -> Dict[str, Any]:
        """
        Run comprehensive repository analysis using Intelligence Pipeline + Stack Composer
        
        Returns enhanced analysis with:
        - intelligence_profile: Complete repo analysis (every file, every word)
        - stack_blueprint: Deployment-ready stack recommendation  
        - executive_summary: High-level project overview
        - legacy_format: Compatible with existing API
        """
        try:
            logger.info(f"🚀 Starting comprehensive analysis for {repo_url}")
            
            # Phase 1: Intelligence Pipeline - Deep repository analysis
            logger.info("📊 Phase 1: Intelligence Pipeline Analysis")
            pipeline_result = await self.intelligence_pipeline.analyze_repository(repo_url, deployment_id)
            
            if not pipeline_result["success"]:
                return {
                    "success": False,
                    "error": pipeline_result.get("error", "Analysis failed"),
                    "analysis_time_seconds": pipeline_result.get("analysis_time_seconds", 0)
                }
            
            # Extract intelligence profile
            intelligence_profile = pipeline_result["intelligence_profile"]
            local_repo_path = pipeline_result["local_repo_path"]
            
            # Phase 2: Stack Composer - Convert to deployment blueprint
            logger.info("🔧 Phase 2: Stack Blueprint Composition")
            
            # Check if blueprint already exists from framework detection stage
            existing_blueprint = pipeline_result.get("stack_blueprint")
            if existing_blueprint and existing_blueprint.get("services"):
                logger.info("✅ Using existing blueprint from framework detection stage")
                stack_blueprint = existing_blueprint
            else:
                logger.info("🔧 Creating blueprint via Stack Composer")
                stack_blueprint = self.stack_composer.compose_stack_blueprint(intelligence_profile)
            
            # Phase 3: Database Detection
            logger.info("🗄️ Phase 3: Database Requirements Detection")
            database_info = self._detect_database_requirements(local_repo_path)
            
            # Phase 4: Deployment Strategy Determination
            deployment_strategy = self._determine_deployment_strategy(
                intelligence_profile, stack_blueprint, database_info
            )
            requires_full_stack = self._requires_full_stack_deployment(stack_blueprint, database_info)
            
            # Phase 5: Executive Summary
            executive_summary = self._create_executive_summary(intelligence_profile, stack_blueprint)
            
            # Phase 6: Legacy format conversion
            legacy_analysis = self._convert_to_legacy_format(
                intelligence_profile, stack_blueprint, repo_url, deployment_id
            )
            
            # Create comprehensive response
            return {
                "success": True,
                "analysis_version": "2.0.0",
                "repository_url": repo_url,
                "deployment_id": deployment_id,
                "local_repo_path": local_repo_path,
                
                # Complete Intelligence Profile (every file, every word)
                "intelligence_profile": intelligence_profile,
                
                # Stack Blueprint (deployment-ready recommendation)
                "stack_blueprint": stack_blueprint,
                
                # Database Detection Results
                "database_info": database_info,
                "deployment_strategy": deployment_strategy,
                "requires_full_stack": requires_full_stack,
                
                # Executive Summary (high-level overview)
                "executive_summary": executive_summary,
                
                # Legacy compatibility
                "framework": legacy_analysis["framework"],
                "analysis": legacy_analysis["analysis"],
                "enhancements": legacy_analysis["enhancements"],
                "validation": legacy_analysis["validation"],
                
                # Frontend compatibility - add projectType field expected by frontend
                "projectType": self._get_frontend_project_type(stack_blueprint),
                
                # Metadata
                "analysis_time_seconds": pipeline_result["analysis_time_seconds"],
                "analyzer_version": "2.0.0-intelligence-pipeline-stack-composer",
                "features": {
                    "deep_crawl": True,
                    "secret_detection": True,
                    "stack_recommendation": True,
                    "deployment_ready": True
                }
            }
            
        except Exception as e:
            logger.error(f"💥 Enhanced analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "analyzer_version": "2.0.0-intelligence-pipeline"
            }
    
    def _get_frontend_project_type(self, stack_blueprint: Dict[str, Any]) -> str:
        """Convert framework name to frontend-expected projectType format"""
        if not stack_blueprint or not stack_blueprint.get("services"):
            return "unknown"
        
        primary_service = stack_blueprint["services"][0]
        framework_name = primary_service.get("framework", {}).get("name", "").lower()
        
        # Map framework names to frontend projectType values
        framework_mapping = {
            "flask": "flask",
            "django": "django", 
            "fastapi": "fastapi",
            "python": "python",
            "react": "react",
            "nextjs": "nextjs",
            "vue": "vue",
            "angular": "angular",
            "laravel": "laravel",
            "static-basic": "static",
            "static-site": "static"
        }
        
        return framework_mapping.get(framework_name, "unknown")
    
    def _convert_to_legacy_format(self, intelligence_profile: Dict[str, Any], 
                                 stack_blueprint: Dict[str, Any], repo_url: str, deployment_id: str) -> Dict[str, Any]:
        """Convert new format to legacy API format for compatibility"""
        
        # 🎯 SHORT-CIRCUIT: Handle Node.js monorepos/libraries specially
        frameworks = intelligence_profile.get("frameworks", [])
        if frameworks and frameworks[0].get("name") in ["nodejs-monorepo", "nodejs"]:
            intent = frameworks[0].get("intent", "unknown")
            if intent in ["library", "tooling"] or frameworks[0].get("name") == "nodejs-monorepo":
                return self._create_library_legacy_format(frameworks[0], intelligence_profile, repo_url, deployment_id)
        
        # Extract primary framework from stack blueprint
        primary_service = None
        if stack_blueprint and "services" in stack_blueprint:
            primary_service = stack_blueprint["services"][0] if stack_blueprint["services"] else None
        
        framework_info = {
            "type": primary_service["framework"]["name"] if primary_service else "unknown",
            "confidence": primary_service["framework"]["confidence"] if primary_service else 0.5,
            "config": self._build_legacy_config(primary_service) if primary_service else {}
        }
        
        # Extract file analysis
        file_intel = intelligence_profile.get("file_intelligence", {})
        crawl_stats = file_intel.get("crawl_stats", {})
        
        file_analysis = {
            "total_files": crawl_stats.get("files_analyzed", 0),
            "total_size": crawl_stats.get("total_size_bytes", 0),
            "file_types": crawl_stats.get("file_types", {}),
            "source_files": [],  # Simplified
            "static_files": []   # Simplified
        }
        
        # Build validation results
        validation = {
            "is_build_ready": True,  # Intelligence pipeline ensures this
            "missing_files": [],
            "present_files": [],
            "build_commands": primary_service.get("build", {}).get("commands", []) if primary_service else [],
            "build_output": primary_service.get("build", {}).get("artifact", ".") if primary_service else ".",
            "entry_point": primary_service.get("runtime", {}).get("entry") if primary_service else None
        }
        
        # Enhancements (new intelligence pipeline doesn't modify files)
        enhancements = {
            "files_created": [],
            "files_modified": [],
            "directories_created": [],
            "smart_fixes": [{
                "type": "intelligence_analysis",
                "reason": "Used comprehensive Intelligence Pipeline for analysis"
            }]
        }
        
        return {
            "framework": framework_info,
            "analysis": file_analysis,
            "validation": validation,
            "enhancements": enhancements
        }
    
    def _build_legacy_config(self, service: Dict[str, Any]) -> Dict[str, Any]:
        """Build legacy config format from service definition"""
        framework_name = service["framework"]["name"]
        
        # Map to legacy config format
        if framework_name == "laravel":
            return {
                "required_files": ["composer.json", "artisan"],
                "build_commands": service.get("build", {}).get("commands", ["composer install"]),
                "build_output": ".",
                "entry_point": None
            }
        elif framework_name in ["react", "nextjs", "vue"]:
            return {
                "required_files": ["package.json"],
                "build_commands": service.get("build", {}).get("commands", ["npm install", "npm run build"]),
                "build_output": service.get("build", {}).get("artifact", "build"),
                "entry_point": "index.html"
            }
        elif framework_name in ["flask", "django", "fastapi"]:
            # Python frameworks - determine entry point based on framework
            if framework_name == "flask":
                entry_point = "app.py"  # Common Flask entry point
            elif framework_name == "django":
                entry_point = "manage.py"  # Django management script
            elif framework_name == "fastapi":
                entry_point = "main.py"  # Common FastAPI entry point
            else:
                entry_point = "app.py"  # Default for Python apps
                
            return {
                "required_files": ["requirements.txt"],
                "build_commands": service.get("build", {}).get("commands", ["pip install -r requirements.txt"]),
                "build_output": ".",
                "entry_point": entry_point
            }
        else:
            return {
                "required_files": [],
                "build_commands": [],
                "build_output": ".",
                "entry_point": None  # Don't assume index.html for unknown frameworks
            }
    
    def _create_executive_summary(self, intelligence_profile: Dict[str, Any], 
                                stack_blueprint: Dict[str, Any]) -> Dict[str, Any]:
        """📋 Create executive summary of analysis and recommendations"""
        
        # Get data from file intelligence instead of missing summary
        file_intel = intelligence_profile.get("file_intelligence", {})
        crawl_stats = file_intel.get("crawl_stats", {})
        frameworks = intelligence_profile.get("frameworks", [])
        stack_class = intelligence_profile.get("stack_classification", {})
        recommendation = stack_blueprint.get("final_recommendation", {})
        services = stack_blueprint.get("services", [])
        risks = stack_blueprint.get("security_risks", [])
        
        # 🎯 SHORT-CIRCUIT: Handle Node.js monorepos/libraries specially
        if frameworks and frameworks[0].get("name") in ["nodejs-monorepo", "nodejs"]:
            intent = frameworks[0].get("intent", "unknown")
            if intent in ["library", "tooling"] or frameworks[0].get("name") == "nodejs-monorepo":
                return self._create_library_summary(frameworks[0], crawl_stats, intent)
        
        # Calculate analysis stats from actual crawl data
        total_files = crawl_stats.get("files_analyzed", 0)
        total_size = crawl_stats.get("total_size_bytes", 0)
        languages = crawl_stats.get("languages_detected", [])
        
        # Determine primary language with better logic based on framework context
        # Weight by code directory bytes, exclude minified/vendor assets
        filtered_languages = []
        for lang in languages:
            # Skip minified or vendor-heavy languages for better accuracy
            if lang not in ["Minified", "Vendor", "Generated"]:
                filtered_languages.append(lang)
        
        if frameworks and frameworks[0].get("name") == "laravel":
            primary_language = "PHP"  # Laravel is always PHP-based
        elif frameworks and frameworks[0].get("name") in ["django", "flask", "fastapi", "python"]:
            primary_language = "Python"  # Python frameworks
        elif frameworks and frameworks[0].get("name") == "angular":
            primary_language = "TypeScript"  # Angular apps use TypeScript primarily
        elif frameworks and frameworks[0].get("name") == "react":
            primary_language = "React JSX"  # React apps use JSX primarily
        elif frameworks and frameworks[0].get("name") in ["nodejs", "nodejs-monorepo", "create-react-app", "react-vite", "nextjs"]:
            primary_language = "JavaScript"  # Node.js based projects
        elif frameworks and frameworks[0].get("name") == "static-basic":
            primary_language = "HTML/CSS/JS"  # Static sites are HTML/CSS/JS-based
        elif "TypeScript" in filtered_languages:
            primary_language = "TypeScript"
        elif "React JSX" in filtered_languages:
            primary_language = "React JSX"
        elif "PHP" in filtered_languages and stack_class.get("type") != "static-site":
            primary_language = "PHP"
        elif "Python" in filtered_languages:
            primary_language = "Python"
        elif "HTML" in filtered_languages and stack_class.get("type") == "static-site":
            primary_language = "HTML/CSS/JS"  # Group for static sites
        elif "JavaScript" in filtered_languages:
            primary_language = "JavaScript"
        elif "CSS" in filtered_languages:
            primary_language = "CSS"
        elif filtered_languages:
            primary_language = filtered_languages[0]
        else:
            primary_language = "Unknown"
        
        # Extract top frameworks
        top_frameworks = sorted(frameworks, key=lambda x: x.get("confidence", 0), reverse=True)[:3]
        
        # Risk assessment
        high_risks = [r for r in risks if r.get("severity") == "high"]
        
        # Determine project type from stack classification and frameworks with better detection
        if stack_class.get("type") == "php-laravel":
            project_type = "Laravel Web Application"
        elif stack_class.get("type") == "static-site":
            project_type = "Static Website"
        elif frameworks:
            fw_name = frameworks[0].get("name", "")
            if fw_name == "static-basic":
                project_type = "Static Website"
            elif fw_name == "laravel":
                project_type = "Laravel Web Application"
            elif fw_name == "nodejs-monorepo":
                project_type = "Node.js Monorepo (Library/Tooling)"
            elif fw_name == "nodejs":
                project_type = "Node.js Application"
            elif fw_name == "create-react-app":
                project_type = "Create React App"
            elif fw_name == "react-vite":
                project_type = "React Vite Application"
            elif fw_name == "nextjs":
                project_type = "Next.js Application"
            elif fw_name == "react":
                variant = frameworks[0].get("variant", "")
                if variant == "nextjs":
                    project_type = "Next.js Application"
                elif variant == "vite":
                    project_type = "React Vite Application"
                elif variant == "create-react-app":
                    project_type = "Create React App"
                else:
                    project_type = "React Application"
            elif fw_name in ["vue", "angular"]:
                project_type = f"{fw_name.title()} Application"
            else:
                project_type = f"{fw_name.title()} Application"
        elif primary_language == "HTML/CSS/JS":
            project_type = "Static Website"
        elif primary_language == "HTML":
            project_type = "Static Website"
        elif primary_language == "JavaScript":
            project_type = "JavaScript Application"
        elif primary_language == "PHP" and stack_class.get("type") != "static-site":
            project_type = "PHP Web Application"
        else:
            project_type = f"{primary_language} Project" if primary_language != "Unknown" else "Web Project"
        
        return {
            "project_type": project_type,
            "primary_technology": primary_language,
            "architecture_pattern": "Monolith" if len(services) <= 1 else "Multi-Service",
            "deployment_ready": intelligence_profile.get("ready_to_deploy", False),
            "key_insights": [
                f"Analyzed {total_files} files ({total_size/1024/1024:.1f} MB)",
                f"Primary technology: {primary_language}",
                f"Framework confidence: {top_frameworks[0].get('confidence', 0):.0%}" if frameworks else "No framework detected",
                f"Services required: {len(services)}",
                f"Stack type: {stack_class.get('type', 'Unknown').replace('-', ' ').title()}"
            ],
            "frameworks_detected": len(frameworks),
            "services_count": len(services),
            "deployment_target": stack_blueprint.get("deployment_targets", {}).get("preferred", "aws"),
            "security_risks": len(risks),
            "estimated_cost": intelligence_profile.get("estimated_monthly_cost", "Unknown")
        }
    
    def _create_library_summary(self, framework: Dict[str, Any], crawl_stats: Dict[str, Any], intent: str) -> Dict[str, Any]:
        """📋 Create executive summary for library/tooling repositories"""
        total_files = crawl_stats.get("files_analyzed", 0)
        total_size = crawl_stats.get("total_size_bytes", 0)
        
        project_type_map = {
            "tooling": "Node.js Monorepo (Library/Tooling)",
            "library": "Node.js Library",
            "nodejs-monorepo": "Node.js Monorepo (Library/Tooling)"
        }
        
        return {
            "project_type": project_type_map.get(intent, "Node.js Monorepo"),
            "primary_technology": "JavaScript",
            "architecture_pattern": "Monorepo" if framework.get("name") == "nodejs-monorepo" else "Library",
            "deployment_ready": False,  # Libraries/tooling aren't deployable
            "key_insights": [
                f"Analyzed {total_files} files ({total_size/1024/1024:.1f} MB)",
                f"Primary technology: JavaScript",
                f"Framework confidence: {framework.get('confidence', 0):.0%}",
                "No app build target - library/tooling repository",
                f"Detected as {intent} repository, not a deployable application"
            ],
            "frameworks_detected": 1,
            "services_count": 0,  # No deployable services
            "deployment_target": "n/a", 
            "security_risks": 0,
            "estimated_cost": "n/a"
        }
    
    def _create_library_legacy_format(self, framework: Dict[str, Any], intelligence_profile: Dict[str, Any], repo_url: str, deployment_id: str) -> Dict[str, Any]:
        """Create legacy format for library/tooling repositories"""
        file_intel = intelligence_profile.get("file_intelligence", {})
        crawl_stats = file_intel.get("crawl_stats", {})
        intent = framework.get("intent", "unknown")
        
        return {
            "success": True,
            "repository_url": repo_url,
            "deployment_id": deployment_id,
            "framework": {
                "type": framework.get("name", "nodejs-monorepo"),
                "confidence": framework.get("confidence", 0.95),
                "config": {}
            },
            "file_analysis": {
                "total_files": crawl_stats.get("files_analyzed", 0),
                "total_size": crawl_stats.get("total_size_bytes", 0),
                "file_types": crawl_stats.get("file_types", {}),
                "source_files": [],
                "static_files": []
            },
            "validation": {
                "is_build_ready": False,  # Libraries aren't build-ready for deployment
                "missing_files": [],
                "present_files": [],
                "build_commands": [],
                "build_output": None,
                "entry_point": None
            },
            "analysis": {
                "total_files": crawl_stats.get("files_analyzed", 0),
                "total_size": crawl_stats.get("total_size_bytes", 0),
                "file_types": crawl_stats.get("file_types", {}),
                "source_files": [],
                "static_files": []
            },
            "enhancements": {
                "files_created": [],
                "files_modified": [],
                "suggestions": [f"This is a {intent} repository, not a deployable application"]
            },
            "features": intelligence_profile.get("features", {}),
            "analyzer_version": "2.0.0-intelligence-pipeline-stack-composer",
            "analysis_time_seconds": intelligence_profile.get("analysis_time_seconds", 0)
        }
    
    def _estimate_deployment_cost(self, stack_blueprint: Dict[str, Any]) -> str:
        """💰 Estimate monthly deployment cost"""
        services = stack_blueprint.get("services", [])
        
        # Simple cost estimation based on services
        cost = 0
        for service in services:
            role = service.get("role", "")
            if role == "backend-api":
                cost += 50  # EC2 instance
            elif role == "database":
                cost += 30  # RDS
            elif role == "web-frontend":
                cost += 10  # S3 + CloudFront
        
        # Shared resources
        shared = stack_blueprint.get("shared_resources", {})
        if shared.get("object_storage"):
            cost += 5
        if shared.get("cdn"):
            cost += 10
        
        if cost < 30:
            return "Low ($10-30/month)"
        elif cost < 100:
            return "Medium ($30-100/month)"
        else:
            return "High ($100+/month)"
    
    def _estimate_deployment_time(self, stack_blueprint: Dict[str, Any]) -> str:
        """⏱️ Estimate deployment time"""
        services_count = len(stack_blueprint.get("services", []))
        
        if services_count <= 1:
            return "5-10 minutes"
        elif services_count <= 3:
            return "10-20 minutes"
        else:
            return "20-30 minutes"
    
    def _calculate_readiness_score(self, intelligence_profile: Dict[str, Any], 
                                 stack_blueprint: Dict[str, Any]) -> float:
        """📊 Calculate overall deployment readiness score (0-1)"""
        
        factors = []
        
        # Framework confidence
        frameworks = intelligence_profile.get("frameworks", [])
        if frameworks:
            max_confidence = max(f.get("confidence", 0) for f in frameworks)
            factors.append(max_confidence)
        
        # Deployment complexity (simpler = higher score)
        services_count = len(stack_blueprint.get("services", []))
        complexity_score = max(0.5, 1.0 - (services_count - 1) * 0.1)
        factors.append(complexity_score)
        
        # Security posture
        risks = stack_blueprint.get("security_risks", [])
        high_risks = [r for r in risks if r.get("severity") == "high"]
        security_score = 0.3 if high_risks else 0.8 if risks else 1.0
        factors.append(security_score)
        
        # Code quality (based on structure and size)
        summary = intelligence_profile.get("summary", {})
        lines_of_code = summary.get("lines_of_code", 0)
        quality_score = min(1.0, lines_of_code / 10000)  # Normalize by 10k LOC
        factors.append(quality_score)
        
        # Calculate weighted average
        return sum(factors) / len(factors) if factors else 0.5
    
    def get_analyzer_capabilities(self) -> Dict[str, Any]:
        """Get comprehensive analyzer capabilities"""
        return self.intelligence_pipeline.get_pipeline_info()

    def _detect_database_requirements(self, local_repo_path: str) -> Dict[str, Any]:
        """🗄️ Detect database requirements and configuration"""
        import os
        from pathlib import Path
        
        repo_path = Path(local_repo_path)
        database_info = {
            "detected": False,
            "database_types": [],
            "config_files": [],
            "packages": [],
            "orm_frameworks": [],
            "migration_tools": [],
            "deployment_strategy": "none"
        }
        
        # Database configuration file indicators
        db_config_files = {
            "prisma/schema.prisma": "postgresql",     # Prisma ORM
            "database.json": "generic",               # Database migrations
            "knexfile.js": "generic",                 # Knex.js
            "sequelize.config.js": "generic",         # Sequelize
            "typeorm.config.js": "generic",           # TypeORM
            "drizzle.config.js": "generic",           # Drizzle ORM
            ".env": "env_vars",                       # Environment variables
            ".env.example": "env_vars",               # Environment template
            "docker-compose.yml": "containerized",    # Docker database
            "docker-compose.yaml": "containerized",   # Docker database
            
            # 🔥 Firebase configuration files (CLIENT-SIDE)
            "firebase.json": "firestore",
            ".firebaserc": "firestore",
            "firestore.rules": "firestore_security",
            "firestore.indexes.json": "firestore",
            "firebase.config.js": "firestore",
            "firebase.config.ts": "firestore",
            
            # 🟦 Supabase configuration files (CLIENT-SIDE)
            "supabase/config.toml": "supabase",
            "types/supabase.ts": "supabase",
            "types/database.types.ts": "supabase"
        }
        
        # Check for database config files
        for config_file, db_type in db_config_files.items():
            config_path = repo_path / config_file
            if config_path.exists():
                database_info["config_files"].append(config_file)
                
                # 🔒 SECURITY VALIDATION for BaaS config files
                if db_type == "firestore_security":
                    # Validate Firestore security rules exist
                    database_info["security_validations"] = database_info.get("security_validations", [])
                    database_info["security_validations"].append({
                        "type": "firestore_rules_found",
                        "file": config_file,
                        "status": "requires_review",
                        "message": "Firestore security rules found - MUST be validated before deployment"
                    })
                elif db_type == "supabase":
                    # Check for Supabase RLS indicators
                    database_info["security_validations"] = database_info.get("security_validations", [])
                    database_info["security_validations"].append({
                        "type": "supabase_config_found", 
                        "file": config_file,
                        "status": "requires_rls_check",
                        "message": "Supabase config found - RLS (Row Level Security) MUST be verified"
                    })
                elif db_type == "firestore_config":
                    # 🔥 Extract Firebase configuration from source files
                    firebase_config = self._extract_firebase_config(config_path)
                    if firebase_config:
                        database_info["firebase_config"] = firebase_config
                        database_info["auto_config_detected"] = True
                        database_info["config_source"] = f"extracted_from_{config_file}"
                        
                        # 🎯 NEW: Check for local data fallback
                        print(f"🔍 Checking for local data fallback in: {repo_path}")
                        local_fallback = self._detect_local_data_fallback(repo_path)
                        if local_fallback:
                            database_info["local_data_fallback"] = local_fallback
                            database_info["deployment_strategy"] = "firebase_with_local_fallback"
                            print(f"✅ Local data fallback detected: {local_fallback['file']}")
                        else:
                            print(f"❌ No local data fallback found in {repo_path}")
                            database_info["deployment_strategy"] = "firebase_only"
                elif db_type == "supabase_config":
                    # 🟦 Extract Supabase configuration from source files  
                    supabase_config = self._extract_supabase_config(config_path)
                    if supabase_config:
                        database_info["supabase_config"] = supabase_config
                        database_info["auto_config_detected"] = True
                        database_info["config_source"] = f"extracted_from_{config_file}"
                elif db_type == "env_config":
                    # 🌍 Extract environment variables for Firebase/Supabase
                    env_vars = self._extract_env_variables(config_path)
                    if env_vars:
                        database_info["env_variables"] = env_vars
                        database_info["env_source"] = config_file
                
                if db_type not in database_info["database_types"] and db_type not in ["env_vars", "containerized", "firestore_security"]:
                    database_info["database_types"].append(db_type)
                database_info["detected"] = True
        
        # Check package.json for database-related packages
        package_json_path = repo_path / "package.json"
        if package_json_path.exists():
            try:
                import json
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                
                # Database packages mapping
                db_packages = {
                    # ORMs and Query Builders
                    "prisma": {"type": "postgresql", "category": "orm"},
                    "@prisma/client": {"type": "postgresql", "category": "orm"},
                    "mongoose": {"type": "mongodb", "category": "orm"},
                    "sequelize": {"type": "generic", "category": "orm"},
                    "typeorm": {"type": "generic", "category": "orm"},
                    "drizzle-orm": {"type": "generic", "category": "orm"},
                    "knex": {"type": "generic", "category": "query_builder"},
                    
                    # Database drivers
                    "pg": {"type": "postgresql", "category": "driver"},
                    "postgres": {"type": "postgresql", "category": "driver"},
                    "mysql2": {"type": "mysql", "category": "driver"},
                    "mysql": {"type": "mysql", "category": "driver"},
                    "mongodb": {"type": "mongodb", "category": "driver"},
                    "sqlite3": {"type": "sqlite", "category": "driver"},
                    "better-sqlite3": {"type": "sqlite", "category": "driver"},
                    
                    # Migration tools
                    "db-migrate": {"type": "generic", "category": "migration"},
                    "migrate": {"type": "generic", "category": "migration"},
                    "umzug": {"type": "generic", "category": "migration"},
                    
                    # 🔥 Firebase/Firestore packages (CLIENT-SIDE ONLY)
                    "firebase": {"type": "firestore", "category": "baas_client", "security_level": "public"},
                    "@firebase/app": {"type": "firestore", "category": "baas_client", "security_level": "public"},
                    "@firebase/firestore": {"type": "firestore", "category": "baas_client", "security_level": "public"},
                    "@firebase/auth": {"type": "firestore_auth", "category": "auth_client", "security_level": "public"},
                    "@firebase/storage": {"type": "firestore_storage", "category": "storage_client", "security_level": "public"},
                    "react-firebase-hooks": {"type": "firestore", "category": "react_integration", "security_level": "public"},
                    
                    # 🚨 Firebase ADMIN packages (SHOULD NOT BE IN CLIENT APPS)
                    "firebase-admin": {"type": "firestore_admin", "category": "baas_admin", "security_level": "DANGER_ADMIN"},
                    "firebase-tools": {"type": "firestore_tools", "category": "cli", "security_level": "dev_tools"},
                    
                    # 🟦 Supabase packages (CLIENT-SIDE ONLY)
                    "@supabase/supabase-js": {"type": "supabase", "category": "baas_client", "security_level": "public"},
                    "@supabase/auth-helpers-react": {"type": "supabase_auth", "category": "auth_client", "security_level": "public"},
                    "@supabase/auth-helpers-nextjs": {"type": "supabase_auth", "category": "auth_client", "security_level": "public"},
                    "@supabase/realtime-js": {"type": "supabase_realtime", "category": "realtime_client", "security_level": "public"},
                    "@supabase/postgrest-js": {"type": "supabase_db", "category": "query_builder", "security_level": "public"},
                    
                    # 🚨 Supabase CLI/Admin tools (SHOULD NOT BE IN CLIENT APPS)
                    "supabase": {"type": "supabase_cli", "category": "cli", "security_level": "dev_tools"}
                }
                
                # Check dependencies and devDependencies
                all_deps = {}
                all_deps.update(package_data.get("dependencies", {}))
                all_deps.update(package_data.get("devDependencies", {}))
                
                for package_name, version in all_deps.items():
                    if package_name in db_packages:
                        package_info = db_packages[package_name]
                        
                        # 🚨 SECURITY CHECK: Detect dangerous admin packages in client apps
                        security_level = package_info.get("security_level", "unknown")
                        if security_level == "DANGER_ADMIN":
                            logger.warning(f"🚨 SECURITY RISK: Admin package '{package_name}' detected in client app!")
                            database_info["security_warnings"] = database_info.get("security_warnings", [])
                            database_info["security_warnings"].append({
                                "type": "admin_package_in_client",
                                "package": package_name,
                                "severity": "HIGH",
                                "message": f"Admin package '{package_name}' should not be in client-side React apps"
                            })
                        
                        database_info["packages"].append({
                            "name": package_name,
                            "version": version,
                            "type": package_info["type"],
                            "category": package_info["category"],
                            "security_level": security_level
                        })
                        
                        if package_info["type"] not in database_info["database_types"]:
                            database_info["database_types"].append(package_info["type"])
                        
                        if package_info["category"] in ["orm", "baas_client"]:
                            database_info["orm_frameworks"].append(package_name)
                        elif package_info["category"] == "migration":
                            database_info["migration_tools"].append(package_name)
                        
                        database_info["detected"] = True
                        
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Could not parse package.json: {e}")
        
        # Check Python requirements for database packages (for full-stack React+Python)
        requirements_files = ["requirements.txt", "requirements-dev.txt", "pyproject.toml"]
        for req_file in requirements_files:
            req_path = repo_path / req_file
            if req_path.exists():
                try:
                    content = req_path.read_text(encoding='utf-8')
                    python_db_packages = [
                        "django", "flask-sqlalchemy", "sqlalchemy", "psycopg2", 
                        "pymongo", "mysql-connector", "sqlite3"
                    ]
                    
                    for db_package in python_db_packages:
                        if db_package in content.lower():
                            database_info["packages"].append({
                                "name": db_package,
                                "language": "python",
                                "type": "backend_api"
                            })
                            database_info["detected"] = True
                            
                except Exception as e:
                    logger.warning(f"Could not parse {req_file}: {e}")
        
        # Determine deployment strategy
        if database_info["detected"]:
            if database_info["config_files"]:
                if "docker-compose.yml" in database_info["config_files"] or "docker-compose.yaml" in database_info["config_files"]:
                    database_info["deployment_strategy"] = "containerized"
                elif database_info["orm_frameworks"]:
                    database_info["deployment_strategy"] = "managed_database"
                else:
                    database_info["deployment_strategy"] = "basic_database"
            else:
                database_info["deployment_strategy"] = "inferred_database"
        
        return database_info

    def _extract_firebase_config(self, config_file_path):
        """
        🔥 Extract Firebase configuration from JavaScript/TypeScript files
        NEW: Enhanced with local data fallback detection
        """
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            firebase_config = {}
            
            # Look for environment variable patterns
            env_patterns = {
                'apiKey': [r'VITE_API_KEY', r'REACT_APP_FIREBASE_API_KEY', r'FIREBASE_API_KEY'],
                'authDomain': [r'VITE_AUTH_DOMAIN', r'REACT_APP_FIREBASE_AUTH_DOMAIN', r'FIREBASE_AUTH_DOMAIN'],
                'projectId': [r'VITE_PROJECT_ID', r'REACT_APP_FIREBASE_PROJECT_ID', r'FIREBASE_PROJECT_ID'],
                'storageBucket': [r'VITE_STORAGE_BUCKET', r'REACT_APP_FIREBASE_STORAGE_BUCKET', r'FIREBASE_STORAGE_BUCKET'],
                'messagingSenderId': [r'VITE_MESSAGING_ID', r'REACT_APP_FIREBASE_MESSAGING_SENDER_ID', r'FIREBASE_MESSAGING_SENDER_ID'],
                'appId': [r'VITE_APP_ID', r'REACT_APP_FIREBASE_APP_ID', r'FIREBASE_APP_ID'],
                'measurementId': [r'VITE_MEASUREMENT_ID', r'REACT_APP_FIREBASE_MEASUREMENT_ID', r'FIREBASE_MEASUREMENT_ID']
            }
            
            # Extract environment variable references
            for config_key, env_vars in env_patterns.items():
                for env_var in env_vars:
                    if env_var in content:
                        firebase_config[config_key] = f"${{{env_var}}}"  # Mark as environment variable
                        break
            
            # Also look for hardcoded values (less secure but possible)
            import re
            hardcoded_patterns = {
                'apiKey': r'apiKey[:\s]*["\']([^"\']+)["\']',
                'authDomain': r'authDomain[:\s]*["\']([^"\']+)["\']',
                'projectId': r'projectId[:\s]*["\']([^"\']+)["\']',
                'storageBucket': r'storageBucket[:\s]*["\']([^"\']+)["\']',
                'messagingSenderId': r'messagingSenderId[:\s]*["\']([^"\']+)["\']',
                'appId': r'appId[:\s]*["\']([^"\']+)["\']'
            }
            
            for config_key, pattern in hardcoded_patterns.items():
                if config_key not in firebase_config:  # Only if not found as env var
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        firebase_config[config_key] = match.group(1)
            
            return firebase_config if firebase_config else None
            
        except Exception as e:
            print(f"Error extracting Firebase config from {config_file_path}: {e}")
            return None

    def _detect_local_data_fallback(self, repo_path: Path) -> Dict[str, Any]:
        """
        🎯 NEW: Detect local data files that can be used as Firebase fallback
        """
        print(f"🔍 Looking for local data patterns in: {repo_path}")
        local_data_patterns = [
            "src/data/products.js", "src/data/all-products.js", "src/data/data.js",
            "src/assets/data.js", "data/products.json", "src/mock/products.js",
            "src/data/products.json", "public/data/products.json"
        ]
        
        for pattern in local_data_patterns:
            data_path = repo_path / pattern
            print(f"🔍 Checking pattern: {pattern} -> {data_path} (exists: {data_path.exists()})")
            if data_path.exists():
                try:
                    # Try to read and validate the data file
                    content = data_path.read_text(encoding='utf-8')
                    
                    # Check if it contains product-like data
                    indicators = ['product', 'item', 'name', 'price', 'id', 'category']
                    content_lower = content.lower()
                    
                    if any(indicator in content_lower for indicator in indicators):
                        result = {
                            "file": pattern,
                            "path": str(data_path),
                            "type": "local_products_data",
                            "size": len(content),
                            "contains_products": True
                        }
                        print(f"✅ Found local data file: {result}")
                        return result
                except Exception as e:
                    print(f"⚠️ Error reading local data file {pattern}: {e}")
                    continue
        
        print(f"❌ No local data files found")
        return None

    def _extract_supabase_config(self, config_file_path):
        """
        🟦 Extract Supabase configuration from JavaScript/TypeScript files
        """
        try:
            with open(config_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            supabase_config = {}
            
            # Look for environment variable patterns
            env_patterns = {
                'url': [r'VITE_SUPABASE_URL', r'REACT_APP_SUPABASE_URL', r'SUPABASE_URL'],
                'anonKey': [r'VITE_SUPABASE_ANON_KEY', r'REACT_APP_SUPABASE_ANON_KEY', r'SUPABASE_ANON_KEY']
            }
            
            # Extract environment variable references
            for config_key, env_vars in env_patterns.items():
                for env_var in env_vars:
                    if env_var in content:
                        supabase_config[config_key] = f"${{{env_var}}}"  # Mark as environment variable
                        break
            
            # Look for hardcoded values
            import re
            hardcoded_patterns = {
                'url': r'["\']https://[a-zA-Z0-9-]+\.supabase\.co["\']',
                'anonKey': r'["\']eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*["\']'  # JWT pattern
            }
            
            for config_key, pattern in hardcoded_patterns.items():
                if config_key not in supabase_config:  # Only if not found as env var
                    match = re.search(pattern, content)
                    if match:
                        supabase_config[config_key] = match.group(0).strip('"\'')
            
            return supabase_config if supabase_config else None
            
        except Exception as e:
            print(f"Error extracting Supabase config from {config_file_path}: {e}")
            return None

    def _extract_env_variables(self, env_file_path):
        """
        🌍 Extract environment variables from .env files
        """
        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            env_vars = {}
            
            # Parse .env file format
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    
                    # Only capture Firebase/Supabase related variables
                    if any(pattern in key.upper() for pattern in [
                        'FIREBASE', 'VITE_API_KEY', 'VITE_AUTH_DOMAIN', 'VITE_PROJECT_ID',
                        'VITE_STORAGE_BUCKET', 'VITE_MESSAGING_ID', 'VITE_APP_ID', 'VITE_MEASUREMENT_ID',
                        'SUPABASE', 'VITE_SUPABASE'
                    ]):
                        env_vars[key] = value
            
            return env_vars if env_vars else None
            
        except Exception as e:
            print(f"Error extracting env variables from {env_file_path}: {e}")
            return None

    def _determine_deployment_strategy(self, intelligence_profile: Dict[str, Any], 
                                     stack_blueprint: Dict[str, Any], 
                                     database_info: Dict[str, Any]) -> str:
        """🎯 Determine optimal deployment strategy for React applications"""
        
        services = stack_blueprint.get("services", [])
        
        # Check for React frontend
        has_react = any(
            service.get("role") == "web-frontend" and 
            "react" in service.get("framework", {}).get("name", "").lower()
            for service in services
        )
        
        # Check for backend API
        has_backend = any(
            service.get("role") == "backend-api" 
            for service in services
        )
        
        # Check for database requirements
        has_database = database_info.get("detected", False)
        
        # Determine strategy
        if has_react and has_database and has_backend:
            return "full_stack_with_api"
        elif has_react and has_database:
            return "full_stack_simple"
        elif has_react and has_backend:
            return "frontend_with_api"
        elif has_react:
            return "frontend_only"
        elif has_backend and has_database:
            return "backend_only"
        else:
            return "static_site"

    def _requires_full_stack_deployment(self, stack_blueprint: Dict[str, Any], 
                                       database_info: Dict[str, Any]) -> bool:
        """🔍 Check if deployment requires orchestrated full-stack approach"""
        deployment_strategy = self._determine_deployment_strategy({}, stack_blueprint, database_info)
        return deployment_strategy in ["full_stack_with_api", "full_stack_simple"]

# Create singleton instance
enhanced_analyzer = EnhancedRepositoryAnalyzer()
