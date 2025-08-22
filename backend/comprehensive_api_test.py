import requests
import json

print('🔍 COMPREHENSIVE API RESPONSE ANALYSIS')
print('=' * 60)

# Test the analysis endpoint with the Flask repo
analysis_payload = {
    'repo_url': 'https://github.com/mesinkasir/cuteblog-flask'
}

try:
    print('Testing analysis endpoint...')
    analysis_response = requests.post('http://localhost:8000/api/analyze-repo', 
                                    json=analysis_payload, timeout=120)
    
    if analysis_response.status_code == 200:
        result = analysis_response.json()
        print('Analysis successful!')
        print()
        
        # Print the ENTIRE response structure to understand what's happening
        print('FULL RESPONSE STRUCTURE:')
        print('=' * 40)
        
        # Top-level fields
        print('TOP-LEVEL FIELDS:')
        for key in sorted(result.keys()):
            value = result[key]
            if isinstance(value, dict) and len(str(value)) > 100:
                print(f'  {key}: <large dict with {len(value)} keys>')
            elif isinstance(value, list) and len(str(value)) > 100:
                print(f'  {key}: <list with {len(value)} items>')
            else:
                print(f'  {key}: {value}')
        
        print()
        print('FRAMEWORK DETECTION ANALYSIS:')
        print('=' * 40)
        
        # The analysis is nested under the 'analysis' key!
        analysis_data = result.get('analysis', {})
        
        # Check all possible locations for framework info
        framework = analysis_data.get('framework')
        project_type = analysis_data.get('projectType')
        
        print(f'result.analysis.framework: {framework}')
        print(f'result.analysis.projectType: {project_type}')
        
        # Check intelligence_profile
        intel = analysis_data.get('intelligence_profile', {})
        frameworks = intel.get('frameworks', [])
        print(f'analysis.intelligence_profile.frameworks: {frameworks}')
        
        # Check stack_blueprint
        blueprint = analysis_data.get('stack_blueprint', {})
        services = blueprint.get('services', [])
        print(f'analysis.stack_blueprint.services: {len(services)} services')
        if services:
            for i, service in enumerate(services):
                fw_info = service.get('framework', {})
                print(f'  Service {i} framework: {fw_info}')
        
        print()
        print('ROUTING PREDICTION:')
        print('=' * 40)
        
        # Test frontend routing logic with ALL possible framework sources
        def test_routing(fw_source, fw_value):
            if isinstance(fw_value, dict) and fw_value.get('type'):
                fw = fw_value['type'].lower()
            elif isinstance(fw_value, str):
                fw = fw_value.lower()
            else:
                fw = ''
            
            if fw in ['flask', 'django', 'fastapi', 'python']:
                endpoint = '/api/deploy/python-lightsail'
                result_text = '✅ LightSail'
            else:
                endpoint = '/api/deploy'
                result_text = '❌ CloudFront'
            
            print(f'  {fw_source}: "{fw_value}" -> {endpoint} ({result_text})')
            return endpoint
        
        test_routing('result.analysis.framework', framework)
        test_routing('result.analysis.projectType', project_type)
        
        if frameworks:
            test_routing('intelligence_profile.frameworks[0]', frameworks[0].get('name'))
        
        if services and services[0].get('framework'):
            test_routing('stack_blueprint.services[0].framework', services[0]['framework'])
        
    else:
        print(f'Analysis failed: {analysis_response.status_code}')
        print(f'Response: {analysis_response.text}')
        
except Exception as e:
    print(f'Test failed: {e}')
    import traceback
    traceback.print_exc()
