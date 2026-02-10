import os
import requests
import json

key = os.environ.get('OPENROUTER_API_KEY')
print('OPENROUTER_API_KEY present:', bool(key))

url = 'https://openrouter.ai/api/v1/chat/completions'
headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
data = {
    'model': 'arcee-ai/trinity-large-preview:free',
    'messages': [{'role':'user','content':'Hello'}],
    'max_tokens': 10
}
try:
    r = requests.post(url, headers=headers, json=data, timeout=15)
    print('Status code:', r.status_code)
    print('Response snippet:', r.text[:1000])
except Exception as e:
    print('Request error:', e)
