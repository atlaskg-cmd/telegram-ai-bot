"""
Комплексная диагностика бота
Проверяет все компоненты: Telegram, WhatsApp, API, БД
"""
import os
import sys
import json
import requests
from datetime import datetime

print("=" * 70)
print("🔍 КОМПЛЕКСНАЯ ДИАГНОСТИКА БОТА")
print(f"📅 Дата проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

errors = []
warnings = []
success = []

# ========== 1. ПРОВЕРКА ФАЙЛОВ ==========
print("\n" + "=" * 70)
print("📁 1. ПРОВЕРКА ФАЙЛОВ")
print("=" * 70)

required_files = [
    'main.py',
    'bot.py',
    'database.py',
    'config.json',
    'requirements.txt',
    'Procfile',
    'railway.json'
]

for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file}")
        success.append(f"Файл {file} найден")
    else:
        print(f"❌ {file} - НЕ НАЙДЕН")
        errors.append(f"Файл {file} отсутствует")

# ========== 2. ПРОВЕРКА CONFIG.JSON ==========
print("\n" + "=" * 70)
print("⚙️  2. ПРОВЕРКА CONFIG.JSON")
print("=" * 70)

try:
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    print("✅ config.json загружен")
    
    # Проверка моделей
    models = config.get('models', [])
    print(f"📦 Моделей в конфиге: {len(models)}")
    
    # Проверка актуальности моделей
    actual_models = [
        'openrouter/free',
        'stepfun/step-3.5-flash:free',
        'arcee-ai/trinity-large-preview:free',
        'meta-llama/llama-3.3-70b-instruct:free',
        'deepseek/deepseek-r1-0528:free',
        'google/gemma-3-27b-it:free',
        'mistralai/mistral-small-3.1-24b-instruct:free',
        'qwen/qwen3-coder:free',
        'nvidia/nemotron-3-nano-30b-a3b:free'
    ]
    
    outdated = []
    for model in models:
        if model not in actual_models and not model.endswith(':free'):
            outdated.append(model)
    
    if outdated:
        print(f"⚠️  Возможнo устаревшие модели: {outdated}")
        warnings.append(f"Устаревшие модели: {outdated}")
    else:
        print("✅ Все модели актуальны")
        success.append("Модели в config.json актуальны")
    
    # Проверка API ключей в конфиге
    if config.get('openrouter_api_key'):
        key = config['openrouter_api_key']
        if key == 'YOUR_OPENROUTER_API_KEY' or len(key) < 10:
            print("⚠️  OPENROUTER_API_KEY не настроен в config.json")
            warnings.append("OPENROUTER_API_KEY пуст или невалиден")
        else:
            print(f"✅ OPENROUTER_API_KEY: {key[:10]}... (настроен)")
    
    if config.get('weather_api_key'):
        key = config['weather_api_key']
        if key == 'YOUR_OPENWEATHERMAP_API_KEY' or len(key) < 10:
            print("⚠️  WEATHER_API_KEY не настроен в config.json")
            warnings.append("WEATHER_API_KEY пуст или невалиден")
        else:
            print(f"✅ WEATHER_API_KEY: {key[:5]}... (настроен)")
    
except json.JSONDecodeError as e:
    print(f"❌ Ошибка парсинга config.json: {e}")
    errors.append(f"config.json повреждён: {e}")
except FileNotFoundError:
    print("❌ config.json не найден")
    errors.append("config.json отсутствует")

# ========== 3. ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ==========
print("\n" + "=" * 70)
print("🔐 3. ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
print("=" * 70)

env_vars = {
    'TELEGRAM_API_TOKEN': 'Telegram Bot API Token',
    'OPENROUTER_API_KEY': 'OpenRouter AI API Key',
    'GREEN_API_ID': 'Green API Instance ID (WhatsApp)',
    'GREEN_API_TOKEN': 'Green API Token (WhatsApp)',
    'WEATHER_API_KEY': 'OpenWeatherMap API Key',
    'ADMIN_ID': 'Admin Telegram ID',
    'DATABASE_URL': 'PostgreSQL Database URL',
    'HF_TOKEN': 'Hugging Face Token (для генерации изображений)',
}

for var, desc in env_vars.items():
    value = os.environ.get(var)
    if value:
        if 'TOKEN' in var or 'KEY' in var or 'PASSWORD' in var:
            masked = f"{value[:5]}...{value[-5:]}" if len(value) > 10 else f"{value[:3]}..."
        else:
            masked = value[:20] + '...' if len(value) > 20 else value
        print(f"✅ {var}: {masked}")
        success.append(f"{desc} настроен")
    else:
        print(f"⚠️  {var}: НЕ УСТАНОВЛЕН")
        if var in ['TELEGRAM_API_TOKEN', 'OPENROUTER_API_KEY']:
            errors.append(f"Критичная переменная {var} не установлена")
        else:
            warnings.append(f"{desc} не настроен")

# ========== 4. ПРОВЕРКА TELEGRAM BOT API ==========
print("\n" + "=" * 70)
print("🤖 4. ПРОВЕРКА TELEGRAM BOT API")
print("=" * 70)

tg_token = os.environ.get('TELEGRAM_API_TOKEN')
if tg_token:
    try:
        tg_url = f"https://api.telegram.org/bot{tg_token}/getMe"
        response = requests.get(tg_url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()['result']
            print(f"✅ Telegram бот: @{bot_info.get('username', 'unknown')}")
            print(f"   Имя: {bot_info.get('first_name', 'unknown')}")
            print(f"   ID: {bot_info.get('id', 'unknown')}")
            success.append("Telegram Bot API работает")
        elif response.status_code == 401:
            print("❌ Ошибка авторизации Telegram Bot API (401)")
            print("   Неверный токен!")
            errors.append("Telegram Bot API: неверный токен")
        else:
            print(f"❌ Ошибка Telegram Bot API: {response.status_code}")
            errors.append(f"Telegram Bot API ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения к Telegram: {e}")
        errors.append(f"Telegram Bot API: {e}")
else:
    print("⏭️  Пропущено (нет TELEGRAM_API_TOKEN)")

# ========== 5. ПРОВЕРКА GREEN API (WHATSAPP) ==========
print("\n" + "=" * 70)
print("💬 5. ПРОВЕРКА GREEN API (WHATSAPP)")
print("=" * 70)

green_id = os.environ.get('GREEN_API_ID')
green_token = os.environ.get('GREEN_API_TOKEN')

if green_id and green_token:
    try:
        state_url = f"https://api.green-api.com/waInstance{green_id}/GetStateInstance/{green_token}"
        response = requests.get(state_url, timeout=10)
        
        if response.status_code == 200:
            state = response.json().get('stateInstance', 'unknown')
            print(f"✅ Green API статус: {state}")
            
            if state == 'authorized':
                print("   ✅ WhatsApp авторизован")
                success.append("WhatsApp Green API авторизован")
            elif state == 'notAuthorized':
                print("   ❌ WhatsApp НЕ авторизован")
                print("   Нужно отсканировать QR-код!")
                errors.append("WhatsApp Green API: не авторизован")
            else:
                print(f"   ⚠️  Статус: {state}")
                warnings.append(f"WhatsApp Green API: статус {state}")
        else:
            print(f"❌ Ошибка Green API: {response.status_code}")
            errors.append(f"Green API ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения к Green API: {e}")
        errors.append(f"Green API: {e}")
else:
    print("⏭️  Пропущено (нет GREEN_API_ID/TOKEN)")

# ========== 6. ПРОВЕРКА OPENROUTER API ==========
print("\n" + "=" * 70)
print("🧠 6. ПРОВЕРКА OPENROUTER API")
print("=" * 70)

openrouter_key = os.environ.get('OPENROUTER_API_KEY')
if openrouter_key:
    try:
        headers = {'Authorization': f'Bearer {openrouter_key}'}
        response = requests.get('https://openrouter.ai/api/v1/auth/key', headers=headers, timeout=10)
        
        if response.status_code == 200:
            key_info = response.json().get('data', {})
            print(f"✅ OpenRouter API ключ валиден")
            print(f"   Label: {key_info.get('label', 'unknown')}")
            print(f"   Usage: ${key_info.get('total_usage', 0):.4f}")
            success.append("OpenRouter API ключ валиден")
        elif response.status_code == 401:
            print("❌ Ошибка авторизации OpenRouter (401)")
            print("   Неверный API ключ!")
            errors.append("OpenRouter API: неверный ключ")
        else:
            print(f"⚠️  OpenRouter API ответ: {response.status_code}")
            warnings.append(f"OpenRouter API: статус {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения к OpenRouter: {e}")
        errors.append(f"OpenRouter API: {e}")
else:
    print("⏭️  Пропущено (нет OPENROUTER_API_KEY)")

# ========== 7. ПРОВЕРКА CURRENCY API ==========
print("\n" + "=" * 70)
print("💱 7. ПРОВЕРКА CURRENCY API")
print("=" * 70)

try:
    url = "https://api.exchangerate-api.com/v4/latest/USD"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        kgs = data['rates'].get('KGS', 'N/A')
        rub = data['rates'].get('RUB', 'N/A')
        print(f"✅ Currency API работает")
        print(f"   1 USD = {kgs} KGS")
        print(f"   1 USD = {rub} RUB")
        success.append("Currency API работает")
    else:
        print(f"❌ Ошибка Currency API: {response.status_code}")
        errors.append(f"Currency API ошибка: {response.status_code}")
except Exception as e:
    print(f"❌ Ошибка подключения к Currency API: {e}")
    errors.append(f"Currency API: {e}")

# ========== 8. ПРОВЕРКА COINGECKO API ==========
print("\n" + "=" * 70)
print("₿ 8. ПРОВЕРКА COINGECKO API (CRYPTO)")
print("=" * 70)

try:
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        btc = data.get('bitcoin', {}).get('usd', 'N/A')
        eth = data.get('ethereum', {}).get('usd', 'N/A')
        print(f"✅ CoinGecko API работает")
        print(f"   Bitcoin: ${btc:,}")
        print(f"   Ethereum: ${eth:,}")
        success.append("CoinGecko API работает")
    elif response.status_code == 429:
        print("⚠️  CoinGecko rate limit (429)")
        print("   Слишком много запросов, попробуйте позже")
        warnings.append("CoinGecko API: rate limit")
    else:
        print(f"❌ Ошибка CoinGecko API: {response.status_code}")
        errors.append(f"CoinGecko API ошибка: {response.status_code}")
except Exception as e:
    print(f"❌ Ошибка подключения к CoinGecko: {e}")
    errors.append(f"CoinGecko API: {e}")

# ========== 9. ПРОВЕРКА OPENWEATHERMAP API ==========
print("\n" + "=" * 70)
print("🌤️  9. ПРОВЕРКА OPENWEATHERMAP API (ПОГОДА)")
print("=" * 70)

weather_key = os.environ.get('WEATHER_API_KEY')
if weather_key and weather_key != 'YOUR_OPENWEATHERMAP_API_KEY' and len(weather_key) > 10:
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Bishkek&appid={weather_key}&units=metric"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            temp = data['main']['temp']
            print(f"✅ OpenWeatherMap API работает")
            print(f"   Погода в Бишкеке: {temp}°C")
            success.append("OpenWeatherMap API работает")
        elif response.status_code == 401:
            print("❌ Ошибка авторизации OpenWeatherMap (401)")
            print("   Неверный API ключ!")
            errors.append("OpenWeatherMap API: неверный ключ")
        else:
            print(f"❌ Ошибка OpenWeatherMap API: {response.status_code}")
            errors.append(f"OpenWeatherMap API ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка подключения к OpenWeatherMap: {e}")
        errors.append(f"OpenWeatherMap API: {e}")
else:
    print("⏭️  Пропущено (нет WEATHER_API_KEY)")

# ========== ИТОГИ ==========
print("\n" + "=" * 70)
print("📊 ИТОГИ ДИАГНОСТИКИ")
print("=" * 70)

print(f"\n✅ Успешно: {len(success)}")
print(f"⚠️  Предупреждения: {len(warnings)}")
print(f"❌ Ошибки: {len(errors)}")

if errors:
    print("\n❌ КРИТИЧЕСКИЕ ОШИБКИ:")
    for error in errors:
        print(f"   • {error}")

if warnings:
    print("\n⚠️  ПРЕДУПРЕЖДЕНИЯ:")
    for warning in warnings:
        print(f"   • {warning}")

print("\n" + "=" * 70)
if errors:
    print("🔴 БОТ НЕ ГОТОВ К РАБОТЕ - есть критические ошибки!")
    print("\n📝 РЕКОМЕНДАЦИИ:")
    print("   1. Настройте переменные окружения в Railway Dashboard")
    print("   2. Проверьте API ключи")
    print("   3. Убедитесь, что все сервисы авторизованы")
else:
    print("🟢 БОТ ГОТОВ К РАБОТЕ!")
    print("\n✅ Все критичные компоненты настроены правильно")

print("=" * 70)

# Exit code
sys.exit(1 if errors else 0)
