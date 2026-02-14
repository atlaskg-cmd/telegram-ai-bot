# Настройка Webhook для Green API

## Получение URL для Webhook

После деплоя на Railway ваш webhook URL будет выглядеть так:
```
https://<ваше-имя-проекта>.up.railway.app/webhook-whatsapp
```

## Настройка в консоли Green API

1. Перейдите в [консоль Green API](https://console.green-api.com/)
2. Выберите ваш инстанс
3. Нажмите "Настройки" или "Settings"
4. Найдите раздел "Webhook" или "Настройка вебхуков"
5. Введите URL webhook:
   ```
   https://<ваше-имя-проекта>.up.railway.app/webhook-whatsapp
   ```
6. Убедитесь, что включены следующие типы уведомлений:
   - incomingMessageReceived (получение входящих сообщений)
   - outgoingMessageStatus (статус отправки сообщений)
   - stateInstanceChanged (изменение статуса инстанса)

## Проверка настройки

После настройки webhook, все входящие сообщения с WhatsApp будут автоматически обрабатываться ботом.

## Переменные окружения

Убедитесь, что в Railway установлены следующие переменные:
- `GREEN_API_ID` - ID вашего инстанса Green API
- `GREEN_API_TOKEN` - токен вашего инстанса Green API
- `TELEGRAM_API_TOKEN` - токен вашего Telegram бота
- `ADMIN_ID` - ваш ID в Telegram (опционально)

## Перезапуск приложения

После изменения настроек webhook, рекомендуется перезапустить приложение на Railway.