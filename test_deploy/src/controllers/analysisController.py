"""
Analysis Controller for CodeFlowOps
Handles repository analysis, project type detection, and deployment configuration
"""

import logging
import asyncio
import tempfile
import shutil
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import yaml

from ..config.env import get_settings
from ..utils.validators import validate_github_access, extract_github_info

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalysisController:
    """
    Controller for analyzing GitHub repositories and generating deployment configurations
    """
    
    def __init__(self):
        self.supported_frameworks = {
            "react": {
                "indicators": ["package.json", "src/App.js", "src/App.tsx", "public/index.html"],
                "build_commands": ["npm install", "npm run build"],
                "build_output": "build",
                "deployment_type": "static"
            },
            "vue": {
                "indicators": ["package.json", "src/main.js", "src/App.vue", "public/index.html"],
                "build_commands": ["npm install", "npm run build"],
                "build_output": "dist",
                "deployment_type": "static"
            },
            "angular": {
                "indicators": ["package.json", "angular.json", "src/main.ts", "src/app/app.component.ts"],
                "build_commands": ["npm install", "npm run build"],
                "build_output": "dist",
                "deployment_type": "static"
            },
            "nextjs": {
                "indicators": ["package.json", "next.config.js", "pages", "app"],
                "build_commands": ["npm install", "npm run build"],
                "build_output": ".next",
                "deployment_type": "serverless"
            },
            "gatsby": {
                "indicators": ["package.json", "gatsby-config.js", "src/pages"],
                "build_commands": ["npm install", "npm run build"],
                "build_output": "public",
                "deployment_type": "static"
            },
            "svelte": {
                "indicators": ["package.json", "rollup.config.js", "src/App.svelte"],
                "build_commands": ["npm install", "npm run build"],
                "build_output": "public",
                "deployment_type": "static"
            },
            "static": {
                "indicators": ["index.html", "*.html"],
                "build_commands": [],
                "build_output": ".",
                "deployment_type": "static"
            }
        }
    
    async def analyze_repository(
        self,
        github_url: str,
        session_id: str,
        validation_data: Dict[str, Any],
        languages_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze GitHub repository to determine project type and configuration
        
        Args:
            github_url: GitHub repository URL
            session_id: Session identifier
            validation_data: Repository validation information
            languages_data: Programming languages information
            
        Returns:
            Analysis results
        """
        try:
            logger.info(f"Analyzing repository {github_url} for session {session_id}")
            
            # Extract repository information
            owner = validation_data.get("owner")
            repo = validation_data.get("repo")
            
            if not owner or not repo:
                return {
                    "success": False,
                    "error": "Invalid repository information"
                }
            
            # Clone repository for analysis (in a real implementation)
            # For now, we'll use GitHub API to get file structure
            repository_structure = await self._get_repository_structure(owner, repo)
            
            # Detect project type
            project_detection = await self._detect_project_type(repository_structure, languages_data)
            
            # Analyze dependencies
            dependencies_analysis = await self._analyze_dependencies(owner, repo, project_detection)
            
            # Generate build configuration
            build_config = await self._generate_build_configuration(project_detection, dependencies_analysis)
            
            # Estimate deployment resources
            resource_estimation = await self._estimate_deployment_resources(
                project_detection,
                dependencies_analysis,
                repository_structure
            )
            
            # Compile analysis results
            analysis_results = {
                "project_type": project_detection["type"],
                "framework": project_detection["framework"],
                "confidence": project_detection["confidence"],
                "languages": languages_data.get("languages", {}),
                "primary_language": languages_data.get("primary_language"),
                "dependencies": dependencies_analysis,
                "build_config": build_config,
                "deployment_config": {
                    "type": project_detection["deployment_type"],
                    "estimated_resources": resource_estimation
                },
                "repository_info": {
                    "owner": owner,
                    "repo": repo,
                    "size": validation_data.get("size", 0),
                    "is_private": validation_data.get("is_private", False),
                    "default_branch": validation_data.get("default_branch", "main")
                },
                "analysis_metadata": {
                    "session_id": session_id,
                    "github_url": github_url,
                    "structure_files_count": len(repository_structure),
                    "detected_files": project_detection.get("detected_files", [])
                }
            }
            
            return {
                "success": True,
                "data": analysis_results
            }
            
        except Exception as e:
            logger.error(f"Repository analysis failed for {github_url}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _get_repository_structure(self, owner: str, repo: str) -> List[str]:
        """
        Get repository file structure using GitHub API
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of file paths in the repository
        """
        try:
            import httpx
            
            # GitHub API URL for repository contents
            api_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CodeFlowOps/1.0"
            }
            
            if settings.GITHUB_TOKEN:
                headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_url, headers=headers)
            
            if response.status_code == 200:
                tree_data = response.json()
                files = []
                
                for item in tree_data.get("tree", []):
                    if item.get("type") == "blob":  # File (not directory)
                        files.append(item.get("path", ""))
                
                return files
            else:
                logger.warning(f"Failed to get repository structure: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Failed to get repository structure: {str(e)}")
            return []
    
    async def _detect_project_type(
        self,
        repository_structure: List[str],
        languages_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect project type and framework based on repository structure
        
        Args:
            repository_structure: List of file paths
            languages_data: Programming languages information
            
        Returns:
            Project detection results
        """
        try:
            detection_scores = {}
            detected_files = {}
            
            # Check each framework
            for framework, config in self.supported_frameworks.items():
                score = 0
                framework_files = []
                
                for indicator in config["indicators"]:
                    if indicator.endswith("*"):
                        # Wildcard matching
                        pattern = indicator[:-1]
                        matches = [f for f in repository_structure if f.startswith(pattern)]
                        if matches:
                            score += len(matches) * 0.5
                            framework_files.extend(matches[:3])  # Limit to first 3 matches
                    else:
                        # Exact file/directory matching
                        if indicator in repository_structure:
                            score += 1
                            framework_files.append(indicator)
                        # Check if it's a directory
                        elif any(f.startswith(indicator + "/") for f in repository_structure):
                            score += 1
                            framework_files.append(indicator + "/")
                
                if score > 0:
                    detection_scores[framework] = score
                    detected_files[framework] = framework_files
            
            # Language-based scoring adjustments
            primary_language = languages_data.get("primary_language", "").lower()
            languages = languages_data.get("languages", {})
            
            if "javascript" in languages or "typescript" in languages:
                # Boost JS/TS frameworks
                for framework in ["react", "vue", "angular", "nextjs", "gatsby", "svelte"]:
                    if framework in detection_scores:
                        detection_scores[framework] *= 1.5
            
            if "html" in languages:
                # Boost static site score
                if "static" in detection_scores:
                    detection_scores["static"] *= 1.2
            
            # Determine best match
            if detection_scores:
                best_framework = max(detection_scores, key=lambda x: detection_scores[x])
                best_score = detection_scores[best_framework]
                
                # Calculate confidence (normalize score)
                max_possible_score = len(self.supported_frameworks[best_framework]["indicators"])
                confidence = min(best_score / max_possible_score, 1.0)
                
                return {
                    "type": "frontend" if best_framework != "static" else "static",
                    "framework": best_framework,
                    "confidence": confidence,
                    "deployment_type": self.supported_frameworks[best_framework]["deployment_type"],
                    "detected_files": detected_files.get(best_framework, []),
                    "all_scores": detection_scores
                }
            else:
                # Fallback to static site
                return {
                    "type": "static",
                    "framework": "static",
                    "confidence": 0.3,
                    "deployment_type": "static",
                    "detected_files": [],
                    "all_scores": {}
                }
                
        except Exception as e:
            logger.error(f"Project type detection failed: {str(e)}")
            return {
                "type": "unknown",
                "framework": "unknown",
                "confidence": 0.0,
                "deployment_type": "static",
                "detected_files": [],
                "all_scores": {}
            }
    
    async def _analyze_dependencies(
        self,
        owner: str,
        repo: str,
        project_detection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze project dependencies
        
        Args:
            owner: Repository owner
            repo: Repository name
            project_detection: Project detection results
            
        Returns:
            Dependencies analysis
        """
        try:
            dependencies = {
                "package_managers": [],
                "runtime_dependencies": {},
                "dev_dependencies": {},
                "build_tools": [],
                "estimated_build_time": "5-10 minutes"
            }
            
            # Get package.json if it's a JavaScript project
            framework = project_detection.get("framework")
            if framework in ["react", "vue", "angular", "nextjs", "gatsby", "svelte"]:
                package_json = await self._get_file_content(owner, repo, "package.json")
                if package_json:
                    try:
                        package_data = json.loads(package_json)
                        dependencies["package_managers"].append("npm")
                        dependencies["runtime_dependencies"] = package_data.get("dependencies", {})
                        dependencies["dev_dependencies"] = package_data.get("devDependencies", {})
                        
                        # Detect build tools
                        scripts = package_data.get("scripts", {})
                        if "build" in scripts:
                            dependencies["build_tools"].append("npm scripts")
                        
                        # Estimate build time based on dependencies count
                        total_deps = len(dependencies["runtime_dependencies"]) + len(dependencies["dev_dependencies"])
                        if total_deps > 100:
                            dependencies["estimated_build_time"] = "10-15 minutes"
                        elif total_deps > 50:
                            dependencies["estimated_build_time"] = "7-12 minutes"
                        else:
                            dependencies["estimated_build_time"] = "3-8 minutes"
                            
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse package.json")
            
            return dependencies
            
        except Exception as e:
            logger.error(f"Dependencies analysis failed: {str(e)}")
            return {
                "package_managers": [],
                "runtime_dependencies": {},
                "dev_dependencies": {},
                "build_tools": [],
                "estimated_build_time": "5-10 minutes"
            }
    
    async def _get_file_content(self, owner: str, repo: str, file_path: str) -> Optional[str]:
        """
        Get file content from GitHub repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            file_path: Path to file
            
        Returns:
            File content or None if not found
        """
        try:
            import httpx
            import base64
            
            api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
            
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "CodeFlowOps/1.0"
            }
            
            if settings.GITHUB_TOKEN:
                headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(api_url, headers=headers)
            
            if response.status_code == 200:
                file_data = response.json()
                if file_data.get("encoding") == "base64":
                    content = base64.b64decode(file_data.get("content", "")).decode("utf-8")
                    return content
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get file content for {file_path}: {str(e)}")
            return None
    
    async def _generate_build_configuration(
        self,
        project_detection: Dict[str, Any],
        dependencies_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate build configuration based on project analysis
        
        Args:
            project_detection: Project detection results
            dependencies_analysis: Dependencies analysis
            
        Returns:
            Build configuration
        """
        try:
            framework = project_detection.get("framework", "static")
            framework_config = self.supported_frameworks.get(framework, self.supported_frameworks["static"])
            
            build_config = {
                "build_commands": framework_config["build_commands"].copy(),
                "build_output_directory": framework_config["build_output"],
                "node_version": "18",  # Default Node.js version
                "environment_variables": {},
                "install_command": "npm install",
                "build_command": "npm run build" if framework != "static" else None,
                "cache_directories": ["node_modules"] if framework != "static" else []
            }
            
            # Framework-specific adjustments
            if framework == "nextjs":
                build_config["environment_variables"]["NEXT_TELEMETRY_DISABLED"] = "1"
                build_config["cache_directories"].append(".next/cache")
            elif framework == "gatsby":
                build_config["cache_directories"].extend([".cache", "public"])
            elif framework == "angular":
                build_config["build_output_directory"] = "dist/*"  # Angular creates subdirectory
            
            return build_config
            
        except Exception as e:
            logger.error(f"Build configuration generation failed: {str(e)}")
            return {
                "build_commands": [],
                "build_output_directory": ".",
                "node_version": "18",
                "environment_variables": {},
                "install_command": None,
                "build_command": None,
                "cache_directories": []
            }
    
    async def _estimate_deployment_resources(
        self,
        project_detection: Dict[str, Any],
        dependencies_analysis: Dict[str, Any],
        repository_structure: List[str]
    ) -> Dict[str, Any]:
        """
        Estimate AWS resources needed for deployment
        
        Args:
            project_detection: Project detection results
            dependencies_analysis: Dependencies analysis
            repository_structure: Repository file structure
            
        Returns:
            Resource estimation
        """
        try:
            deployment_type = project_detection.get("deployment_type", "static")
            
            # Base resources for static site
            resources = {
                "s3_bucket": True,
                "cloudfront_distribution": True,
                "lambda_functions": False,
                "api_gateway": False,
                "estimated_monthly_cost": "$5-15",
                "performance_tier": "standard"
            }
            
            # Adjust based on deployment type
            if deployment_type == "serverless":
                resources["lambda_functions"] = True
                resources["api_gateway"] = True
                resources["estimated_monthly_cost"] = "$15-50"
                resources["performance_tier"] = "enhanced"
            
            # Adjust based on project size
            file_count = len(repository_structure)
            if file_count > 500:
                resources["performance_tier"] = "premium"
                if deployment_type == "static":
                    resources["estimated_monthly_cost"] = "$10-25"
                else:
                    resources["estimated_monthly_cost"] = "$25-75"
            
            # Add CDN recommendations
            resources["cdn_regions"] = ["us-east-1", "eu-west-1", "ap-southeast-1"]
            
            return resources
            
        except Exception as e:
            logger.error(f"Resource estimation failed: {str(e)}")
            return {
                "s3_bucket": True,
                "cloudfront_distribution": True,
                "lambda_functions": False,
                "api_gateway": False,
                "estimated_monthly_cost": "$5-15",
                "performance_tier": "standard",
                "cdn_regions": ["us-east-1"]
            }
    
    async def generate_deployment_config(
        self,
        analysis_data: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """
        Generate detailed deployment configuration
        
        Args:
            analysis_data: Analysis results
            session_id: Session identifier
            
        Returns:
            Deployment configuration
        """
        try:
            deployment_config = {
                "session_id": session_id,
                "deployment_type": analysis_data.get("deployment_config", {}).get("type", "static"),
                "aws_stack": await self._generate_aws_stack_config(analysis_data),
                "build_spec": await self._generate_build_spec(analysis_data),
                "environment_config": await self._generate_environment_config(analysis_data),
                "monitoring_config": {
                    "enable_cloudwatch": True,
                    "enable_x_ray": analysis_data.get("deployment_config", {}).get("type") == "serverless",
                    "alert_endpoints": []
                }
            }
            
            return deployment_config
            
        except Exception as e:
            logger.error(f"Deployment configuration generation failed: {str(e)}")
            return {
                "session_id": session_id,
                "deployment_type": "static",
                "aws_stack": {},
                "build_spec": {},
                "environment_config": {},
                "monitoring_config": {}
            }
    
    async def _generate_aws_stack_config(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AWS CloudFormation stack configuration"""
        deployment_type = analysis_data.get("deployment_config", {}).get("type", "static")
        
        if deployment_type == "static":
            return {
                "template_type": "static-site",
                "resources": {
                    "S3Bucket": {
                        "type": "AWS::S3::Bucket",
                        "properties": {
                            "WebsiteConfiguration": True,
                            "PublicReadPolicy": True
                        }
                    },
                    "CloudFrontDistribution": {
                        "type": "AWS::CloudFront::Distribution",
                        "properties": {
                            "OriginS3": True,
                            "CachingEnabled": True,
                            "GzipCompression": True
                        }
                    }
                }
            }
        else:
            return {
                "template_type": "serverless-site",
                "resources": {
                    "S3Bucket": {"type": "AWS::S3::Bucket"},
                    "LambdaFunction": {"type": "AWS::Lambda::Function"},
                    "APIGateway": {"type": "AWS::ApiGateway::RestApi"},
                    "CloudFrontDistribution": {"type": "AWS::CloudFront::Distribution"}
                }
            }
    
    async def _generate_build_spec(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AWS CodeBuild buildspec configuration"""
        build_config = analysis_data.get("build_config", {})
        
        return {
            "version": "0.2",
            "phases": {
                "install": {
                    "runtime-versions": {
                        "nodejs": build_config.get("node_version", "18")
                    },
                    "commands": [build_config.get("install_command", "npm install")] if build_config.get("install_command") else []
                },
                "build": {
                    "commands": [build_config.get("build_command")] if build_config.get("build_command") else []
                }
            },
            "artifacts": {
                "files": ["**/*"],
                "base-directory": build_config.get("build_output_directory", ".")
            },
            "cache": {
                "paths": build_config.get("cache_directories", [])
            }
        }
    
    async def _generate_environment_config(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate environment configuration"""
        return {
            "variables": analysis_data.get("build_config", {}).get("environment_variables", {}),
            "secrets": [],
            "aws_region": settings.AWS_REGION,
            "deployment_stage": "production"
        }
