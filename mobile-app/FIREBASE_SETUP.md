# 🔥 Настройка Firebase

## Для чего нужен Firebase?
- Push уведомления (Firebase Messaging)
- Аналитика
- Crashlytics

---

## 📱 Android настройка

### Шаг 1: Создайте проект Firebase
1. Перейдите на https://console.firebase.google.com/
2. Нажмите "Add project" или выберите существующий
3. Следуйте инструкциям

### Шаг 2: Добавьте Android приложение
1. Нажмите "Add app" → Android
2. Введите package name: `com.example.ai_bot_app`
3. Скачайте `google-services.json`

### Шаг 3: Разместите файл
Поместите `google-services.json` в:
```
mobile-app/android/app/google-services.json
```

### Шаг 4: Добавьте зависимости

**android/build.gradle:**
```gradle
buildscript {
    dependencies {
        classpath 'com.google.gms:google-services:4.4.0'
    }
}
```

**android/app/build.gradle:**
```gradle
apply plugin: 'com.google.gms.google-services'

dependencies {
    implementation platform('com.google.firebase:firebase-bom:32.7.0')
    implementation 'com.google.firebase:firebase-messaging'
}
```

---

## 🍎 iOS настройка

### Шаг 1: Добавьте iOS приложение
1. В Firebase Console нажмите "Add app" → iOS
2. Bundle ID: `com.example.aiBotApp`
3. Скачайте `GoogleService-Info.plist`

### Шаг 2: Разместите файл
В Xcode:
1. Откройте `ios/Runner.xcworkspace`
2. Перетащите `GoogleService-Info.plist` в Runner (в папку Runner)
3. Убедитесь что файл добавлен в Target

---

## ✅ Проверка

После настройки выполните:
```bash
flutter run
```

Push уведомления должны работать.

---

## 📝 Примечание

Для тестирования приложения Firebase **не обязателен**.
Приложение будет работать без push уведомлений.
