import requests

# Test the new endpoint on production
base_url = 'https://api.codeflowops.com'
headers = {'Origin': 'https://www.codeflowops.com', 'Content-Type': 'application/json'}

print('Testing new /api/v1/payments/subscription/user endpoint on production...')

try:
    response = requests.get(f'{base_url}/api/v1/payments/subscription/user', headers=headers, timeout=10)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type", "")}')
    
    if response.status_code == 200:
        try:
            data = response.json()
            print('✅ Production endpoint working!')
            print(f'Subscription status: {data.get("subscription", {}).get("status")}')
            print(f'Plan: {data.get("subscription", {}).get("plan", {}).get("product")}')
            print(f'Message: {data.get("message")}')
        except:
            print('❌ JSON parsing failed')
            print(f'First 200 chars: {response.text[:200]}')
    else:
        print(f'❌ Error status: {response.status_code}')
        print(f'Response: {response.text[:200]}')
        
except Exception as e:
    print(f'Error: {str(e)}')