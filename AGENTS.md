# AI Bot Project Context

## О проекте
Телеграм бот с ИИ (OpenRouter), погодой, новостями, TTS.

## Архитектура деплоя
```
VS Code → GitHub → Railway (auto-deploy)
```

## Важные правила

### 1. Бот остановлен локально
В `bot.py` есть защита:
```python
if os.environ.get('RAILWAY_ENVIRONMENT'):
    asyncio.run(main())  # только на Railway
else:
    print("[STOP] Bot stopped locally...")  # локально не запускается
```
**НЕ удалять эту проверку!**

### 2. Workflow изменений
```bash
# После любых изменений в коде:
git add .
git commit -m "описание изменений"
git push origin main
# Railway автоматически деплоит
```

### 3. Railway настройки
- **Auto Deploy**: ВКЛЮЧЕН (деплой после каждого push)
- **Start Command**: `python bot.py`
- **Переменные окружения**: TELEGRAM_API_TOKEN, OPENROUTER_API_KEY, WEATHER_API_KEY

### 4. Проверка ошибок
```bash
# Логи Railway (через CLI)
railway logs -f

# Или в браузере:
# https://railway.app/dashboard → проект → вкладка Logs
```

## Структура проекта
- `bot.py` — основной код бота
- `config.json` — локальная конфигурация
- `requirements.txt` — зависимости
- `railway.json` — настройки Railway
- `Procfile` — команда запуска

## Git
- Репозиторий: `https://github.com/atlaskg-cmd/telegram-ai-bot.git`
- Ветка: `main`

## Примечания
- Бот работает ТОЛЬКО на Railway
- Локальный запуск запрещён (чтобы не было конфликта токенов)
- После изменений обязательно `git push origin main`
