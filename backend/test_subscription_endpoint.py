import requests
import json

# Test the updated subscription endpoint
base_url = 'https://api.codeflowops.com'
headers = {'Origin': 'https://www.codeflowops.com', 'Content-Type': 'application/json'}

print('Testing updated /api/v1/payments/subscription/user endpoint...')

try:
    response = requests.get(f'{base_url}/api/v1/payments/subscription/user', headers=headers, timeout=30)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type", "")}')

    if response.status_code == 200:
        try:
            data = response.json()
            print('✅ SUCCESS! JSON Response received')
            print(f'Success: {data.get("success")}')
            print(f'Message: {data.get("message")}')
            print(f'Plan: {data.get("plan")}')

            subscription = data.get("subscription", {})
            if subscription:
                print(f'Subscription ID: {subscription.get("id")}')
                print(f'Status: {subscription.get("status")}')
                print(f'Product: {subscription.get("plan", {}).get("product")}')
                print(f'Amount: ${subscription.get("plan", {}).get("amount", 0) / 100}')
            else:
                print('❌ No subscription data in response')
        except:
            print('❌ JSON parsing failed')
            print(f'First 500 chars: {response.text[:500]}')
    else:
        print(f'❌ Error status: {response.status_code}')
        print(f'Response: {response.text[:500]}')

except Exception as e:
    print(f'Error: {str(e)}')