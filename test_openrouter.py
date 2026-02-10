import json
import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

OPENROUTER_API_KEY = config.get("openrouter_api_key")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def query_deepseek(messages):
    if not OPENROUTER_API_KEY:
        print("OPENROUTER_API_KEY не установлен.")
        return
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": config.get("default_model", "arcee-ai/trinity-large-preview:free"),
        "messages": messages,
        "max_tokens": 1000
    }
    try:
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            print(f"Error: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    # Test query
    messages = [{"role": "user", "content": "Hello, how are you?"}]
    response = query_deepseek(messages)
    print("Response:", response)