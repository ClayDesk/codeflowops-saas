#!/usr/bin/env python3
"""
End-to-end test for ReactDeployer using react-crash repository
"""

from react_deployer import ReactDeployer
import json

def test_react_deployment():
    print('🚀 Starting end-to-end React deployment test...')
    
    # Initialize deployer
    deployer = ReactDeployer()
    
    # Test repository analysis
    repo_url = 'https://github.com/FahimFBA/react-crash'
    print(f'📊 Analyzing repository: {repo_url}')
    
    analysis_result = deployer.analyze_react_repository(repo_url)
    print('Analysis result:', json.dumps(analysis_result, indent=2))
    
    if analysis_result['status'] == 'success':
        print('✅ Repository analysis successful!')
        print(f'Package Manager: {analysis_result.get("package_manager")}')
        print(f'Build Tool: {analysis_result.get("build_tool")}')
        print(f'React Version: {analysis_result.get("react_version")}')
        print(f'Output Directory: {analysis_result.get("output_directory")}')
        print(f'Build Script: {analysis_result.get("build_script")}')
        
        # Now test building (without AWS deployment for now)
        print('\n🔨 Testing React build process...')
        from direct_react_builder import DirectReactBuilder
        
        builder = DirectReactBuilder()
        build_result = builder.build_react_from_repo(repo_url, "test-deployment-001")
        
        print('Build result:', json.dumps(build_result, indent=2))
        
        if build_result['status'] == 'success':
            print('✅ React build successful!')
            print(f'Archive Path: {build_result.get("archive_path")}')
            print(f'Build Output Path: {build_result.get("build_output_path")}')
        else:
            print('❌ React build failed!')
            
    else:
        print('❌ Repository analysis failed!')

if __name__ == "__main__":
    test_react_deployment()
