"""
Диагностика WhatsApp webhook для Railway.
Проверяет все компоненты интеграции с Green API.
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_credentials():
    """Проверяет наличие Green API credentials."""
    print("1️⃣ Проверка credentials...")
    
    id_instance = os.environ.get("GREEN_API_ID")
    api_token = os.environ.get("GREEN_API_TOKEN")
    
    if not id_instance:
        print("   ❌ GREEN_API_ID не установлен!")
        return False
    
    if not api_token:
        print("   ❌ GREEN_API_TOKEN не установлен!")
        return False
    
    print(f"   ✅ Instance ID: {id_instance[:8]}...")
    print(f"   ✅ API Token: {api_token[:20]}...")
    return True


def check_instance_state(id_instance, api_token):
    """Проверяет статус Green API инстанса."""
    print("\n2️⃣ Проверка статуса инстанса...")
    
    api_url = "https://api.green-api.com"
    state_url = f"{api_url}/waInstance{id_instance}/getStateInstance/{api_token}"
    
    try:
        response = requests.get(state_url, timeout=10)
        
        if response.status_code == 200:
            state = response.json()
            state_instance = state.get("stateInstance", "unknown")
            
            if state_instance == "authorized":
                print("   ✅ Инстанс авторизован (QR-код отсканирован)")
                return True
            elif state_instance == "notAuthorized":
                print("   ❌ Инстанс НЕ авторизован!")
                print("      Отсканируйте QR-код: https://console.green-api.com/")
                return False
            else:
                print(f"   ⚠️  Неизвестный статус: {state_instance}")
                return False
        else:
            print(f"   ❌ Ошибка API: {response.status_code}")
            print(f"      {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False


def check_webhook_settings(id_instance, api_token):
    """Проверяет настройки webhook."""
    print("\n3️⃣ Проверка настроек webhook...")
    
    api_url = "https://api.green-api.com"
    settings_url = f"{api_url}/waInstance{id_instance}/getSettings/{api_token}"
    
    try:
        response = requests.get(settings_url, timeout=10)
        
        if response.status_code == 200:
            settings = response.json()
            
            webhook_url = settings.get("webhookUrl", "")
            incoming_webhook = settings.get("incomingWebhook", "no")
            
            print(f"   📡 Webhook URL: {webhook_url or '(не установлен)'}")
            print(f"   📥 Incoming Webhook: {incoming_webhook}")
            
            if not webhook_url:
                print("   ❌ Webhook URL не настроен!")
                print("      Запустите: python setup_whatsapp_webhook.py")
                return False
            
            if incoming_webhook != "yes":
                print("   ❌ Incoming Webhook отключен!")
                return False
            
            print("   ✅ Webhook настроен корректно")
            return True
        else:
            print(f"   ❌ Ошибка API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        return False


def check_railway_domain():
    """Проверяет Railway domain."""
    print("\n4️⃣ Проверка Railway domain...")
    
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    
    if railway_domain:
        print(f"   ✅ Domain: {railway_domain}")
        print(f"   📡 Webhook URL: https://{railway_domain}/webhook-whatsapp")
        return True
    else:
        print("   ⚠️  RAILWAY_PUBLIC_DOMAIN не установлен")
        print("      Установите в Railway Variables если деплоите на Railway")
        return False


def test_webhook_endpoint():
    """Тестирует доступность webhook endpoint."""
    print("\n5️⃣ Тестирование webhook endpoint...")
    
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    
    if not railway_domain:
        print("   ⏭️  Пропускаем (нет RAILWAY_PUBLIC_DOMAIN)")
        return None
    
    webhook_url = f"https://{railway_domain}/webhook-whatsapp"
    
    try:
        # Пробуем GET запрос (должен вернуть 405 Method Not Allowed, но это норм)
        response = requests.get(webhook_url, timeout=5)
        
        if response.status_code in [200, 405]:
            print(f"   ✅ Endpoint доступен: {webhook_url}")
            return True
        else:
            print(f"   ⚠️  Неожиданный код: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   ⚠️  Timeout при подключении к {webhook_url}")
        return False
    except Exception as e:
        print(f"   ❌ Ошибка подключения: {e}")
        return False


def main():
    """Главная функция диагностики."""
    print("\n" + "=" * 60)
    print("🔍 ДИАГНОСТИКА WHATSAPP WEBHOOK")
    print("=" * 60 + "\n")
    
    # Проверяем credentials
    if not check_credentials():
        print("\n❌ ДИАГНОСТИКА ПРОВАЛЕНА: Нет credentials")
        print("   Установите GREEN_API_ID и GREEN_API_TOKEN")
        return False
    
    id_instance = os.environ.get("GREEN_API_ID")
    api_token = os.environ.get("GREEN_API_TOKEN")
    
    # Проверяем статус инстанса
    instance_ok = check_instance_state(id_instance, api_token)
    
    # Проверяем webhook настройки
    webhook_ok = check_webhook_settings(id_instance, api_token)
    
    # Проверяем Railway domain
    domain_ok = check_railway_domain()
    
    # Тестируем endpoint
    endpoint_ok = test_webhook_endpoint()
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ДИАГНОСТИКИ")
    print("=" * 60)
    
    status = []
    status.append(("✅" if True else "❌") + " Credentials установлены")
    status.append(("✅" if instance_ok else "❌") + " Инстанс авторизован")
    status.append(("✅" if webhook_ok else "❌") + " Webhook настроен")
    status.append(("✅" if domain_ok else "⚠️ ") + " Railway domain")
    status.append(("✅" if endpoint_ok else "⚠️ ") + " Endpoint доступен")
    
    for s in status:
        print(f"   {s}")
    
    # Выводим рекомендации
    print("\n📝 РЕКОМЕНДАЦИИ:")
    
    if not instance_ok:
        print("   1. Отсканируйте QR-код в https://console.green-api.com/")
    
    if not webhook_ok:
        print("   2. Настройте webhook: python setup_whatsapp_webhook.py")
    
    if not domain_ok:
        print("   3. Установите RAILWAY_PUBLIC_DOMAIN в Railway Variables")
    
    if instance_ok and webhook_ok:
        print("   ✅ Все основные компоненты настроены!")
        print("   📱 Отправьте 'привет' на номер бота для проверки")
    
    print()
    
    all_ok = instance_ok and webhook_ok
    return all_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
