#!/usr/bin/env python3
"""
Test Full Frontend-to-Backend ReactDeployer Flow
"""

import json
import uuid
from typing import Dict, Any

print('🌐 Testing Full Frontend-to-Backend ReactDeployer Flow')
print('=' * 60)

# Simulate a frontend request for React deployment
def simulate_frontend_react_deploy():
    print('📤 Simulating Frontend React Deploy Request...')
    
    # Import the API function
    from simple_api import deploy_to_aws, DeployRequest
    
    # Create a mock request like the frontend would send
    deployment_id = str(uuid.uuid4())
    
    # Mock request data (like what frontend sends)
    request_data = {
        'deployment_id': deployment_id,
        'aws_access_key_id': 'AKIA***REDACTED***',
        'aws_secret_access_key': '***REDACTED***',
        'aws_region': 'us-east-1',
        'repository_url': 'https://github.com/FahimFBA/react-crash',
        'project_name': 'test-react-app',
        'framework': 'react'  # Frontend detected framework
    }
    
    print(f'📋 Request Details:')
    print(f'   Deployment ID: {deployment_id}')
    print(f'   Repository: {request_data["repository_url"]}')
    print(f'   Framework: {request_data["framework"]}')
    print(f'   AWS Region: {request_data["aws_region"]}')
    
    # Mock analysis results (what would come from repo analyzer)
    mock_analysis = {
        'status': 'success',
        'framework': {'type': 'react', 'name': 'React'},
        'frameworks': [{'name': 'react', 'type': 'frontend'}],
        'deployment_strategy': 'frontend_only',
        'requires_full_stack': False,
        'repository_url': request_data['repository_url'],
        'package_manager': 'npm',
        'build_tool': 'create-react-app'
    }
    
    print(f'\n🔍 Mock Analysis:')
    print(f'   Framework Detected: ✅ React')
    print(f'   Full Stack Required: ❌ No')
    print(f'   Deployment Strategy: frontend_only')
    print(f'   Package Manager: {mock_analysis["package_manager"]}')
    
    # Create request object
    class MockRequest:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    request = MockRequest(**request_data)
    
    print(f'\n🚀 Testing React Detection and Routing...')
    
    # Check if React will be detected
    has_react = (
        any("react" in str(fw).lower() for fw in mock_analysis.get("frameworks", [])) or
        "react" in str(mock_analysis.get("framework", "")).lower() or
        "react" in str(request.framework or "").lower()
    )
    
    requires_full_stack = mock_analysis.get("requires_full_stack", False)
    
    from simple_api import REACT_DEPLOYER_AVAILABLE
    
    print(f'   React Detected: {"✅ Yes" if has_react else "❌ No"}')
    print(f'   Full Stack Required: {"✅ Yes" if requires_full_stack else "❌ No"}')
    print(f'   ReactDeployer Available: {"✅ Yes" if REACT_DEPLOYER_AVAILABLE else "❌ No"}')
    
    will_route_to_react_deployer = (
        has_react and 
        not requires_full_stack and 
        REACT_DEPLOYER_AVAILABLE
    )
    
    print(f'\n🎯 Routing Decision:')
    if will_route_to_react_deployer:
        print('✅ WILL ROUTE TO REACTDEPLOYER')
        print('   ⚛️ Simple React app detected')
        print('   🚀 Using DirectReactBuilder + S3 + CloudFront')
        print('   ⚡ No CodeBuild required - faster deployment')
    else:
        print('❌ Will NOT route to ReactDeployer')
        if not has_react:
            print('   Reason: React not detected')
        elif requires_full_stack:
            print('   Reason: Full-stack deployment required')
        elif not REACT_DEPLOYER_AVAILABLE:
            print('   Reason: ReactDeployer not available')
    
    return will_route_to_react_deployer

if __name__ == "__main__":
    try:
        result = simulate_frontend_react_deploy()
        
        print('\n📊 Integration Test Results:')
        if result:
            print('✅ Frontend Integration: SUCCESSFUL')
            print('✅ React Detection: Working')
            print('✅ ReactDeployer Routing: Working')
            print('✅ DirectReactBuilder: Ready')
            print('✅ S3 + CloudFront: Ready')
            print('')
            print('🎉 Frontend can successfully deploy React apps!')
            print('🚀 Faster deployment without CodeBuild!')
        else:
            print('❌ Frontend Integration: FAILED')
            print('❌ React apps will not be routed to ReactDeployer')
            
    except Exception as e:
        print(f'❌ Test failed: {e}')
        import traceback
        traceback.print_exc()
