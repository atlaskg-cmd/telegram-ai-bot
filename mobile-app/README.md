# AI Bot Mobile App 📱

**Кроссплатформенное мобильное приложение** (iOS + Android) для AI бота с погодой, валютами, новостями и криптовалютами.

---

## ⚡ Быстрый старт

### Windows (автоматическая установка):
1. **Запустите:** `install-and-run.bat`
2. **Следуйте инструкциям**

### Вручную:
```bash
# 1. Установить Flutter: https://flutter.dev/docs/get-started/install
# 2. Инициализировать проект
flutter create . --platforms=android,ios

# 3. Установить зависимости
flutter pub get

# 4. Запустить
flutter run
```

📖 **Подробная инструкция:** См. [QUICK_START.md](QUICK_START.md)  
📖 **Установка Flutter:** См. [INSTALL_FLUTTER.md](INSTALL_FLUTTER.md)

---

## 🚀 Возможности

### 🤖 AI Чат
- Общение с AI через OpenRouter API
- DeepSeek R1 для сложных запросов
- История сообщений (локальное хранение)
- Голосовой ввод/вывод (в разработке)

### 🌤 Погода
- 5 городов: Бишкек, Москва, Иссык-Куль, Бөкөнбаево, Тон
- Текущая температура, ощущаемая температура
- Влажность, ветер, описание погоды
- Автообновление

### 💱 Конвертер валют
- CNY ↔ KGS (Юань ↔ Сом)
- USD → KGS, RUB
- EUR → KGS
- Актуальные курсы

### 💰 Криптовалюты
- Курсы популярных криптовалют (BTC, ETH, SOL, ...)
- Изменение цены за 24ч 🟢🔴
- Портфель криптовалют
- Отслеживание прибыли/убытков

### 📰 Новости
- 20+ RSS источников
- AI анализ тональности
- Персонализированный дайджест
- Категории: Кыргызстан, Технологии, ИИ, Наука, Мир, Спорт, Экономика, Крипто

### 🎨 Генерация изображений
- AI генерация по описанию
- Multi-provider fallback (HF, Cloudflare, Pollinations)
- Сохранение и share

### 📇 Контакты
- Добавление/удаление контактов
- Поиск
- Быстрый звонок/SMS/WhatsApp

### ⚙️ Настройки
- Тёмная/светлая тема
- Голосовые ответы
- Интересы для новостей
- API ключи
- Очистка данных

---

## 📋 Требования

- **Flutter SDK:** >= 3.0.0
- **Dart SDK:** >= 3.0.0
- **iOS:** >= 12.0
- **Android:** API >= 21

---

## 🛠️ Установка

### 1. Клонирование репозитория

```bash
cd C:\tegi
# mobile-app уже создан
cd mobile-app
```

### 2. Установка зависимостей

```bash
flutter pub get
```

### 3. Настройка API ключей

Создайте файл `.env` или настройте через приложение:

```env
OPENROUTER_API_KEY=your_openrouter_api_key
WEATHER_API_KEY=your_openweathermap_api_key
HF_TOKEN=your_huggingface_token (опционально)
CF_API_TOKEN=your_cloudflare_token (опционально)
CF_ACCOUNT_ID=your_cloudflare_account_id (опционально)
```

### 4. Запуск

```bash
# Запуск на подключенном устройстве/эмуляторе
flutter run

# Запуск на iOS
flutter run -d ios

# Запуск на Android
flutter run -d android

# Сборка релиза
flutter build apk --release      # Android
flutter build ios --release      # iOS
```

---

## 📁 Структура проекта

```
mobile-app/
├── lib/
│   ├── main.dart                 # Точка входа
│   ├── models/                   # Модели данных
│   │   ├── message.dart
│   │   ├── weather.dart
│   │   ├── currency.dart
│   │   ├── crypto.dart
│   │   ├── news.dart
│   │   └── user.dart
│   ├── services/                 # API сервисы
│   │   ├── openrouter_service.dart
│   │   ├── weather_service.dart
│   │   ├── currency_service.dart
│   │   ├── crypto_service.dart
│   │   ├── news_service.dart
│   │   ├── image_generation_service.dart
│   │   └── storage_service.dart
│   ├── providers/                # State management (Provider)
│   │   ├── chat_provider.dart
│   │   ├── weather_provider.dart
│   │   ├── currency_provider.dart
│   │   ├── crypto_provider.dart
│   │   ├── news_provider.dart
│   │   └── settings_provider.dart
│   ├── screens/                  # Экраны
│   │   ├── main_screen.dart
│   │   ├── chat_screen.dart
│   │   ├── weather_screen.dart
│   │   ├── currency_screen.dart
│   │   ├── crypto_screen.dart
│   │   ├── news_screen.dart
│   │   ├── image_screen.dart
│   │   ├── contacts_screen.dart
│   │   └── settings_screen.dart
│   └── widgets/                  # UI компоненты
├── assets/
│   ├── images/
│   └── icons/
├── android/                      # Android проект
├── ios/                          # iOS проект
├── pubspec.yaml                  # Зависимости
└── README.md
```

---

## 🎨 Скриншоты

| AI Чат | Погода | Валюты |
|--------|--------|--------|
| ![Chat](assets/screenshots/chat.png) | ![Weather](assets/screenshots/weather.png) | ![Currency](assets/screenshots/currency.png) |

| Крипто | Новости | Настройки |
|--------|---------|-----------|
| ![Crypto](assets/screenshots/crypto.png) | ![News](assets/screenshots/news.png) | ![Settings](assets/screenshots/settings.png) |

---

## 🔧 Настройка для публикации

### Android

1. **Создание keystore:**
```bash
keytool -genkey -v -keystore ~/upload-keystore.jks -keyalg RSA -keysize 2048 -validity 10000 -alias upload
```

2. **Настройка `android/key.properties`:**
```properties
storePassword=<password>
keyPassword=<password>
keyAlias=upload
storeFile=<path-to-keystore>
```

3. **Сборка:**
```bash
flutter build appbundle --release
```

### iOS

1. **Настройка Signing & Capabilities в Xcode**
2. **Archive:**
```bash
flutter build ipa
```

3. **App Store Connect:**
   - Создать App Record
   - Загрузить build через Transporter
   - Заполнить метаданные

---

## 📦 Зависимости

| Пакет | Назначение |
|-------|------------|
| `provider` | State management |
| `http` / `dio` | HTTP запросы |
| `shared_preferences` | Локальное хранилище |
| `hive_flutter` | Быстрая БД |
| `go_router` | Навигация |
| `fl_chart` | Графики для крипто |
| `intl` | Интернационализация |
| `url_launcher` | Открытие ссылок |
| `image_picker` | Выбор изображений |
| `share_plus` | Share изображений |
| `firebase_core` / `firebase_messaging` | Push уведомления |

---

## 🔐 Безопасность

- API ключи хранятся в защищенном хранилище (`flutter_secure_storage`)
- Все данные локальны (не отправляются на сервер)
- SSL/TLS для всех API запросов

---

## 📝 Changelog

### Version 1.0.0 (2026-02-21) - Исправление проблем
- ✅ Созданы недостающие файлы проекта (.gitignore, widgets.dart)
- ✅ Созданы assets директории (images/, icons/)
- ✅ Упрощен pubspec.yaml (убраны шрифты для избежания ошибок)
- ✅ Созданы placeholder файлы для иконок
- ✅ Создан скрипт install-and-run.bat для автоматической установки
- ✅ Созданы инструкции: QUICK_START.md, INSTALL_FLUTTER.md, FIREBASE_SETUP.md
- ⚠️ Требуется установка Flutter SDK пользователем

### Version 1.0.0 (2026-02-20) - Начальная версия
- ✅ AI чат с OpenRouter
- ✅ Погода (5 городов)
- ✅ Конвертер валют (CNY↔KGS, USD, EUR)
- ✅ Криптовалюты + портфель
- ✅ Новости + AI дайджест
- ✅ Генерация изображений
- ✅ Контакты
- ✅ Настройки (тема, голос, интересы)
- ✅ Локальное хранилище

---

## 🤝 Вклад

1. Fork репозиторий
2. Создай feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменений (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Открой Pull Request

---

## 📄 Лицензия

MIT License

---

## 📞 Контакты

- **Telegram:** @yourusername
- **GitHub:** your-username
- **Email:** your.email@example.com

---

## 🙏 Благодарности

- [OpenRouter](https://openrouter.ai/) - AI API
- [Open-Meteo](https://open-meteo.com/) - Weather API
- [CoinGecko](https://www.coingecko.com/) - Crypto API
- [Exchangerate API](https://exchangerate-api.com/) - Currency API
- [Pollinations.ai](https://pollinations.ai/) - Image Generation

---

**Сделано с ❤️ для Кыргызстана** 🇰🇬
