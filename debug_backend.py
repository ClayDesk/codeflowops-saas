#!/usr/bin/env python3
"""
Debug AWS Backend Issues
"""

import requests
import json

def debug_backend():
    print('🔍 Debugging Backend Issues')
    print('=' * 50)
    
    base_url = 'https://api.codeflowops.com'
    
    # Test 1: Basic health check
    print('1. Testing Backend Health...')
    try:
        health_response = requests.get(f'{base_url}/health')
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f'   ✅ Backend is healthy: {health_data}')
        else:
            print(f'   ❌ Health check failed: {health_response.status_code}')
    except Exception as e:
        print(f'   ❌ Health check error: {e}')
    
    # Test 2: Check if ReactDeployer is available
    print('\n2. Testing ReactDeployer Availability...')
    try:
        # Test a simple repository analysis with a known React repo
        test_payload = {
            'repo_url': 'https://github.com/facebook/react',  # Official React repo
            'analysis_type': 'quick'
        }
        
        analysis_response = requests.post(
            f'{base_url}/api/analyze-repo',
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f'   Status Code: {analysis_response.status_code}')
        
        if analysis_response.status_code == 200:
            analysis_data = analysis_response.json()
            print(f'   ✅ Analysis successful!')
            print(f'   Response: {json.dumps(analysis_data, indent=2)[:500]}...')
        else:
            print(f'   ❌ Analysis failed')
            print(f'   Error: {analysis_response.text[:500]}...')
            
    except Exception as e:
        print(f'   ❌ Analysis error: {e}')
    
    # Test 3: Test simple deployment endpoint
    print('\n3. Testing Deployment Endpoint...')
    try:
        # Try a minimal deployment request
        minimal_payload = {
            'deployment_id': 'test-deployment-001',
            'aws_region': 'us-east-1',
            'repository_url': 'https://github.com/FahimFBA/react-crash',
            'framework': 'react'
        }
        
        # Don't actually deploy, just test if endpoint accepts the request format
        deploy_response = requests.post(
            f'{base_url}/api/deploy',
            json=minimal_payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f'   Status Code: {deploy_response.status_code}')
        print(f'   Response: {deploy_response.text[:500]}...')
        
    except Exception as e:
        print(f'   ❌ Deployment test error: {e}')
    
    print('\n🔧 Debugging Complete')

if __name__ == "__main__":
    debug_backend()
