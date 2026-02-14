"""
WhatsApp Bot Diagnostic Tool
Run this to check if WhatsApp bot configuration is correct.
"""
import os
import sys
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def check_env_variables():
    """Check if required environment variables are set."""
    print("=" * 60)
    print("🔍 Проверка переменных окружения")
    print("=" * 60)
    
    green_api_id = os.environ.get("GREEN_API_ID")
    green_api_token = os.environ.get("GREEN_API_TOKEN")
    telegram_token = os.environ.get("TELEGRAM_API_TOKEN")
    
    errors = []
    
    if not green_api_id:
        errors.append("❌ GREEN_API_ID не установлен")
        print("❌ GREEN_API_ID: не найден")
    else:
        print(f"✅ GREEN_API_ID: {green_api_id[:5]}...")
    
    if not green_api_token:
        errors.append("❌ GREEN_API_TOKEN не установлен")
        print("❌ GREEN_API_TOKEN: не найден")
    else:
        print(f"✅ GREEN_API_TOKEN: {green_api_token[:10]}...")
    
    if not telegram_token:
        print("⚠️  TELEGRAM_API_TOKEN: не найден (только WhatsApp будет работать)")
    else:
        print(f"✅ TELEGRAM_API_TOKEN: {telegram_token[:15]}...")
    
    if errors:
        print("\n❌ ОШИБКИ:")
        for error in errors:
            print(f"   {error}")
        return False, green_api_id, green_api_token
    
    print("\n✅ Все необходимые переменные установлены!")
    return True, green_api_id, green_api_token


def check_green_api_connection(api_id, api_token):
    """Test connection to Green API."""
    print("\n" + "=" * 60)
    print("🔍 Проверка подключения к Green API")
    print("=" * 60)
    
    # Test GetSettings method
    url = f"https://api.green-api.com/waInstance{api_id}/GetSettings/{api_token}"
    
    try:
        print(f"🌐 Отправка запроса к Green API...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Подключение успешно!")
            
            # Check settings
            if 'wid' in data:
                print(f"📱 Номер бота: {data.get('wid', 'неизвестно')}")
            if 'webhookUrl' in data:
                print(f"🔗 Webhook URL: {data.get('webhookUrl', 'не установлен')}")
            
            return True
        elif response.status_code == 401:
            print("❌ Ошибка 401: Неверные credentials (ID или Token)")
            print("   Проверьте GREEN_API_ID и GREEN_API_TOKEN")
            return False
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут при подключении к Green API")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def check_receive_notification(api_id, api_token):
    """Test receiving notifications."""
    print("\n" + "=" * 60)
    print("🔍 Проверка получения сообщений")
    print("=" * 60)
    
    url = f"https://api.green-api.com/waInstance{api_id}/ReceiveNotification/{api_token}"
    
    try:
        print("🌐 Попытка получить уведомления...")
        print("   (Отправьте сообщение на номер бота в WhatsApp прямо сейчас!)")
        
        response = requests.get(url, timeout=35)  # Long polling
        
        if response.status_code == 200:
            data = response.json()
            
            if data:
                print("✅ Уведомление получено!")
                print(f"📋 Тип: {data.get('body', {}).get('typeWebhook', 'unknown')}")
                
                # Try to extract message details
                body = data.get('body', {})
                if body.get('typeWebhook') == 'incomingMessageReceived':
                    sender = body.get('senderData', {}).get('sender', 'unknown')
                    print(f"📱 Отправитель: {sender}")
                    
                    message_data = body.get('messageData', {})
                    if message_data.get('typeMessage') == 'textMessage':
                        text = message_data.get('textMessageData', {}).get('textMessage', '')
                        print(f"💬 Текст: {text[:50]}...")
                
                # Delete the notification
                receipt_id = data.get('receiptId')
                if receipt_id:
                    delete_url = f"https://api.green-api.com/waInstance{api_id}/DeleteNotification/{api_token}/{receipt_id}"
                    requests.delete(delete_url, timeout=10)
                    print("🗑️  Уведомление удалено из очереди")
                
                return True
            else:
                print("ℹ️  Нет новых уведомлений (null response)")
                print("   Это нормально - просто нет новых сообщений")
                return True
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("ℹ️  Таймаут - нет новых сообщений (это нормально)")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_send_message(api_id, api_token):
    """Test sending a message (to your own number)."""
    print("\n" + "=" * 60)
    print("🔍 Тест отправки сообщения")
    print("=" * 60)
    
    print("⚠️  Чтобы протестировать отправку, введите свой номер WhatsApp")
    print("   Формат: 996XXXYYYYYY (киргизский формат)")
    print("   Или: 7XXXYYYYYYY (российский формат)")
    print("   Или нажмите Enter чтобы пропустить")
    
    phone = input("Номер: ").strip()
    
    if not phone:
        print("⏩ Пропускаем тест отправки")
        return True
    
    # Format phone number
    if not phone.startswith("+"):
        phone = "+" + phone
    
    chat_id = phone + "@c.us"
    
    url = f"https://api.green-api.com/waInstance{api_id}/SendMessage/{api_token}"
    payload = {
        "chatId": chat_id,
        "message": "🤖 Тестовое сообщение от бота!\n\nЕсли вы видите это сообщение, значит бот работает корректно. ✅"
    }
    
    try:
        print(f"🌐 Отправка сообщения на {phone}...")
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            print("✅ Сообщение успешно отправлено!")
            print("   Проверьте WhatsApp!")
            return True
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            print(f"   Ответ: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def main():
    """Run all diagnostics."""
    print("\n" + "=" * 60)
    print("🩺 ДИАГНОСТИКА WHATSAPP БОТА")
    print("=" * 60)
    
    # Check 1: Environment variables
    ok, api_id, api_token = check_env_variables()
    if not ok:
        print("\n" + "=" * 60)
        print("❌ ДИАГНОСТИКА НЕ ПРОЙДЕНА")
        print("=" * 60)
        print("\n💡 Как исправить:")
        print("   1. Установите переменные окружения:")
        print("      export GREEN_API_ID='your_id'")
        print("      export GREEN_API_TOKEN='your_token'")
        print("   2. Или добавьте в Railway Dashboard → Variables")
        sys.exit(1)
    
    # Check 2: Green API connection
    if not check_green_api_connection(api_id, api_token):
        print("\n" + "=" * 60)
        print("❌ НЕ УДАЛОСЬ ПОДКЛЮЧИТЬСЯ К GREEN API")
        print("=" * 60)
        print("\n💡 Возможные причины:")
        print("   1. Неверный GREEN_API_ID или GREEN_API_TOKEN")
        print("   2. Инстанс удалён или не активен")
        print("   3. Проблемы с сетью")
        sys.exit(1)
    
    # Check 3: Receive notifications
    print("\n💡 Для проверки получения сообщений:")
    print("   1. Отправьте сообщение на номер бота в WhatsApp")
    print("   2. Ждите 30 секунд...")
    check_receive_notification(api_id, api_token)
    
    # Check 4: Send message
    test_send_message(api_id, api_token)
    
    print("\n" + "=" * 60)
    print("✅ ДИАГНОСТИКА ЗАВЕРШЕНА")
    print("=" * 60)
    print("\n💡 Если все проверки пройдены, но бот не работает:")
    print("   1. Проверьте логи в Railway Dashboard → Logs")
    print("   2. Убедитесь, что бот запущен (статус 'Running')")
    print("   3. Проверьте, что QR-код в Green API отсканирован")


if __name__ == "__main__":
    main()
