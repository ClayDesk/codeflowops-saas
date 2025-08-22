import requests
import json

print('🔍 TESTING UPDATED BACKEND ANALYSIS')
print('=' * 50)

# Test the analysis endpoint with the Flask repo
analysis_payload = {
    'repo_url': 'https://github.com/mesinkasir/cuteblog-flask'
}

try:
    print('Testing analysis endpoint...')
    analysis_response = requests.post('http://localhost:8000/api/analyze-repo', 
                                    json=analysis_payload, timeout=60)
    
    if analysis_response.status_code == 200:
        result = analysis_response.json()
        print('Analysis successful!')
        print(f'  framework: {result.get("framework")}')
        print(f'  projectType: {result.get("projectType")}')
        print(f'  detected_stack: {result.get("detected_stack")}')
        
        # Check the frameworks array
        frameworks = result.get('intelligence_profile', {}).get('frameworks', [])
        if frameworks:
            fw = frameworks[0]
            print(f'  Framework detected: {fw.get("name")}')
            print(f'  Framework type: {fw.get("framework_type")}')
            print(f'  Deployment target: {fw.get("deployment_target")}')
        else:
            print('  No frameworks detected in intelligence_profile!')
        
        print()
        print('ROUTING TEST:')
        # Test frontend routing logic
        framework_obj = result.get('framework')
        project_type = result.get('projectType')
        
        def get_frontend_endpoint(framework):
            if isinstance(framework, dict) and framework.get('type'):
                fw = framework['type'].lower()
            elif isinstance(framework, str):
                fw = framework.lower()
            else:
                fw = ''
            
            if fw in ['flask', 'django', 'fastapi', 'python']:
                return '/api/deploy/python-lightsail'
            return '/api/deploy'
        
        endpoint1 = get_frontend_endpoint(framework_obj)
        endpoint2 = get_frontend_endpoint(project_type)
        
        print(f'  Using framework object: {endpoint1}')
        print(f'  Using projectType: {endpoint2}')
        
        if '/python-lightsail' in endpoint1 or '/python-lightsail' in endpoint2:
            print('✅ SUCCESS: Will route to LightSail!')
        else:
            print('❌ FAIL: Will still route to CloudFront!')
    else:
        print(f'Analysis failed: {analysis_response.status_code} - {analysis_response.text}')
        
except Exception as e:
    print(f'Test failed: {e}')
