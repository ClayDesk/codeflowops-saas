# Template Selector Service for Smart Deploy
# Analyzes repositories and selects appropriate infrastructure templates

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re

class TemplateSelector:
    """
    Service for selecting appropriate Terraform templates based on repository analysis
    """
    
    def __init__(self):
        self.template_configs = self._load_template_configs()
    
    def _load_template_configs(self) -> Dict[str, Dict]:
        """Load template configuration metadata"""
        return {
            "static_site": {
                "name": "Static Website",
                "description": "S3 + CloudFront + IAM for static websites",
                "suitable_for": ["react", "vue", "angular", "static", "spa", "gatsby", "next-static"],
                "resources": ["S3", "CloudFront", "Route53", "ACM", "IAM"],
                "estimated_cost_range": "$5-20/month",
                "supports_custom_domain": True,
                "deployment_time": "5-10 minutes",
                "complexity": "low"
            },
            "react_node_app": {
                "name": "Full-Stack React Node App",
                "description": "ECS Fargate + ALB + RDS + IAM for containerized applications",
                "suitable_for": ["fullstack", "api", "node", "express", "nestjs", "containerized"],
                "resources": ["ECS", "ALB", "RDS", "VPC", "NAT", "CloudWatch", "IAM"],
                "estimated_cost_range": "$30-100/month",
                "supports_custom_domain": True,
                "deployment_time": "15-25 minutes",
                "complexity": "high"
            }
        }
    
    def analyze_and_select_template(
        self, 
        analysis_data: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze repository data and select the best template
        
        Returns:
            Tuple of (template_name, template_info)
        """
        try:
            # Extract analysis information
            languages = analysis_data.get("languages", [])
            frameworks = analysis_data.get("frameworks", [])
            dependencies = analysis_data.get("dependencies", [])
            project_type = analysis_data.get("project_type", "unknown")
            has_backend = analysis_data.get("has_backend", False)
            has_database = analysis_data.get("has_database", False)
            
            print(f"🔍 Template selection analysis:")
            print(f"   Languages: {languages}")
            print(f"   Frameworks: {frameworks}")
            print(f"   Dependencies: {dependencies}")
            print(f"   Project type: {project_type}")
            print(f"   Has backend: {has_backend}")
            print(f"   Has database: {has_database}")
            
            # Decision logic for template selection
            selected_template = self._apply_selection_logic(
                languages=languages,
                frameworks=frameworks,
                dependencies=dependencies,
                project_type=project_type,
                has_backend=has_backend,
                has_database=has_database,
                deployment_config=deployment_config
            )
            
            template_info = self.template_configs.get(selected_template, {})
            
            print(f"✅ Selected template: {selected_template}")
            print(f"📋 Template info: {template_info.get('name', 'Unknown')}")
            
            return selected_template, template_info
            
        except Exception as e:
            print(f"⚠️ Template selection failed, defaulting to static_site: {e}")
            return "static_site", self.template_configs["static_site"]
    
    def _apply_selection_logic(
        self,
        languages: List[str],
        frameworks: List[str], 
        dependencies: List[str],
        project_type: str,
        has_backend: bool,
        has_database: bool,
        deployment_config: Dict[str, Any]
    ) -> str:
        """
        Apply template selection logic based on analysis data
        """
        # Force template selection via config override
        forced_template = deployment_config.get("force_template")
        if forced_template and forced_template in self.template_configs:
            print(f"🔧 Forced template selection: {forced_template}")
            return forced_template
        
        # Check for full-stack indicators
        fullstack_indicators = [
            has_backend and has_database,
            "express" in dependencies,
            "nestjs" in dependencies,
            "fastapi" in dependencies,
            "django" in dependencies,
            "rails" in dependencies,
            "laravel" in dependencies,
            any(db in dependencies for db in ["postgres", "mysql", "mongodb", "redis"]),
            project_type in ["fullstack", "api", "backend"],
            "docker" in dependencies or "dockerfile" in [f.lower() for f in dependencies]
        ]
        
        if any(fullstack_indicators):
            print(f"🏗️ Full-stack application detected, selecting react_node_app template")
            return "react_node_app"
        
        # Check for static site indicators
        static_indicators = [
            project_type in ["static_site", "spa", "frontend"],
            any(fw in frameworks for fw in ["react", "vue", "angular", "svelte"]),
            any(tool in dependencies for tool in ["gatsby", "next", "nuxt", "vite", "webpack"]),
            not has_backend,
            not has_database,
            "javascript" in languages or "typescript" in languages
        ]
        
        if any(static_indicators):
            print(f"🌐 Static site application detected, selecting static_site template")
            return "static_site"
        
        # Default decision based on complexity
        if len(dependencies) > 10 or has_backend:
            print(f"🔧 Complex application detected, defaulting to react_node_app template")
            return "react_node_app"
        else:
            print(f"📄 Simple application detected, defaulting to static_site template")
            return "static_site"
    
    def get_template_recommendations(
        self, 
        analysis_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Get ranked template recommendations with explanations
        """
        recommendations = []
        
        for template_name, template_info in self.template_configs.items():
            score = self._calculate_template_score(template_name, analysis_data)
            
            recommendations.append({
                "template": template_name,
                "score": score,
                "name": template_info["name"],
                "description": template_info["description"],
                "resources": template_info["resources"],
                "estimated_cost": template_info["estimated_cost_range"],
                "deployment_time": template_info["deployment_time"],
                "complexity": template_info["complexity"],
                "explanation": self._get_recommendation_explanation(template_name, analysis_data)
            })
        
        # Sort by score (descending)
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations
    
    def _calculate_template_score(self, template_name: str, analysis_data: Dict[str, Any]) -> float:
        """
        Calculate a score for how well a template matches the analysis data
        """
        template_config = self.template_configs[template_name]
        suitable_for = template_config["suitable_for"]
        
        score = 0.0
        
        # Check project type match
        project_type = analysis_data.get("project_type", "")
        if project_type in suitable_for:
            score += 2.0
        
        # Check framework matches
        frameworks = analysis_data.get("frameworks", [])
        for framework in frameworks:
            if any(framework.lower() in suitable.lower() for suitable in suitable_for):
                score += 1.0
        
        # Check dependency matches
        dependencies = analysis_data.get("dependencies", [])
        for dependency in dependencies:
            if any(dependency.lower() in suitable.lower() for suitable in suitable_for):
                score += 0.5
        
        # Adjust for complexity
        has_backend = analysis_data.get("has_backend", False)
        has_database = analysis_data.get("has_database", False)
        
        if template_name == "react_node_app":
            if has_backend or has_database:
                score += 1.5
            else:
                score -= 1.0  # Penalty for using complex template for simple projects
        
        if template_name == "static_site":
            if not has_backend and not has_database:
                score += 1.0
            else:
                score -= 0.5  # Penalty for using simple template for complex projects
        
        return max(0.0, score)
    
    def _get_recommendation_explanation(self, template_name: str, analysis_data: Dict[str, Any]) -> str:
        """
        Generate explanation for template recommendation
        """
        if template_name == "static_site":
            return "Ideal for frontend applications, static websites, and SPAs with no backend requirements."
        elif template_name == "react_node_app":
            return "Best for full-stack applications with backend APIs, databases, and containerized deployments."
        else:
            return "Template recommendation based on project analysis."
    
    def get_template_variables(
        self, 
        template_name: str, 
        analysis_data: Dict[str, Any],
        deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate template-specific variables based on analysis and config
        """
        base_variables = {
            "project_name": deployment_config.get("project_name", "my-app"),
            "environment": deployment_config.get("environment", "prod"),
            "aws_region": deployment_config.get("aws_region", "us-east-1"),
            "domain_name": deployment_config.get("domain_name", ""),
        }
        
        if template_name == "static_site":
            return {
                **base_variables,
                "cloudfront_price_class": "PriceClass_100",  # Cost optimization
                "enable_logging": False,
            }
        elif template_name == "react_node_app":
            return {
                **base_variables,
                "app_port": self._detect_app_port(analysis_data),
                "fargate_cpu": 512,  # Start small
                "fargate_memory": 1024,
                "db_instance_class": "db.t3.micro",  # Cost optimization
                "auto_scaling_min_capacity": 1,
                "auto_scaling_max_capacity": 3,
            }
        
        return base_variables
    
    def _detect_app_port(self, analysis_data: Dict[str, Any]) -> int:
        """
        Detect the application port from analysis data
        """
        # Look for common port configurations
        dependencies = analysis_data.get("dependencies", [])
        
        # Common framework ports
        if "next" in dependencies:
            return 3000
        elif "express" in dependencies:
            return 3000
        elif "nestjs" in dependencies:
            return 3000
        elif "fastapi" in dependencies:
            return 8000
        elif "django" in dependencies:
            return 8000
        else:
            return 3000  # Default Node.js port
