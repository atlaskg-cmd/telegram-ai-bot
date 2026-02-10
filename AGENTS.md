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
- **Переменные окружения**: 
  - `TELEGRAM_API_TOKEN` - токен бота от BotFather
  - `OPENROUTER_API_KEY` - API ключ OpenRouter
  - `WEATHER_API_KEY` - ключ OpenWeatherMap
  - `ADMIN_ID` - твой Telegram ID для админ-панели
  - `CF_API_TOKEN` - Cloudflare API Token (для генерации изображений)
  - `CF_ACCOUNT_ID` - Cloudflare Account ID (для генерации изображений)
  - `DATABASE_URL` - автоматически создаётся при добавлении PostgreSQL

### 4. Database (PostgreSQL) - ВАЖНО!
Бот поддерживает две базы данных:
- **SQLite** (`bot.db`) - локально, НЕ сохраняется при деплое!
- **PostgreSQL** - на Railway, данные сохраняются навсегда

#### Настройка PostgreSQL на Railway:
1. В Railway Dashboard нажми **"New"** → **"Database"** → **"Add PostgreSQL"**
2. Railway автоматически создаст переменную `DATABASE_URL`
3. Бот автоматически подключится к PostgreSQL (при наличии `DATABASE_URL`)
4. **ВСЕ ДАННЫЕ (контакты, настройки, история) будут сохраняться после деплоя!**

> ⚠️ Без PostgreSQL: контакты и настройки сбрасываются после каждого push!

### 5. Проверка ошибок
```bash
# Логи Railway (через CLI)
railway logs -f

# Или в браузере:
# https://railway.app/dashboard → проект → вкладка Logs
```

## Структура проекта
- `bot.py` — основной код бота
- `database.py` — база данных (SQLite/PostgreSQL)
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
- Для сохранения данных настрой PostgreSQL (см. пункт 4)
