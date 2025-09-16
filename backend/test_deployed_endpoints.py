import requests
import json

# Test the GitHub subscription endpoint that was added
base_url = 'https://api.codeflowops.com'
headers = {'Origin': 'https://www.codeflowops.com', 'Content-Type': 'application/json'}

print('Testing GitHub subscription endpoint...')
try:
    response = requests.get(f'{base_url}/api/v1/auth/github/subscription', headers=headers, timeout=10)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type", "")}')

    if response.status_code == 200:
        data = response.json()
        print('✅ GitHub subscription endpoint working!')
        print(f'Status: {data.get("status")}')
        print(f'Product: {data.get("plan", {}).get("product")}')
    else:
        print(f'❌ Error: {response.status_code}')
        print(f'Response: {response.text[:200]}')
except Exception as e:
    print(f'Error: {str(e)}')

print()
print('Testing payments subscription endpoint...')
try:
    response = requests.get(f'{base_url}/api/v1/payments/subscription/user', headers=headers, timeout=10)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type", "")}')

    if response.status_code == 200:
        data = response.json()
        print('✅ Payments subscription endpoint working!')
        print(f'Success: {data.get("success")}')
        print(f'Plan: {data.get("plan")}')
        subscription = data.get('subscription', {})
        print(f'Subscription Status: {subscription.get("status")}')
        print(f'Product: {subscription.get("plan", {}).get("product")}')
    else:
        print(f'❌ Error: {response.status_code}')
        print(f'Response: {response.text[:200]}')
except Exception as e:
    print(f'Error: {str(e)}')