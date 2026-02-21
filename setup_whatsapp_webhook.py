"""
Автоматическая настройка webhook для Green API WhatsApp бота.
Запускай этот скрипт после деплоя на Railway для подключения webhook.
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_webhook():
    """Настраивает webhook в Green API консоли программно."""
    
    print("🔧 Настройка WhatsApp Webhook для Green API")
    print("=" * 60)
    
    # Получаем credentials
    id_instance = os.environ.get("GREEN_API_ID")
    api_token = os.environ.get("GREEN_API_TOKEN")
    
    if not id_instance or not api_token:
        print("❌ Ошибка: GREEN_API_ID или GREEN_API_TOKEN не установлены!")
        print("   Добавьте их в Railway Variables или .env файл")
        return False
    
    print(f"✅ Instance ID: {id_instance[:8]}...")
    print(f"✅ API Token: {api_token[:20]}...")
    
    # Определяем webhook URL
    railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
    
    if railway_domain:
        webhook_url = f"https://{railway_domain}/webhook-whatsapp"
        print(f"🌐 Railway Domain: {railway_domain}")
    else:
        print("\n⚠️  RAILWAY_PUBLIC_DOMAIN не найдена!")
        print("   Введите URL вашего Railway проекта вручную:")
        print("   Пример: your-project-name.up.railway.app")
        domain = input("   Домен: ").strip()
        
        if not domain:
            print("❌ Домен обязателен!")
            return False
        
        webhook_url = f"https://{domain}/webhook-whatsapp"
    
    print(f"📡 Webhook URL: {webhook_url}")
    print()
    
    # Настраиваем webhook через Green API
    api_url = "https://api.green-api.com"
    
    # 1. Получаем текущие настройки
    print("1️⃣ Получаю текущие настройки...")
    settings_url = f"{api_url}/waInstance{id_instance}/getSettings/{api_token}"
    
    try:
        response = requests.get(settings_url, timeout=10)
        if response.status_code != 200:
            print(f"❌ Ошибка получения настроек: {response.status_code}")
            print(f"   {response.text}")
            return False
        
        current_settings = response.json()
        print("✅ Текущие настройки получены")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Green API: {e}")
        return False
    
    # 2. Обновляем настройки с webhook URL
    print("\n2️⃣ Обновляю настройки webhook...")
    update_url = f"{api_url}/waInstance{id_instance}/setSettings/{api_token}"
    
    # Важные настройки для webhook
    new_settings = {
        "webhookUrl": webhook_url,
        "webhookUrlToken": "",  # Можно добавить токен для безопасности
        "incomingWebhook": "yes",  # Включаем входящие сообщения
        "outgoingWebhook": "yes",  # Включаем статус исходящих
        "stateWebhook": "yes",  # Включаем изменения статуса
        "outgoingMessageWebhook": "yes",
        "outgoingAPIMessageWebhook": "yes",
        "incomingBlock": "no"  # НЕ блокируем входящие
    }
    
    try:
        response = requests.post(update_url, json=new_settings, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Webhook успешно настроен!")
            print(f"   Результат: {result}")
        else:
            print(f"❌ Ошибка настройки webhook: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обновления настроек: {e}")
        return False
    
    # 3. Проверяем обновленные настройки
    print("\n3️⃣ Проверяю обновленные настройки...")
    
    try:
        response = requests.get(settings_url, timeout=10)
        if response.status_code == 200:
            updated_settings = response.json()
            webhook_configured = updated_settings.get("webhookUrl")
            
            if webhook_configured == webhook_url:
                print("✅ Webhook подтвержден в настройках!")
                print(f"   URL: {webhook_configured}")
            else:
                print(f"⚠️  Webhook URL не совпадает:")
                print(f"   Ожидали: {webhook_url}")
                print(f"   Получили: {webhook_configured}")
        
    except Exception as e:
        print(f"⚠️  Не удалось проверить настройки: {e}")
    
    # 4. Проверяем статус инстанса
    print("\n4️⃣ Проверяю статус инстанса...")
    state_url = f"{api_url}/waInstance{id_instance}/getStateInstance/{api_token}"
    
    try:
        response = requests.get(state_url, timeout=10)
        if response.status_code == 200:
            state = response.json()
            state_instance = state.get("stateInstance", "unknown")
            
            if state_instance == "authorized":
                print("✅ Инстанс авторизован и готов к работе!")
            elif state_instance == "notAuthorized":
                print("⚠️  Инстанс НЕ авторизован!")
                print("   Отсканируйте QR-код в консоли Green API:")
                print("   https://console.green-api.com/")
            else:
                print(f"⚠️  Статус инстанса: {state_instance}")
        
    except Exception as e:
        print(f"⚠️  Не удалось проверить статус: {e}")
    
    # Итоги
    print("\n" + "=" * 60)
    print("🎉 НАСТРОЙКА ЗАВЕРШЕНА!")
    print("=" * 60)
    print("\n📝 Что дальше:")
    print("1. Убедитесь что инстанс авторизован (QR-код отсканирован)")
    print("2. Отправьте сообщение 'привет' на номер WhatsApp бота")
    print("3. Проверьте логи в Railway: railway logs -f")
    print("\n💡 Если бот не отвечает:")
    print("   - Проверьте что RAILWAY_PUBLIC_DOMAIN корректен")
    print("   - Проверьте логи на наличие ошибок")
    print("   - Убедитесь что Railway приложение запущено")
    print()
    
    return True


if __name__ == "__main__":
    print()
    success = setup_webhook()
    sys.exit(0 if success else 1)
