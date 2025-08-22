print('🔍 EMERGENCY INVESTIGATION: WHY CLOUDFRONT AGAIN?')
print('=' * 60)

# Let's check if the backend is even running our fixed code
import requests
import json

try:
    # Test if our backend is running and has the fixes
    response = requests.get('http://localhost:8000/health', timeout=5)
    print(f'Backend health check: {response.status_code}')
    
    # Test the analysis endpoint with the Flask repo
    analysis_payload = {
        'repo_url': 'https://github.com/mesinkasir/cuteblog-flask'
    }
    
    print('Testing analysis endpoint...')
    analysis_response = requests.post('http://localhost:8000/api/analyze-repo', 
                                    json=analysis_payload, timeout=30)
    
    if analysis_response.status_code == 200:
        result = analysis_response.json()
        print('Analysis successful!')
        print(f'  framework: {result.get("framework")}')
        print(f'  projectType: {result.get("projectType")}')
        print(f'  detected_stack: {result.get("detected_stack")}')
        
        # Test if the generic deploy endpoint would block Python
        deployment_id = result.get('deployment_id')
        if deployment_id:
            deploy_payload = {
                'deployment_id': deployment_id,
                'aws_access_key': 'test',
                'aws_secret_key': 'test',
                'aws_region': 'us-east-1',
                'project_name': 'test-flask'
            }
            
            print(f'Testing generic deploy endpoint with deployment_id: {deployment_id}')
            try:
                deploy_response = requests.post('http://localhost:8000/api/deploy', 
                                              json=deploy_payload, timeout=10)
                print(f'Deploy response status: {deploy_response.status_code}')
                if deploy_response.status_code == 400:
                    error_detail = deploy_response.json().get('detail', '')
                    if 'PYTHON APPLICATION DETECTED' in error_detail:
                        print('✅ SUCCESS: Backend WOULD block Python from CloudFront!')
                    else:
                        print(f'❌ FAIL: Wrong error: {error_detail}')
                else:
                    print('❌ FAIL: Backend did NOT block Python deployment!')
                    print(f'Response: {deploy_response.text}')
            except Exception as e:
                print(f'Deploy test failed: {e}')
    else:
        print(f'Analysis failed: {analysis_response.status_code} - {analysis_response.text}')
        
except Exception as e:
    print(f'Backend connection failed: {e}')
    print('Backend might not be running or not have our fixes!')
