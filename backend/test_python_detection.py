print('🔍 TESTING PYTHON DETECTION LOGIC')
print('=' * 50)

# Simulate the actual analysis result we got earlier
analysis_result = {
    'framework': {'type': 'flask', 'confidence': 0.6},
    'projectType': 'flask',
    'frameworks': [],
    'stack_blueprint': {'services': []},
    'repository_url': 'https://github.com/mesinkasir/cuteblog-flask'
}

# Test the Python detection logic from simple_api.py
def test_python_detection(analysis):
    python_indicators = ['flask', 'django', 'fastapi', 'python', 'streamlit', 'gradio']
    
    # Get all possible framework indicators
    framework_obj = analysis.get('framework', {})
    framework_name = ''
    if isinstance(framework_obj, dict):
        framework_name = framework_obj.get('type', '')
    elif isinstance(framework_obj, str):
        framework_name = framework_obj
    
    project_type = analysis.get('projectType', '')
    legacy_framework = analysis.get('detected_stack', '')
    frameworks_array = analysis.get('frameworks', [])
    services = analysis.get('stack_blueprint', {}).get('services', [])
    
    # Check if this is a Python application
    is_python_app = (
        framework_name.lower() in python_indicators or 
        project_type.lower() in python_indicators or
        legacy_framework.lower() in python_indicators or
        any(fw.get('name', '').lower() in python_indicators for fw in frameworks_array) or
        any(service.get('framework', {}).get('name', '').lower() in python_indicators for service in services) or
        'python' in analysis.get('repository_url', '').lower()
    )
    
    print('DETECTION RESULTS:')
    print(f'  framework_name: "{framework_name}"')
    print(f'  project_type: "{project_type}"')
    print(f'  legacy_framework: "{legacy_framework}"')
    print(f'  frameworks_array: {frameworks_array}')
    print(f'  services: {services}')
    repo_url = analysis.get('repository_url', '')
    print(f'  repository_url: "{repo_url}"')
    print()
    print(f'  framework_name in python_indicators: {framework_name.lower() in python_indicators}')
    print(f'  project_type in python_indicators: {project_type.lower() in python_indicators}')
    print(f'  is_python_app: {is_python_app}')
    
    return is_python_app

is_python = test_python_detection(analysis_result)

if is_python:
    print()
    print('✅ SUCCESS: Python detection would BLOCK CloudFront deployment')
    print('🚨 This should trigger HTTPException with redirect to LightSail')
else:
    print()
    print('❌ FAILURE: Python detection would NOT block CloudFront deployment')
    print('🔥 THIS IS THE BUG! Detection logic is not working')
