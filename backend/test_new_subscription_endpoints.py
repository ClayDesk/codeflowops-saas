import requests
import json

# Test the new subscription endpoints
base_url = 'http://localhost:8000'

print('Testing new subscription endpoints...')

# Test billing subscription endpoint
print('\n1. Testing /api/v1/billing/subscription (requires auth)')
try:
    # For testing, we'll use a mock token
    headers = {'Authorization': 'Bearer token-test-123456'}
    response = requests.get(f'{base_url}/api/v1/billing/subscription', headers=headers, timeout=5)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type", "")}')

    if response.status_code == 200:
        try:
            data = response.json()
            print('✅ SUCCESS! JSON Response received')
            print(f'Success: {data.get("success")}')
            print(f'Message: {data.get("message")}')
            if 'subscription' in data:
                sub = data['subscription']
                print(f'Subscription ID: {sub.get("id")}')
                print(f'Status: {sub.get("status")}')
                print(f'Plan: {sub.get("plan", {}).get("name")}')
        except:
            print('❌ JSON parsing failed')
            print(f'First 500 chars: {response.text[:500]}')
    else:
        print(f'❌ Error status: {response.status_code}')
        print(f'Response: {response.text[:500]}')

except Exception as e:
    print(f'Error: {str(e)}')

# Test GitHub subscription endpoint
print('\n2. Testing /api/v1/auth/github/subscription (requires auth)')
try:
    headers = {'Authorization': 'Bearer github-token-123456'}
    response = requests.get(f'{base_url}/api/v1/auth/github/subscription', headers=headers, timeout=5)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type", "")}')

    if response.status_code == 200:
        try:
            data = response.json()
            print('✅ SUCCESS! JSON Response received')
            print(f'Success: {data.get("success")}')
            print(f'Message: {data.get("message")}')
            if 'subscription' in data:
                sub = data['subscription']
                print(f'Subscription ID: {sub.get("id")}')
                print(f'Status: {sub.get("status")}')
                print(f'Plan: {sub.get("plan", {}).get("name")}')
        except:
            print('❌ JSON parsing failed')
            print(f'First 500 chars: {response.text[:500]}')
    else:
        print(f'❌ Error status: {response.status_code}')
        print(f'Response: {response.text[:500]}')

except Exception as e:
    print(f'Error: {str(e)}')

print('\nTest completed!')