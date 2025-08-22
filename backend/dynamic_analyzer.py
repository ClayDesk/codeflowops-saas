"""
🎯 Dynamic Plain English Repository Analyzer
Analyzes any repository using intelligent framework detection and provides human-readable insights
"""

import requests
import json
from typing import Dict, Any, List

class DynamicRepositoryAnalyzer:
    """🔍 Dynamic analyzer that works with any repository type"""
    
    def __init__(self, api_url: str = "http://localhost:8000/api/analyze-repository"):
        self.api_url = api_url
        
        # Dynamic project type descriptions
        self.project_descriptions = {
            "static-basic": {
                "emoji": "🌐",
                "description": "a static website - HTML, CSS, and JavaScript files served directly",
                "details": "Perfect for portfolios, business websites, or landing pages"
            },
            "nextjs-static": {
                "emoji": "⚡",
                "description": "a Next.js static website - modern React framework with static generation",
                "details": "Optimized for performance with static site generation"
            },
            "nextjs-ssr": {
                "emoji": "🚀", 
                "description": "a Next.js web application - modern React framework with server-side rendering",
                "details": "Dynamic web application with server-side features"
            },
            "react-spa": {
                "emoji": "📱",
                "description": "a React web application - modern single-page application",
                "details": "Interactive web app with modern JavaScript framework"
            },
            "vue-spa": {
                "emoji": "🌟",
                "description": "a Vue.js web application - progressive JavaScript framework",
                "details": "Modern web app with Vue.js framework"
            },
            "php-laravel": {
                "emoji": "🏗️",
                "description": "a Laravel PHP application - modern PHP framework",
                "details": "Full-featured web application with PHP backend"
            },
            "php": {
                "emoji": "🌐",
                "description": "a PHP web application - dynamic server-side website",
                "details": "Traditional web application with PHP backend"
            },
            "python": {
                "emoji": "🐍",
                "description": "a Python application",
                "details": "Python-based application or web service"
            },
            "django": {
                "emoji": "🎯",
                "description": "a Django web application - Python web framework",
                "details": "Full-featured web application with Python backend"
            },
            "flask": {
                "emoji": "🌶️",
                "description": "a Flask web application - lightweight Python web framework",
                "details": "Lightweight web application or API"
            },
            "fastapi": {
                "emoji": "⚡",
                "description": "a FastAPI application - modern Python API framework",
                "details": "High-performance API with automatic documentation"
            }
        }
        
        # Dynamic deployment strategies
        self.deployment_strategies = {
            "static": {
                "type": "Static Website Deployment",
                "hosts": ["AWS S3 + CloudFront", "Netlify", "Vercel", "GitHub Pages"],
                "steps": [
                    "📁 Upload all static files to web hosting",
                    "🌐 Point your domain to the hosting service", 
                    "✅ Your website will be live!"
                ],
                "cost": "Very Low ($0-10/month)"
            },
            "server": {
                "type": "Server-Side Application",
                "hosts": ["AWS EC2", "DigitalOcean", "Railway", "Heroku"],
                "steps": [
                    "🚀 Deploy to server hosting platform",
                    "⚙️ Configure environment variables",
                    "🗄️ Set up database (if required)",
                    "🌐 Configure domain and SSL",
                    "✅ Your application will be live!"
                ],
                "cost": "Medium ($10-50/month)"
            },
            "spa": {
                "type": "Single Page Application",
                "hosts": ["Netlify", "Vercel", "AWS S3 + CloudFront"],
                "steps": [
                    "📦 Run build command to create production files",
                    "📤 Upload build folder to web hosting",
                    "🌐 Configure routing for SPA",
                    "✅ Your app will be live!"
                ],
                "cost": "Low ($5-20/month)"
            }
        }

    def analyze_repository(self, repo_url: str) -> None:
        """Analyze any repository and provide human-readable insights"""
        print("🎯 DYNAMIC PLAIN ENGLISH REPOSITORY ANALYSIS")
        print("=" * 50)
        print(f"\n🔍 COMPREHENSIVE ANALYSIS: {repo_url}")
        print("=" * 80)
        
        try:
            # Call the intelligent analysis API
            response = requests.post(
                self.api_url,
                json={"repository_url": repo_url, "deployment_id": f"dynamic-analysis"},
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            
            if response.status_code != 200:
                print(f"❌ Analysis failed: {response.status_code}")
                return
                
            data = response.json()
            
            # Extract key information
            intelligence_profile = data.get('intelligence_profile', {})
            stack_blueprint = data.get('stack_blueprint', {})
            executive_summary = data.get('executive_summary', {})
            
            # Dynamic analysis reporting
            self._print_summary_report(data, intelligence_profile)
            self._print_project_identification(intelligence_profile)
            self._print_technology_stack(intelligence_profile, executive_summary)
            self._print_security_assessment(intelligence_profile)
            self._print_deployment_readiness(executive_summary, stack_blueprint)
            self._print_overall_assessment(executive_summary)
            self._print_dynamic_recommendations(intelligence_profile, stack_blueprint)
            self._print_technical_breakdown(intelligence_profile)
            self._print_deployment_architecture(stack_blueprint)
            self._print_deployment_guide(intelligence_profile, stack_blueprint)
            self._print_cost_analysis(executive_summary, stack_blueprint)
            
            print("\n" + "=" * 80)
            print("✅ COMPLETE DYNAMIC ANALYSIS FINISHED!")
            print("This analysis adapts to any repository type automatically.")
            print("=" * 80)
            
        except Exception as e:
            print(f"❌ Error during analysis: {str(e)}")

    def _print_summary_report(self, data: Dict[str, Any], intelligence_profile: Dict[str, Any]) -> None:
        """Print dynamic summary based on actual analysis"""
        file_intel = intelligence_profile.get('file_intelligence', {})
        crawl_stats = file_intel.get('crawl_stats', {})
        
        total_files = crawl_stats.get('files_analyzed', 0)
        analysis_time = data.get('analysis_time_seconds', 0)
        languages = crawl_stats.get('languages_detected', [])
        
        print(f"\n📋 SUMMARY REPORT")
        print("-" * 40)
        print(f"✅ Successfully analyzed {total_files} files in {analysis_time:.1f} seconds")
        if languages:
            print(f"🌍 Found code written in {len(languages)} different programming languages")

    def _print_project_identification(self, intelligence_profile: Dict[str, Any]) -> None:
        """Dynamically identify project type from framework detection"""
        print(f"\n🎯 WHAT IS THIS PROJECT?")
        print("-" * 30)
        
        stack_classification = intelligence_profile.get('stack_classification', {})
        stack_type = stack_classification.get('type', 'unknown')
        confidence = stack_classification.get('confidence', 0)
        evidence = stack_classification.get('evidence', [])
        
        # Get project description dynamically
        project_info = self.project_descriptions.get(stack_type)
        if project_info:
            print(f"{project_info['emoji']} This is {project_info['description']}")
            if confidence > 0.8:
                print(f"   ✨ High confidence detection ({confidence:.0%})")
            
            # Show evidence if available
            if evidence and len(evidence) > 0:
                key_evidence = evidence[:3]  # Show top 3 pieces of evidence
                print(f"   📋 Key indicators: {', '.join(key_evidence)}")
        else:
            # Fallback for unknown types
            frameworks = intelligence_profile.get('frameworks', [])
            if frameworks:
                top_framework = frameworks[0]
                framework_name = top_framework.get('name', 'unknown')
                print(f"🔧 This appears to be a {framework_name} project")
            else:
                print("📁 This appears to be a software project")
        
        # Project size assessment
        file_intel = intelligence_profile.get('file_intelligence', {})
        crawl_stats = file_intel.get('crawl_stats', {})
        total_files = crawl_stats.get('files_analyzed', 0)
        
        if total_files < 20:
            print("📏 Size: Small project - easy to understand and work with")
        elif total_files < 100:
            print("📏 Size: Medium project - well-organized and manageable")
        else:
            print("📏 Size: Large project - comprehensive with many components")

    def _print_technology_stack(self, intelligence_profile: Dict[str, Any], executive_summary: Dict[str, Any]) -> None:
        """Dynamic technology stack analysis"""
        print(f"\n🔧 TECHNOLOGIES USED")
        print("-" * 25)
        
        frameworks = intelligence_profile.get('frameworks', [])
        file_intel = intelligence_profile.get('file_intelligence', {})
        languages = file_intel.get('crawl_stats', {}).get('languages_detected', [])
        
        # Show detected frameworks first (most important)
        if frameworks:
            print("📦 Frameworks & Libraries:")
            for framework in frameworks[:5]:  # Show top 5 frameworks
                name = framework.get('name', 'Unknown')
                confidence = framework.get('confidence', 0)
                variant = framework.get('variant')
                
                description = self._get_framework_description(name, variant)
                confidence_indicator = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
                
                variant_text = f" ({variant})" if variant else ""
                print(f"   {confidence_indicator} {name}{variant_text} - {description}")
        
        # Show programming languages
        if languages:
            print(f"\n💬 Programming Languages:")
            language_descriptions = {
                'JavaScript': 'For interactive web functionality',
                'Python': 'For backend logic and data processing', 
                'PHP': 'For server-side web development',
                'HTML': 'For website structure and content',
                'CSS': 'For styling and visual design',
                'TypeScript': 'For type-safe JavaScript development',
                'Java': 'For enterprise applications',
                'C#': 'For .NET applications',
                'Go': 'For high-performance backend services',
                'Rust': 'For system programming and performance',
                'Ruby': 'For web applications and scripting'
            }
            
            for lang in languages[:7]:  # Show top 7 languages
                description = language_descriptions.get(lang, f'For {lang.lower()} development')
                print(f"   • {lang} - {description}")
            
            if len(languages) > 7:
                print(f"   ...and {len(languages) - 7} more")

    def _print_security_assessment(self, intelligence_profile: Dict[str, Any]) -> None:
        """Dynamic security assessment"""
        print(f"\n🛡️ SECURITY CHECK")
        print("-" * 20)
        
        env_data = intelligence_profile.get('env', {})
        security_risks = env_data.get('security_risks', [])
        secrets = env_data.get('secrets', [])
        
        if not security_risks and not secrets:
            print("✅ Great! No security issues found - the code looks clean and safe")
        else:
            risk_count = len(security_risks) + len(secrets)
            print(f"⚠️  Found {risk_count} security issue(s) that need attention:")
            
            for risk in security_risks[:3]:  # Show top 3 risks
                risk_type = risk.get('type', 'Unknown')
                severity = risk.get('severity', 'medium')
                severity_emoji = "🔴" if severity == 'high' else "🟡" if severity == 'medium' else "🟢"
                print(f"   {severity_emoji} {risk_type} ({severity} severity)")
            
            if len(security_risks) > 3:
                print(f"   ... and {len(security_risks) - 3} more issues")

    def _print_deployment_readiness(self, executive_summary: Dict[str, Any], stack_blueprint: Dict[str, Any]) -> None:
        """Dynamic deployment readiness assessment"""
        print(f"\n🚀 CAN THIS BE DEPLOYED?")
        print("-" * 30)
        
        deployment_rec = executive_summary.get('deployment_recommendation', {})
        confidence = deployment_rec.get('confidence', 0)
        complexity = deployment_rec.get('deployment_complexity', 'Unknown')
        cost = deployment_rec.get('estimated_cost', 'Unknown')
        deploy_time = deployment_rec.get('deployment_time', 'Unknown')
        
        if confidence > 0.8:
            print("✅ Yes! This project is ready to deploy easily")
        elif confidence > 0.5:
            print("🟡 Yes, with some configuration needed")
        else:
            print("🔴 Needs work before deployment - complex setup required")
        
        print(f"💰 Estimated monthly cost: {cost}")
        print(f"⏱️ Time to deploy: {deploy_time}")
        print(f"📦 Deployment complexity: {complexity}")

    def _print_overall_assessment(self, executive_summary: Dict[str, Any]) -> None:
        """Dynamic overall project assessment"""
        print(f"\n⭐ OVERALL ASSESSMENT")
        print("-" * 25)
        
        readiness_score = executive_summary.get('readiness_score', {})
        overall = readiness_score.get('overall', 0) * 100
        
        if overall >= 80:
            print(f"🎉 Excellent! ({overall:.0f}/100) - This project is in great shape")
        elif overall >= 60:
            print(f"👍 Good! ({overall:.0f}/100) - This project is ready with minor improvements needed")
        elif overall >= 40:
            print(f"👌 Okay ({overall:.0f}/100) - This project needs some work but is manageable")
        else:
            print(f"🔧 Needs Work ({overall:.0f}/100) - This project requires significant attention")

    def _print_dynamic_recommendations(self, intelligence_profile: Dict[str, Any], stack_blueprint: Dict[str, Any]) -> None:
        """Generate dynamic recommendations based on detected stack"""
        print(f"\n💡 INTELLIGENT RECOMMENDATIONS")
        print("-" * 35)
        
        stack_classification = intelligence_profile.get('stack_classification', {})
        stack_type = stack_classification.get('type', 'unknown')
        rendering_mode = stack_classification.get('rendering_mode', 'unknown')
        required_runtimes = stack_classification.get('required_runtimes', [])
        
        # Dynamic recommendations based on stack type
        if rendering_mode == 'static':
            print("• This project can be deployed as a static website")
            print("• No server maintenance required - just upload and go")
            print("• Perfect for fast loading times and low costs")
            print("• Consider using CDN for global performance")
        elif rendering_mode == 'server':
            print("• This application requires server-side hosting")
            print("• Database setup may be needed")
            if required_runtimes:
                runtime_list = ', '.join(required_runtimes)
                print(f"• Requires runtime: {runtime_list}")
            print("• Consider containerization for easier deployment")
        
        # Framework-specific recommendations
        frameworks = intelligence_profile.get('frameworks', [])
        if frameworks:
            primary_framework = frameworks[0]
            framework_name = primary_framework.get('name', '')
            
            if framework_name == 'static-basic':
                evidence = primary_framework.get('evidence', [])
                if any('incidental PHP' in str(e) for e in evidence):
                    print("• Note: Contact form functionality detected - may need form service")
            elif framework_name == 'nextjs':
                print("• Consider using Vercel for optimal Next.js hosting")
                print("• Enable image optimization and automatic API routes")
            elif framework_name == 'react':
                print("• Optimize bundle size with code splitting")
                print("• Consider Progressive Web App features")

    def _print_technical_breakdown(self, intelligence_profile: Dict[str, Any]) -> None:
        """Dynamic technical file analysis"""
        print(f"\n📊 TECHNICAL BREAKDOWN")
        print("=" * 25)
        
        file_intel = intelligence_profile.get('file_intelligence', {})
        crawl_stats = file_intel.get('crawl_stats', {})
        file_types = crawl_stats.get('file_types', {})
        
        print(f"\n📁 FILE ANALYSIS")
        print("-" * 20)
        total_files = crawl_stats.get('files_analyzed', 0)
        print(f"Total files analyzed: {total_files}")
        
        # Categorize files dynamically
        categories = {
            'web': ['.html', '.htm', '.css', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte'],
            'backend': ['.php', '.py', '.rb', '.java', '.cs', '.go', '.rs', '.cpp', '.c'],
            'config': ['.json', '.yaml', '.yml', '.toml', '.ini', '.env', '.config'],
            'docs': ['.md', '.txt', '.rst', '.pdf', '.doc'],
            'images': ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp'],
            'data': ['.sql', '.db', '.sqlite', '.csv', '.xml']
        }
        
        categorized_files = {}
        for ext, count in file_types.items():
            category_found = False
            for category, extensions in categories.items():
                if ext.lower() in extensions:
                    if category not in categorized_files:
                        categorized_files[category] = []
                    categorized_files[category].append((ext, count))
                    category_found = True
                    break
            if not category_found:
                if 'other' not in categorized_files:
                    categorized_files['other'] = []
                categorized_files['other'].append((ext, count))
        
        # Display categorized files
        category_emojis = {
            'web': '🌐',
            'backend': '⚙️',
            'config': '📋',
            'docs': '📚',
            'images': '🖼️',
            'data': '🗄️',
            'other': '📁'
        }
        
        for category, files in categorized_files.items():
            emoji = category_emojis.get(category, '📁')
            total_count = sum(count for _, count in files)
            print(f"   {emoji} {category.title()} files: {total_count} files")
            
            # Show breakdown for categories with multiple types
            if len(files) > 1:
                for ext, count in files[:3]:  # Show top 3 extensions
                    print(f"      - {ext or '(no extension)'}: {count} files")

    def _print_deployment_architecture(self, stack_blueprint: Dict[str, Any]) -> None:
        """Dynamic deployment architecture recommendations"""
        print(f"\n🏗️ DEPLOYMENT ARCHITECTURE")
        print("-" * 35)
        
        services = stack_blueprint.get('services', [])
        shared_resources = stack_blueprint.get('shared_resources', {})
        final_rec = stack_blueprint.get('final_recommendation', {})
        
        stack_id = final_rec.get('stack_id', 'Unknown')
        deployment_recipe = final_rec.get('deployment_recipe_id', '')
        
        print(f"Recommended stack: {stack_id}")
        
        if deployment_recipe:
            # Parse deployment recipe for insights
            if 's3' in deployment_recipe and 'cloudfront' in deployment_recipe:
                print("   🌐 Amazon Web Services (AWS) static hosting")
                print("   📊 S3 for file storage + CloudFront CDN")
                print("   ⚡ Global content delivery network")
                print("   💳 Pay-as-you-use pricing")
            elif 'ec2' in deployment_recipe:
                print("   🖥️ Amazon EC2 server hosting")
                print("   🔧 Full server control and customization")
                print("   📈 Scalable compute resources")
            elif 'vercel' in deployment_recipe or 'netlify' in deployment_recipe:
                print("   ⚡ Modern JAMstack hosting platform")
                print("   🚀 Automatic deployments from git")
                print("   🌍 Global edge network")

    def _print_deployment_guide(self, intelligence_profile: Dict[str, Any], stack_blueprint: Dict[str, Any]) -> None:
        """Dynamic deployment guide based on detected stack"""
        print(f"\n🚀 DEPLOYMENT GUIDE")
        print("-" * 25)
        
        stack_classification = intelligence_profile.get('stack_classification', {})
        rendering_mode = stack_classification.get('rendering_mode', 'unknown')
        stack_type = stack_classification.get('type', 'unknown')
        
        # Determine deployment strategy
        if rendering_mode == 'static':
            strategy = self.deployment_strategies['static']
        elif stack_type.endswith('-spa'):
            strategy = self.deployment_strategies['spa']
        else:
            strategy = self.deployment_strategies['server']
        
        print(f"Deployment Type: {strategy['type']}")
        print(f"\nRecommended Steps:")
        for i, step in enumerate(strategy['steps'], 1):
            print(f"{i}. {step}")
        
        print(f"\nRecommended Hosting Platforms:")
        for host in strategy['hosts']:
            print(f"   • {host}")

    def _print_cost_analysis(self, executive_summary: Dict[str, Any], stack_blueprint: Dict[str, Any]) -> None:
        """Dynamic cost analysis"""
        print(f"\n💰 COST ANALYSIS")
        print("-" * 20)
        
        deployment_rec = executive_summary.get('deployment_recommendation', {})
        cost = deployment_rec.get('estimated_cost', 'Unknown')
        
        stack_classification_type = stack_blueprint.get('services', [])
        
        print(f"Estimated monthly cost: {cost}")
        
        # Dynamic cost breakdown based on deployment type
        if any('static' in str(service) for service in stack_classification_type):
            print("💵 Static hosting breakdown:")
            print("   • Hosting: $0-5/month (Netlify/Vercel free tiers available)")
            print("   • Domain: $10-15/year")
            print("   • SSL Certificate: $0 (included with most hosts)")
        else:
            print("💵 Server hosting breakdown:")
            print("   • Server: $5-25/month (basic VPS)")
            print("   • Database: $0-15/month (if required)")
            print("   • Domain: $10-15/year")
            print("   • SSL Certificate: $0 (Let's Encrypt)")

    def _get_framework_description(self, name: str, variant: str = None) -> str:
        """Get human-readable description for frameworks"""
        descriptions = {
            'static-basic': 'Static HTML/CSS/JS website',
            'nextjs': 'Modern React framework',
            'react': 'Interactive JavaScript library',
            'vue': 'Progressive JavaScript framework', 
            'angular': 'Full-featured TypeScript framework',
            'laravel': 'Elegant PHP framework',
            'django': 'Python web framework',
            'flask': 'Lightweight Python framework',
            'fastapi': 'Modern Python API framework',
            'express': 'Node.js web framework',
            'spring': 'Java enterprise framework'
        }
        
        base_desc = descriptions.get(name, f'{name} framework')
        if variant:
            base_desc += f' ({variant})'
        return base_desc


if __name__ == "__main__":
    analyzer = DynamicRepositoryAnalyzer()
    
    # Default to cv-site for testing, but can analyze any repo
    repo_url = "https://github.com/kalanakt/cv-site"
    analyzer.analyze_repository(repo_url)
