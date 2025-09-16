import requests

# Test the new endpoint locally first
print('Testing new /api/v1/payments/subscription/user endpoint locally...')

try:
    # Test local endpoint
    response = requests.get('http://localhost:8000/api/v1/payments/subscription/user', timeout=5)
    print(f'Local test - Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print('✅ Local endpoint working')
        print(f'Subscription status: {data.get("subscription", {}).get("status")}')
        print(f'Plan: {data.get("subscription", {}).get("plan", {}).get("product")}')
    else:
        print(f'❌ Local endpoint failed: {response.text}')
except Exception as e:
    print(f'Local test failed: {str(e)}')