#!/usr/bin/env python3
"""
Extended diagnostic script for WhatsApp bot.
Checks all possible issues with Green API setup.
"""
import os
import sys
import requests
import time
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_environment():
    """Check if environment variables are set."""
    print("[CHECK] 1. Проверка переменных окружения...")
    
    green_api_id = os.environ.get("GREEN_API_ID")
    green_api_token = os.environ.get("GREEN_API_TOKEN")
    
    print(f"   GREEN_API_ID: {'SET' if green_api_id else 'NOT SET'}")
    print(f"   GREEN_API_TOKEN: {'SET' if green_api_token else 'NOT SET'}")
    
    if not green_api_id or not green_api_token:
        print("   [ERROR] Отсутствуют учетные данные Green API!")
        print("   Для работы WhatsApp бота необходимо установить:")
        print("   - GREEN_API_ID: ID вашего инстанса")
        print("   - GREEN_API_TOKEN: API токен вашего инстанса")
        return False
    
    print("   [SUCCESS] Переменные окружения установлены")
    return True


def check_credentials_validity(api_id, api_token):
    """Check if credentials are valid."""
    print("\n[CHECK] 2. Проверка валидности учетных данных...")
    
    api_url = "https://api.green-api.com"
    test_url = f"{api_url}/waInstance{api_id}/GetSettings/{api_token}"
    
    try:
        response = requests.get(test_url, timeout=10)
        print(f"   API Request: GET {test_url}")
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   [SUCCESS] Учетные данные действительны")
            try:
                data = response.json()
                print(f"   - Статус аккаунта: {data.get('accountStatus', 'Unknown')}")
                print(f"   - Номер телефона: {data.get('phoneNumber', 'Not set')}")
                print(f"   - Тип аккаунта: {data.get('typeAccount', 'Unknown')}")
                return True
            except:
                print("   [WARNING] Не удалось распарсить ответ, но соединение успешно")
                return True
        elif response.status_code == 400:
            print("   [ERROR] Неверные учетные данные или ID инстанса")
            print("   Проверьте правильность значений GREEN_API_ID и GREEN_API_TOKEN")
            return False
        elif response.status_code == 402:
            print("   [ERROR] Требуется оплата - аккаунт не активирован")
            print("   Проверьте статус подписки в вашем аккаунте Green API")
            return False
        elif response.status_code == 403:
            print("   [ERROR] Доступ запрещен - возможно, IP-адрес не в белом списке")
            print("   Проверьте настройки безопасности в аккаунте Green API")
            return False
        else:
            print(f"   [ERROR] Ошибка API: {response.status_code}")
            print(f"   Ответ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   [ERROR] Таймаут запроса - проверьте подключение к интернету")
        return False
    except requests.exceptions.ConnectionError:
        print("   [ERROR] Ошибка подключения - проверьте подключение к интернету")
        return False
    except Exception as e:
        print(f"   [ERROR] Неожиданная ошибка: {e}")
        return False


def check_account_limits(api_id, api_token):
    """Check account limits and status."""
    print("\n[CHECK] 3. Проверка лимитов аккаунта...")
    
    api_url = "https://api.green-api.com"
    test_url = f"{api_url}/waInstance{api_id}/GetStats/{api_token}"
    
    try:
        response = requests.get(test_url, timeout=10)
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   [INFO] Данные аккаунта получены")
                
                # Проверяем тип аккаунта и лимиты
                if 'tariffDaysLeft' in data:
                    print(f"   - Дней до окончания тарифа: {data.get('tariffDaysLeft', 'Unknown')}")
                
                # Попробуем получить информацию о тарифе
                tariff_url = f"{api_url}/waInstance{api_id}/GetTariff/{api_token}"
                tariff_response = requests.get(tariff_url, timeout=10)
                
                if tariff_response.status_code == 200:
                    tariff_data = tariff_response.json()
                    print(f"   - Тип тарифа: {tariff_data.get('packageName', 'Unknown')}")
                    
                    # Проверяем ограничения
                    if 'limits' in tariff_data:
                        limits = tariff_data['limits']
                        print(f"   - Дневной лимит сообщений: {limits.get('messagesPerDay', 'Unknown')}")
                        
                        # Проверяем, не превышен ли лимит
                        if limits.get('messagesPerDay') == 0:
                            print("   [WARNING] Возможно, лимит сообщений исчерпан")
                            
            except Exception as e:
                print(f"   [INFO] Не удалось получить детальную информацию о лимитах: {e}")
                
        elif response.status_code == 400:
            print("   [INFO] Информация о статистике недоступна (возможно, не поддерживается)")
        else:
            print(f"   [INFO] Статус {response.status_code} (не критично)")
            
        return True
        
    except Exception as e:
        print(f"   [INFO] Не удалось получить информацию о лимитах: {e}")
        return True  # Не критично для работы


def check_qr_session_status(api_id, api_token):
    """Check if WhatsApp session is active."""
    print("\n[CHECK] 4. Проверка статуса сессии WhatsApp...")
    
    api_url = "https://api.green-api.com"
    test_url = f"{api_url}/waInstance{api_id}/GetWaSettings/{api_token}"
    
    try:
        response = requests.get(test_url, timeout=10)
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   - Статус WhatsApp: {data.get('waStatus', 'Unknown')}")
                
                # Если статус не "authorized", значит нужно переподключить
                if data.get('waStatus') != 'authorized':
                    print("   [ERROR] WhatsApp не авторизован!")
                    print("   Необходимо заново отсканировать QR-код в течение 14 дней")
                    print("   Инструкция: WhatsApp → Настройки → Связанные устройства → Подключить устройство")
                    return False
                else:
                    print("   [SUCCESS] WhatsApp авторизован и готов к работе")
                    return True
                    
            except Exception as e:
                print(f"   [INFO] Не удалось получить статус WhatsApp: {e}")
                return True
                
        else:
            print(f"   [INFO] Не удалось получить статус WhatsApp: {response.status_code}")
            return True  # Не критично
            
    except Exception as e:
        print(f"   [INFO] Не удалось проверить статус сессии: {e}")
        return True  # Не критично


def check_whatsapp_adapter():
    """Check if WhatsApp adapter can be imported and initialized."""
    print("\n[CHECK] 5. Проверка адаптера WhatsApp...")
    
    try:
        from adapters.whatsapp_full import FullWhatsAppBot
        print("   [SUCCESS] Адаптер WhatsApp успешно импортирован")
        
        # Попробуем инициализировать бота
        bot = FullWhatsAppBot()
        
        if bot.enabled:
            print("   [SUCCESS] WhatsApp бот инициализирован и готов к работе")
            print(f"   - ID инстанса: {bot.id_instance[:8] if bot.id_instance else 'None'}...")
            return True
        else:
            print("   [ERROR] WhatsApp бот отключен (возможно, из-за отсутствия учетных данных)")
            return False
            
    except ImportError as e:
        print(f"   [ERROR] Не удалось импортировать адаптер WhatsApp: {e}")
        return False
    except Exception as e:
        print(f"   [ERROR] Ошибка при инициализации WhatsApp бота: {e}")
        return False


def check_main_app_config():
    """Check if main app is configured to run WhatsApp bot."""
    print("\n[CHECK] 6. Проверка конфигурации основного приложения...")
    
    # Проверим, как настроен запуск в main.py
    try:
        with open('main.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'WHATSAPP_RUNNER' in content:
            print("   [SUCCESS] WhatsApp бот настроен для запуска в main.py")
        else:
            print("   [ERROR] WhatsApp бот не найден в конфигурации main.py")
            return False
            
        # Проверим, запускается ли в отдельном потоке
        if 'Thread' in content and 'whatsapp' in content.lower():
            print("   [SUCCESS] WhatsApp бот запускается в отдельном потоке")
        else:
            print("   [WARNING] Не найдено явное указание на запуск в потоке")
            
        return True
        
    except Exception as e:
        print(f"   [ERROR] Не удалось проверить конфигурацию main.py: {e}")
        return False


def main():
    """Main diagnostic function."""
    print("[DIAGNOSTIC] Расширенная диагностика WhatsApp бота")
    print("=" * 60)
    print("Проверка всех возможных причин неработоспособности WhatsApp бота:")
    print("=" * 60)
    
    all_checks_passed = True
    
    # 1. Проверка переменных окружения
    env_ok = check_environment()
    all_checks_passed &= env_ok
    
    if env_ok:
        # Получаем учетные данные
        api_id = os.environ.get("GREEN_API_ID")
        api_token = os.environ.get("GREEN_API_TOKEN")
        
        # 2. Проверка валидности учетных данных
        creds_ok = check_credentials_validity(api_id, api_token)
        all_checks_passed &= creds_ok
        
        if creds_ok:
            # 3. Проверка лимитов аккаунта
            limits_ok = check_account_limits(api_id, api_token)
            all_checks_passed &= limits_ok
            
            # 4. Проверка статуса сессии
            session_ok = check_qr_session_status(api_id, api_token)
            all_checks_passed &= session_ok
    
    # 5. Проверка адаптера
    adapter_ok = check_whatsapp_adapter()
    all_checks_passed &= adapter_ok
    
    # 6. Проверка конфигурации основного приложения
    config_ok = check_main_app_config()
    all_checks_passed &= config_ok
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТ:")
    
    if all_checks_passed:
        print("[SUCCESS] Все проверки пройдены! WhatsApp бот должен работать.")
        print("\nДополнительные рекомендации:")
        print("- Убедитесь, что основное приложение запущено: python main.py")
        print("- Проверьте логи приложения на наличие ошибок")
        print("- Убедитесь, что включен режим разработки (ALLOW_LOCAL_RUN=true) если запускаете локально")
    else:
        print("[ERROR] Обнаружены проблемы, которые могут мешать работе WhatsApp бота.")
        print("\nРекомендации по устранению:")
        print("1. Установите правильные значения для GREEN_API_ID и GREEN_API_TOKEN")
        print("2. Проверьте статус вашего аккаунта Green API")
        print("3. Убедитесь, что WhatsApp авторизован (сканировали QR-код)")
        print("4. Проверьте, не исчерпаны ли лимиты на бесплатном тарифе")
        print("5. См. инструкцию в GREEN_API_SETUP.md")
        
    return all_checks_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)