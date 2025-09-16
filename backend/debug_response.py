import requests

# Check the actual response content from old Elastic Beanstalk URL
base_url = 'http://codeflowops.us-east-1.elasticbeanstalk.com'
headers = {'Origin': 'https://www.codeflowops.com', 'Content-Type': 'application/json'}

print('Checking actual response content from old Elastic Beanstalk URL...')

try:
    response = requests.get(f'{base_url}/api/v1/billing/subscription', headers=headers, timeout=10)
    print(f'Status: {response.status_code}')
    print(f'Content-Type: {response.headers.get("content-type", "")}')
    print(f'Response length: {len(response.text)}')
    print(f'First 500 chars: {response.text[:500]}')
    print(f'Last 500 chars: {response.text[-500:]}')

    # Check if it contains HTML
    if '<!DOCTYPE' in response.text[:100]:
        print('❌ Contains HTML DOCTYPE - this is the source of the error!')
    elif response.text.strip().startswith('{') or response.text.strip().startswith('['):
        print('✅ Looks like JSON')
    else:
        print('⚠️ Unknown format')

except Exception as e:
    print(f'Error: {str(e)}')