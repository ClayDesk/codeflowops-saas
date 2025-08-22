#!/usr/bin/env python3
"""
Test the framework handling fix in the Python LightSail router
"""
import requests
import json

def test_framework_handling():
    """Test the Python LightSail endpoint with different framework formats"""
    
    # Test with string framework
    test_payload_string = {
        'repo_url': 'https://github.com/test/test-flask',
        'deployment_id': 'test-123',
        'aws_access_key': 'test-key',
        'aws_secret_key': 'test-secret',
        'framework': 'flask'
    }

    # Test with dict framework (like from enhanced analyzer)
    test_payload_dict = {
        'repo_url': 'https://github.com/test/test-flask',
        'deployment_id': 'test-456',
        'aws_access_key': 'test-key',
        'aws_secret_key': 'test-secret',
        'framework': {'type': 'flask', 'name': 'Flask', 'confidence': 0.9}
    }

    print('🧪 Testing Python LightSail endpoint with different framework formats...')
    print()

    test_cases = [
        ('string', test_payload_string),
        ('dict', test_payload_dict)
    ]

    for i, (name, payload) in enumerate(test_cases, 1):
        print(f'Test {i}: Framework as {name}')
        print(f'Framework data: {payload["framework"]}')
        
        try:
            response = requests.post(
                'http://localhost:8000/api/deploy/python-lightsail',
                json=payload,
                timeout=10
            )
            print(f'Status: {response.status_code}')
            if response.status_code != 200:
                print(f'Error: {response.text}')
                
                # Try to parse JSON error
                try:
                    error_data = response.json()
                    print(f'Error detail: {error_data.get("detail", "Unknown error")}')
                except:
                    pass
            else:
                result = response.json()
                print(f'✅ Success! Deployment ID: {result.get("deployment_id", "Unknown")}')
                
        except Exception as e:
            print(f'❌ Request failed: {e}')
        
        print('-' * 50)

if __name__ == "__main__":
    test_framework_handling()
