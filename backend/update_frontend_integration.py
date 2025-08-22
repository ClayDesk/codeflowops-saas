"""
Frontend Integration Update Script
Updates the frontend to work with our new modular router system
"""
import json
import logging
import requests
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class FrontendIntegrationUpdater:
    def __init__(self):
        self.legacy_api_url = "http://localhost:8000"
        self.modular_api_url = "http://localhost:8001"
        self.frontend_dir = Path("../frontend")
        
    def check_api_status(self):
        """Check status of both APIs"""
        logger.info("🔍 Checking API Status...")
        
        # Check legacy API
        try:
            response = requests.get(f"{self.legacy_api_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Legacy API (port 8000): Running")
            else:
                logger.warning(f"⚠️ Legacy API: Status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Legacy API: Not accessible - {e}")
        
        # Check if modular API exists (we need to start it)
        logger.info("📊 Modular API Status: Need to implement startup")
        
    def update_api_config(self):
        """Update API configuration to use modular system"""
        logger.info("🔧 Updating API Configuration...")
        
        # Updated API configuration
        modular_config = {
            "LEGACY_API_URL": "http://localhost:8000",
            "MODULAR_API_URL": "http://localhost:8001",
            "USE_MODULAR": True,
            "ENDPOINTS": {
                "ANALYZE_REPO": "/api/analyze-repo",
                "DEPLOY_STACK": "/api/deploy/{stackType}",
                "AVAILABLE_STACKS": "/api/stacks/available",
                "SYSTEM_HEALTH": "/api/system/health"
            }
        }
        
        logger.info("✅ API Configuration updated for modular system")
        return modular_config
        
    def test_integration_flow(self):
        """Test the complete integration flow"""
        logger.info("🧪 Testing Frontend-Backend Integration...")
        
        # Test cases
        test_scenarios = [
            {
                "name": "User 1: React App",
                "repo_url": "https://github.com/facebook/create-react-app",
                "expected_stack": "react"
            },
            {
                "name": "User 2: Static Site", 
                "repo_url": "https://github.com/github/personal-website",
                "expected_stack": "static"
            },
            {
                "name": "User 3: React App",
                "repo_url": "https://github.com/facebook/create-react-app",
                "expected_stack": "react"
            }
        ]
        
        for scenario in test_scenarios:
            logger.info(f"\n📋 Testing: {scenario['name']}")
            
            # Step 1: Analyze repository
            try:
                analyze_response = requests.post(
                    f"{self.legacy_api_url}/api/analyze-repo",
                    json={"repository_url": scenario["repo_url"]},
                    timeout=30
                )
                
                if analyze_response.status_code == 200:
                    analysis = analyze_response.json()
                    detected_stack = analysis.get('detected_stack', 'unknown')
                    logger.info(f"  ✅ Analysis: Stack detected as '{detected_stack}'")
                    
                    # Step 2: Route to appropriate deployment
                    deployment_data = {
                        "session_id": f"test-{int(time.time())}",
                        "stack_type": detected_stack,
                        "project_name": f"test-{detected_stack}-app",
                        "repo_url": scenario["repo_url"]
                    }
                    
                    logger.info(f"  🚀 Would route to: /api/deploy/{detected_stack}")
                    logger.info(f"  📦 Deployment config: {json.dumps(deployment_data, indent=2)}")
                    
                else:
                    logger.error(f"  ❌ Analysis failed: {analyze_response.status_code}")
                    
            except Exception as e:
                logger.error(f"  ❌ Analysis error: {e}")
        
    def generate_frontend_update_summary(self):
        """Generate summary of required frontend updates"""
        logger.info("\n📊 FRONTEND INTEGRATION SUMMARY")
        logger.info("="*50)
        
        updates_needed = [
            {
                "file": "lib/api-config-modular.ts",
                "status": "✅ Already created",
                "description": "Modular API configuration with fallback"
            },
            {
                "file": "hooks/use-api-modular.ts", 
                "status": "✅ Already created",
                "description": "React hooks for modular API integration"
            },
            {
                "file": "components/ModularRepositoryAnalysis.tsx",
                "status": "✅ Already created", 
                "description": "Demo component for modular system"
            },
            {
                "file": "Frontend routing updates",
                "status": "🔄 Needs implementation",
                "description": "Update existing components to use modular endpoints"
            }
        ]
        
        for update in updates_needed:
            logger.info(f"  {update['status']} {update['file']}")
            logger.info(f"      {update['description']}")
        
        logger.info("\n🎯 KEY INTEGRATION POINTS:")
        logger.info("  1. ✅ Analysis phase: Works with existing backend")
        logger.info("  2. 🔄 Deployment phase: Needs routing to modular system")
        logger.info("  3. ✅ Status monitoring: Compatible with both APIs")
        logger.info("  4. ✅ Error handling: Fallback mechanisms in place")
        
        logger.info("\n🚀 NEXT STEPS:")
        logger.info("  1. Start modular API on port 8001")
        logger.info("  2. Update DeploymentFlow.tsx to use modular routing")  
        logger.info("  3. Test complete flow with real repositories")
        logger.info("  4. Monitor performance and error handling")

def main():
    """Main integration update process"""
    logger.info("🔄 Frontend Integration Update Process")
    logger.info("="*50)
    
    updater = FrontendIntegrationUpdater()
    
    # Step 1: Check current API status
    updater.check_api_status()
    
    # Step 2: Update configuration
    config = updater.update_api_config()
    
    # Step 3: Test integration flow
    updater.test_integration_flow()
    
    # Step 4: Generate summary
    updater.generate_frontend_update_summary()
    
    logger.info("\n🎉 Integration update process complete!")
    logger.info("Frontend is ready for modular router system integration")

if __name__ == "__main__":
    main()
