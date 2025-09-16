import requests
import json

# Test the exact response format from the payments endpoint
base_url = 'https://api.codeflowops.com'
headers = {'Origin': 'https://www.codeflowops.com', 'Content-Type': 'application/json'}

print('Testing exact response format from payments endpoint...')
try:
    response = requests.get(f'{base_url}/api/v1/payments/subscription/user', headers=headers, timeout=10)
    if response.status_code == 200:
        data = response.json()
        print('Full response:')
        print(json.dumps(data, indent=2))
        print()
        print('Key checks:')
        print(f'data.success: {data.get("success")}')
        print(f'data.subscription exists: {"subscription" in data}')
        if 'subscription' in data:
            print(f'data.subscription.status: {data["subscription"].get("status")}')
            print(f'data.subscription.plan.product: {data["subscription"].get("plan", {}).get("product")}')
    else:
        print(f'Error: {response.status_code}')
except Exception as e:
    print(f'Error: {str(e)}')