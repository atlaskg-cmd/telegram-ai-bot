import requests
import json

# Читаем ключ из config.json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

api_key = config.get('openrouter_api_key', '')
model = config.get('default_model', 'arcee-ai/trinity-large-preview:free')

print(f"Checking key: {api_key[:20]}...")
print(f"Model: {model}")
print()

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/",
    "X-Title": "Bot Test"
}

data = {
    "model": model,
    "messages": [{"role": "user", "content": "Hi"}],
    "max_tokens": 10
}

try:
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=data,
        timeout=30
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        msg = result['choices'][0]['message']['content']
        print(f"Response: {msg}")
        print("\n[OK] Key is working!")
    elif response.status_code == 401:
        print("\n[ERROR] Invalid key (401)")
    elif response.status_code == 402:
        print("\n[ERROR] No credits (402)")
    elif response.status_code == 429:
        print("\n[ERROR] Rate limit (429)")
    else:
        print(f"\n[ERROR] Status: {response.status_code}")
        print(f"Body: {response.text[:200]}")
        
except Exception as e:
    print(f"\n[ERROR] Request failed: {e}")
