import requests

# Test the suspicious frontend URL that profile page might be calling
base_url = 'https://www.codeflowops.com/api'
headers = {'Origin': 'https://www.codeflowops.com', 'Content-Type': 'application/json'}

print('Testing frontend URL with /api prefix...')

try:
    response = requests.get(f'{base_url}/v1/payments/subscription/user', headers=headers, timeout=10)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type", "")}')
    print(f'Response length: {len(response.text)}')
    
    if '<!DOCTYPE' in response.text[:100]:
        print('❌ FOUND IT! HTML Response with DOCTYPE - this is the source of the error!')
        print(f'First 200 chars: {response.text[:200]}')
    else:
        print(f'First 200 chars: {response.text[:200]}')
        
except Exception as e:
    print(f'Error: {str(e)}')