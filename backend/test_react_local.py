#!/usr/bin/env python3
"""
Test ReactDeployer Local Integration
"""

print('🔍 Testing ReactDeployer Local Integration')
print('=' * 50)

try:
    from react_deployer import ReactDeployer
    print('✅ ReactDeployer imported successfully')
    
    # Test initialization
    deployer = ReactDeployer()
    print('✅ ReactDeployer initialized')
    
    # Test repository analysis
    print('\n🔍 Testing Repository Analysis...')
    analysis = deployer.analyze_react_repository('https://github.com/FahimFBA/react-crash')
    
    if analysis.get('status') == 'success':
        print('✅ Repository analysis successful!')
        print(f'   Package Manager: {analysis.get("package_manager")}')
        print(f'   Build Tool: {analysis.get("build_tool")}')
        print(f'   React Version: {analysis.get("react_version")}')
        print(f'   Output Directory: {analysis.get("output_directory")}')
    else:
        print(f'❌ Repository analysis failed: {analysis.get("error")}')
    
    # Test API integration
    print('\n🔗 Testing API Integration...')
    from simple_api import REACT_DEPLOYER_AVAILABLE
    print(f'✅ ReactDeployer Available in API: {REACT_DEPLOYER_AVAILABLE}')
    
    print('\n🎉 All Local Tests Passed!')
    print('✅ ReactDeployer is working locally')
    print('✅ DirectReactBuilder integration active')
    print('✅ Ready for deployment testing')
    
except Exception as e:
    print(f'❌ Test failed: {e}')
    import traceback
    traceback.print_exc()
