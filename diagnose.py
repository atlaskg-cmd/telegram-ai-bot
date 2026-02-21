"""
Diagnostic script for WhatsApp bot
Checks configuration and tests API connection
"""
import os
import sys
import requests

print("=" * 60)
print("🔍 ДИАГНОСТИКА WHATSAPP БОТА")
print("=" * 60)

# Check environment variables
print("\n1. Проверка переменных окружения:")
print("-" * 40)

green_id = os.environ.get("GREEN_API_ID")
green_token = os.environ.get("GREEN_API_TOKEN")

if not green_id:
    print("❌ GREEN_API_ID: НЕ УСТАНОВЛЕНА")
    print("   Добавьте в Railway Variables!")
else:
    print(f"✅ GREEN_API_ID: {green_id[:5]}... (длина: {len(green_id)})")

if not green_token:
    print("❌ GREEN_API_TOKEN: НЕ УСТАНОВЛЕН")
    print("   Добавьте в Railway Variables!")
else:
    print(f"✅ GREEN_API_TOKEN: {green_token[:10]}... (длина: {len(green_token)})")

if not green_id or not green_token:
    print("\n⚠️  Переменные не установлены!")
    print("   Перейдите в Railway → Variables → New Variable")
    sys.exit(1)

# Test API connection
print("\n2. Проверка подключения к Green API:")
print("-" * 40)

api_url = f"https://api.green-api.com/waInstance{green_id}/GetStateInstance/{green_token}"

try:
    response = requests.get(api_url, timeout=10)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API отвечает")
        print(f"   Статус: {data.get('stateInstance', 'неизвестно')}")
        
        status = data.get('stateInstance')
        if status == "authorized":
            print("   ✅ Номер авторизован!")
        elif status == "created":
            print("   ❌ Номер НЕ авторизован!")
            print("   Нужно отсканировать QR-код в Green API Console")
        elif status == "error":
            print("   ❌ Ошибка авторизации!")
            print("   Возможно, номер отвязался. Попробуйте пересканировать QR")
        else:
            print(f"   ⚠️  Неизвестный статус: {status}")
    else:
        print(f"❌ Ошибка API: {response.status_code}")
        print(f"   Ответ: {response.text[:100]}")
        print("\n   Возможные причины:")
        print("   - Неправильный ID Instance")
        print("   - Неправильный API Token")
        print("   - Instance удален или заблокирован")
        
except Exception as e:
    print(f"❌ Ошибка подключения: {e}")
    print("   Проверьте интернет-соединение")

print("\n" + "=" * 60)
print("📋 РЕКОМЕНДАЦИИ:")
print("=" * 60)

if status == "authorized":
    print("✅ Номер подключен правильно!")
    print("\nЕсли бот не отвечает:")
    print("1. Проверьте логи в Railway Dashboard → Logs")
    print("2. Перезапустите бота: Deploy → Redeploy")
    print("3. Убедитесь, что main.py запускается")
else:
    print("❌ Нужно авторизовать номер:")
    print("1. Откройте https://console.green-api.com/")
    print("2. Найдите ваш Instance")
    print("3. Нажмите 'QR code'")
    print("4. Отсканируйте QR-код телефоном (WhatsApp)")
